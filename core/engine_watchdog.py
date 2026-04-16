"""
╔══════════════════════════════════════════════════════════╗
║     GRAVITY AI ENGINE WATCHDOG V9.3                      ║
║     Auto-Detección, Auto-Switch y Auto-Optimización      ║
╚══════════════════════════════════════════════════════════╝

Corre en segundo plano como hilo demonio.
Delega toda la lógica de detección y routing al V9.3 ProviderManager.
Persiste la selección en _settings.json.
"""

import threading
import time
import json
import os
from core import provider_manager

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE  = os.path.join(BASE_DIR, "_settings.json")

# ── Global state ──────────────────────────────────────────────────────────────
_current_provider_name = None
_current_model         = None
_current_url           = None
_current_protocol      = None
_current_api_opts      = {}
_hardware_profile      = None
_lock                  = threading.Lock()
_on_switch_callbacks   = []
_started               = False


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
    _on_switch_callbacks.append(callback)


def _persist_settings(provider_result, model_name, api_opts):
    try:
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
            from env_optimizer import apply_all, build_api_options
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
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                user_opts = json.load(f).get("advanced_params", {})
        except Exception:
            user_opts = {}

        api_opts = build_api_options(engine_key, profile, user_opts)
        return profile, api_opts
    except Exception:
        return {}, {}


def _watchdog_loop(interval_seconds=30, verbose=False):
    global _current_provider_name, _current_model, _current_url, _current_protocol
    global _current_api_opts, _hardware_profile

    while True:
        try:
            best_prov, best_mod = provider_manager.get_best()

            # Evita sobreescribir si estamos bloqueados manualmente vía bridge_server o ask_deepseek
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                if settings.get("model_locked", False):
                    # Si está bloqueado, respetarlo y no hacer auto-switch
                    time.sleep(interval_seconds)
                    continue
            except Exception:
                pass

            if best_prov and best_mod:
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

                        if verbose and old_name is not None:
                            print(
                                f"\n[WATCHDOG] Switch: {old_name}/{old_model}"
                                f" → {best_prov.name}/{best_mod}"
                                f" | ctx={api_opts.get('num_ctx', '?')}"
                            )

                        for cb in _on_switch_callbacks:
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
            from env_optimizer import apply_all
            profile, _ = apply_all(persist=False, verbose=verbose)
            _hardware_profile = profile
        except ImportError:
            profile = {}
    except Exception:
        profile = {}

    try:
        best_prov, best_mod = provider_manager.get_best()
        if best_prov and best_mod:
            _current_provider_name = best_prov.name
            _current_model         = best_mod
            _current_url           = best_prov.url
            _current_protocol      = best_prov.protocol

            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    user_opts = json.load(f).get("advanced_params", {})
            except Exception:
                user_opts = {}

            engine_key = best_prov.protocol
            if "lemonade" in best_prov.name.lower():
                engine_key = "lemonade"

            try:
                from env_optimizer import build_api_options
                _current_api_opts = build_api_options(engine_key, profile or {}, user_opts)
            except Exception:
                _current_api_opts = user_opts

            _persist_settings(best_prov, best_mod, _current_api_opts)
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
