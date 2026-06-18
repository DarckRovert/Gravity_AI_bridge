"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI ENGINE WATCHDOG V16.0 PRO                 ║
║     Auto-Detección, Auto-Switch, Auto-Optimización       ║
║     + Daemon Health Monitor con Auto-Restart             ║
╚══════════════════════════════════════════════════════════╝

Corre en segundo plano como hilo demonio.
- Gestiona el routing automático de proveedores LLM.
- Monitorea los daemons críticos de Gravity y los relanza si mueren.
- Expone get_health() para el dashboard de autonomía.
"""

import threading
import time
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from core import provider_manager
from core.logger import log

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE  = os.path.join(BASE_DIR, "_settings.json")

# ── Global state — Provider routing ───────────────────────────────────────────
_current_provider_name = None
_current_model         = None
_current_url           = None
_current_protocol      = None
_current_api_opts      = {}
_hardware_profile      = None
_lock                  = threading.RLock()
_settings_lock         = threading.RLock()
_on_switch_callbacks   = []
_started               = False

# ── Daemon Health Monitor ─────────────────────────────────────────────────────
# Registro de daemons críticos: {nombre: {thread, restart_fn, restart_count, last_restart}}
_daemon_registry: Dict[str, Dict[str, Any]] = {}
_daemon_lock = threading.RLock()
DAEMON_CHECK_INTERVAL = 30   # segundos entre checks
MAX_RESTARTS_PER_HOUR = 6    # máximo de reinicios por daemon por hora


def register_daemon(
    name: str,
    thread: threading.Thread,
    restart_fn: Optional[Callable] = None,
) -> None:
    """
    Registra un daemon crítico para monitoreo.

    Args:
        name:       Nombre identificador (ej. 'autonomy_engine')
        thread:     El objeto threading.Thread que corre el daemon
        restart_fn: Función sin argumentos que relanza el daemon.
                    Si es None, el daemon se registra solo para monitoreo.
    """
    with _daemon_lock:
        _daemon_registry[name] = {
            "thread":         thread,
            "restart_fn":     restart_fn,
            "restart_count":  0,
            "restart_times":  [],
            "last_restart":   None,
            "status":         "running",
        }
    log.debug(f"[Watchdog] Daemon registrado para monitoreo: {name}")


def _is_daemon_alive(name: str) -> bool:
    """Retorna True si el thread del daemon sigue vivo."""
    with _daemon_lock:
        entry = _daemon_registry.get(name)
    if not entry:
        return True  # No registrado = no monitoreado = no intervenir
    t = entry.get("thread")
    return t is not None and t.is_alive()


def _relaunch_daemon(name: str) -> bool:
    """
    Intenta relanzar un daemon muerto.
    Respeta el límite MAX_RESTARTS_PER_HOUR.
    Retorna True si se pudo relanzar.
    """
    with _daemon_lock:
        entry = _daemon_registry.get(name)
        if not entry or not entry.get("restart_fn"):
            log.warning(f"[Watchdog] Daemon '{name}' no tiene restart_fn. No se puede relanzar.")
            entry["status"] = "dead_no_restart"
            return False

        # Limpiar reinicios de hace más de 1 hora
        now = time.time()
        entry["restart_times"] = [t for t in entry["restart_times"] if now - t < 3600]

        if len(entry["restart_times"]) >= MAX_RESTARTS_PER_HOUR:
            log.error(
                f"[Watchdog] Daemon '{name}' superó {MAX_RESTARTS_PER_HOUR} reinicios/hora. "
                "Marcado como FAILED. Requiere intervención manual."
            )
            entry["status"] = "failed_max_restarts"
            return False

        restart_fn = entry["restart_fn"]

    try:
        new_thread = restart_fn()
        with _daemon_lock:
            entry = _daemon_registry[name]
            entry["thread"]       = new_thread
            entry["restart_times"].append(time.time())
            entry["restart_count"] += 1
            entry["last_restart"]  = datetime.now(timezone.utc).isoformat()
            entry["status"]        = "restarted"
        log.info(f"[Watchdog] Daemon '{name}' relanzado (reinicio #{entry['restart_count']})")
        return True
    except Exception as e:
        log.error(f"[Watchdog] Error relanzando daemon '{name}': {e}")
        with _daemon_lock:
            _daemon_registry[name]["status"] = "restart_failed"
        return False


def _monitor_daemons() -> None:
    """Verifica si los daemons críticos siguen vivos y los relanza si no."""
    with _daemon_lock:
        names = list(_daemon_registry.keys())

    for name in names:
        if not _is_daemon_alive(name):
            log.warning(f"[Watchdog] Daemon muerto detectado: '{name}'. Intentando relanzar...")
            _relaunch_daemon(name)


def get_health() -> Dict[str, Any]:
    """
    Retorna el estado de salud del sistema para el dashboard.
    Incluye estado de cada daemon registrado.
    """
    with _daemon_lock:
        daemons_health = {}
        for name, entry in _daemon_registry.items():
            t = entry.get("thread")
            daemons_health[name] = {
                "alive":          t is not None and t.is_alive(),
                "status":         entry.get("status", "unknown"),
                "restart_count":  entry.get("restart_count", 0),
                "last_restart":   entry.get("last_restart"),
                "can_restart":    entry.get("restart_fn") is not None,
            }

    with _lock:
        provider_info = {
            "name":  _current_provider_name,
            "model": _current_model,
        }

    return {
        "ts":       datetime.now(timezone.utc).isoformat(),
        "provider": provider_info,
        "daemons":  daemons_health,
    }


def get_active_state():
    with _lock:
        return {
            "provider":  _current_provider_name,
            "model":     _current_model,
            "url":       _current_url,
            "protocol":  _current_protocol,
            "api_opts":  _current_api_opts.copy(),
            "hardware":  _hardware_profile.copy() if _hardware_profile else {},
        }


def get_optimized_options(base_opts=None):
    with _lock:
        merged = _current_api_opts.copy()
    if base_opts:
        for k, v in base_opts.items():
            merged[k] = v
    return merged


def on_provider_switch(callback):
    with _lock:
        _on_switch_callbacks.append(callback)


def _persist_settings(provider_result, model_name, api_opts):
    try:
        with _settings_lock:
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

            # Mantiene compatibilidad V6
            data["provider"]          = provider_result.name
            data["provider_protocol"] = provider_result.protocol
            data["api_url"]           = provider_result.url
            data["last_model"]        = model_name

            adv         = data.get("advanced_params", {})
            current_ctx = adv.get("num_ctx", 0)
            new_ctx     = api_opts.get("num_ctx", 0)
            if new_ctx > current_ctx:
                adv["num_ctx"]          = new_ctx
                data["advanced_params"] = adv

            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _apply_engine_optimization(provider_name, protocol):
    try:
        try:
            from core.env_optimizer import apply_all, build_api_options
        except ImportError:
            return {}, {}
        profile, _ = apply_all(persist=False, verbose=False)

        engine_key = protocol
        pn_lower   = provider_name.lower()
        if "lemonade"  in pn_lower: engine_key = "lemonade"
        elif "studio"  in pn_lower: engine_key = "lm_studio"
        elif "kobold"  in pn_lower: engine_key = "kobold"
        elif "jan"     in pn_lower: engine_key = "jan"

        try:
            with _settings_lock:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    user_opts = json.load(f).get("advanced_params", {})
        except Exception:
            user_opts = {}

        api_opts = build_api_options(engine_key, profile, user_opts)

        # Aplicar optimización KV-cache de Ollama via turbo_kv
        if engine_key == "ollama":
            try:
                from core.turbo_kv import get_ollama_kv_options
                vram_mb = profile.get("vram_mb", 8192)
                kv_opts = get_ollama_kv_options(vram_mb)
                # Aplicar env vars de KV-cache al proceso actual
                import os as _os
                _os.environ["OLLAMA_KV_CACHE_TYPE"]  = kv_opts.get("OLLAMA_KV_CACHE_TYPE", "q4_0")
                _os.environ["OLLAMA_FLASH_ATTENTION"] = kv_opts.get("OLLAMA_FLASH_ATTENTION", "1")
            except Exception:
                pass

        return profile, api_opts
    except Exception:
        return {}, {}



def _watchdog_loop(interval_seconds=30, verbose=False):
    global _current_provider_name, _current_model, _current_url, _current_protocol
    global _current_api_opts, _hardware_profile

    while True:
        # ── 1. Monitor de daemons críticos ────────────────────────────────
        try:
            _monitor_daemons()
        except Exception as _mon_e:
            log.debug(f"[Watchdog] Error en monitor de daemons: {_mon_e}")

        # ── 2. Auto-switch de proveedor LLM ───────────────────────────────
        try:
            best_prov, best_mod = provider_manager.get_best()

            # Evita sobreescribir si estamos bloqueados manualmente vía bridge_server o ask_deepseek
            try:
                with _settings_lock:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                if settings.get("model_locked", False):
                    # Si está bloqueado, respetarlo y no hacer auto-switch
                    time.sleep(interval_seconds)
                    continue
            except Exception:
                pass

            if best_prov and best_mod:
                did_switch = False
                old_name = None
                old_model = None
                callbacks_to_run = []

                with _lock:
                    did_switch = (
                        _current_provider_name != best_prov.name or
                        _current_model         != best_mod
                    )

                    if did_switch:
                        old_name  = _current_provider_name
                        old_model = _current_model

                        _current_provider_name = best_prov.name
                        _current_model         = best_mod
                        _current_url           = best_prov.url
                        _current_protocol      = best_prov.protocol

                        profile, api_opts = _apply_engine_optimization(
                            best_prov.name, best_prov.protocol
                        )
                        _hardware_profile  = profile
                        _current_api_opts  = api_opts

                        _persist_settings(best_prov, best_mod, api_opts)

                        # Capturamos una copia segura de los callbacks bajo lock
                        callbacks_to_run = list(_on_switch_callbacks)

                if did_switch:
                    if verbose and old_name is not None:
                        print(
                            f"\n[WATCHDOG] Switch: {old_name}/{old_model}"
                            f" → {best_prov.name}/{best_mod}"
                            f" | ctx={api_opts.get('num_ctx', '?')}"
                        )

                    # Los callbacks se ejecutan fuera del lock para evitar deadlocks
                    for cb in callbacks_to_run:
                        try:
                            cb(best_prov, best_mod)
                        except Exception:
                            pass

        except Exception:
            pass  # Network-tolerant

        time.sleep(interval_seconds)


def start(interval_seconds=30, verbose=False):
    global _current_provider_name, _current_model, _current_url, _current_protocol
    global _current_api_opts, _hardware_profile, _started

    if _started:
        return None
    _started = True

    try:
        try:
            from core.env_optimizer import apply_all
            profile, _ = apply_all(persist=False, verbose=verbose)
            with _lock:
                _hardware_profile = profile
        except ImportError:
            profile = {}
    except Exception:
        profile = {}

    try:
        best_prov, best_mod = provider_manager.get_best()
        if best_prov and best_mod:
            with _lock:
                _current_provider_name = best_prov.name
                _current_model         = best_mod
                _current_url           = best_prov.url
                _current_protocol      = best_prov.protocol

            try:
                with _settings_lock:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        user_opts = json.load(f).get("advanced_params", {})
            except Exception:
                user_opts = {}

            engine_key = best_prov.protocol
            if "lemonade" in best_prov.name.lower():
                engine_key = "lemonade"

            try:
                from core.env_optimizer import build_api_options
                opts = build_api_options(engine_key, profile or {}, user_opts)
            except Exception:
                opts = user_opts

            with _lock:
                _current_api_opts = opts

            _persist_settings(best_prov, best_mod, opts)
            if verbose:
                print(f"[⚡ WATCHDOG] Iniciado → {best_prov.name} / {best_mod}")
    except Exception:
        pass

    t = threading.Thread(
        target=_watchdog_loop,
        args=(interval_seconds, verbose),
        name="GravityEngineWatchdog",
        daemon=True,
    )
    t.start()
    return t
