"""
╔══════════════════════════════════════════════════════╗
║     GRAVITY AI ENGINE WATCHDOG V5.0                  ║
║     Auto-Detección, Auto-Switch y Auto-Optimización  ║
╚══════════════════════════════════════════════════════╝

Este módulo corre en segundo plano como un hilo demonio.
Su función: detectar qué motor de IA está disponible,
actualizar el proveedor activo, y aplicar las variables de
entorno y parámetros API óptimos para ese motor específico.

Prioridad de selección:
  1. El proveedor con un modelo actualmente cargado en RAM/GPU
  2. El proveedor con el modelo de mayor peso (parámetros)
  3. El proveedor con menor latencia de red como desempate
"""

import threading
import time
import json
import os
from provider_scanner import ProviderScanner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")

# Estado global del motor activo (compartido entre hilos)
_current_provider_name = None
_current_model = None
_current_url = None
_current_protocol = None
_current_api_opts = {}      # Parámetros API óptimos para el motor activo
_hardware_profile = None    # Cache del perfil de hardware
_lock = threading.Lock()
_on_switch_callbacks = []   # Callbacks a ejecutar cuando haya un cambio de motor


def get_active_state():
    """Devuelve el estado actual del motor de IA de forma segura."""
    with _lock:
        return {
            "provider": _current_provider_name,
            "model": _current_model,
            "url": _current_url,
            "protocol": _current_protocol,
            "api_opts": _current_api_opts.copy(),
            "hardware": _hardware_profile.copy() if _hardware_profile else {},
        }


def get_optimized_options(base_opts=None):
    """
    Returns the Ollama/OpenAI options dict enriched with hardware-optimal params.
    Use this in AuditorCLI.handle_input() instead of raw settings.options.
    """
    with _lock:
        merged = _current_api_opts.copy()
    if base_opts:
        for k, v in base_opts.items():
            merged[k] = v  # User settings override hardware defaults
    return merged


def on_provider_switch(callback):
    """Registers a callback to execute when the active provider changes."""
    _on_switch_callbacks.append(callback)


def _persist_settings(provider_result, model_name, api_opts):
    """Updates _settings.json safely without overwriting user preferences."""
    try:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data["provider"] = provider_result.protocol
        data["api_url"] = provider_result.url
        data["last_model"] = model_name

        # Persist the hardware-optimized num_ctx if it's better than what's stored
        adv = data.get("advanced_params", {})
        current_ctx = adv.get("num_ctx", 0)
        new_ctx = api_opts.get("num_ctx", 0)
        if new_ctx > current_ctx:
            adv["num_ctx"] = new_ctx
            data["advanced_params"] = adv

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _apply_engine_optimization(provider_name, protocol):
    """
    Applies env vars and builds API options for the newly detected engine.
    Called on every engine switch.
    """
    try:
        from env_optimizer import apply_all, build_api_options
        profile, _ = apply_all(persist=False, verbose=False)

        # Build engine-specific API options
        engine_key = protocol  # "ollama", "openai", etc.
        if "lemonade" in provider_name.lower():
            engine_key = "lemonade"
        elif "studio" in provider_name.lower():
            engine_key = "lm_studio"
        elif "kobold" in provider_name.lower():
            engine_key = "kobold"
        elif "jan" in provider_name.lower():
            engine_key = "jan"

        # Load user's base options from settings
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            user_opts = data.get("advanced_params", {})
        except Exception:
            user_opts = {}

        api_opts = build_api_options(engine_key, profile, user_opts)
        return profile, api_opts

    except Exception:
        return {}, {}


def _watchdog_loop(interval_seconds=30, verbose=False):
    """Main watchdog loop. Runs in a separate daemon thread."""
    global _current_provider_name, _current_model, _current_url, _current_protocol
    global _current_api_opts, _hardware_profile

    while True:
        try:
            scans = ProviderScanner.scan_all()
            best_prov, best_mod = ProviderScanner.auto_select_best(scans)

            if best_prov and best_mod:
                with _lock:
                    did_switch = (
                        _current_provider_name != best_prov.name or
                        _current_model != best_mod
                    )

                    if did_switch:
                        old_name = _current_provider_name
                        old_model = _current_model

                        _current_provider_name = best_prov.name
                        _current_model = best_mod
                        _current_url = best_prov.url
                        _current_protocol = best_prov.protocol

                        # Apply optimizations for the new engine
                        profile, api_opts = _apply_engine_optimization(
                            best_prov.name, best_prov.protocol
                        )
                        _hardware_profile = profile
                        _current_api_opts = api_opts

                        _persist_settings(best_prov, best_mod, api_opts)

                        if verbose and old_name is not None:
                            print(f"\n[⚡ WATCHDOG] Switch: {old_name}/{old_model}"
                                  f" → {best_prov.name}/{best_mod}"
                                  f" | ctx={api_opts.get('num_ctx', '?')}")

                        for cb in _on_switch_callbacks:
                            try:
                                cb(best_prov, best_mod)
                            except Exception:
                                pass

        except Exception:
            pass  # Network tolerant

        time.sleep(interval_seconds)


def start(interval_seconds=30, verbose=False):
    """
    Starts the watchdog in a low-priority daemon thread.
    Performs an initial SYNCHRONOUS scan+optimize before launching the daemon,
    so the calling code gets an already-configured environment.

    Args:
        interval_seconds: How often to re-scan providers.
        verbose: Print console messages on engine switch.

    Returns:
        The started daemon thread.
    """
    global _current_provider_name, _current_model, _current_url, _current_protocol
    global _current_api_opts, _hardware_profile

    # ── Initial synchronous scan + optimization ──────────────────────────────
    try:
        # Apply env vars first (before scanning, so Ollama inherits them)
        from env_optimizer import apply_all, build_api_options
        profile, _ = apply_all(persist=False, verbose=verbose)
        _hardware_profile = profile
    except Exception:
        profile = {}

    try:
        scans = ProviderScanner.scan_all()
        best_prov, best_mod = ProviderScanner.auto_select_best(scans)
        if best_prov and best_mod:
            _current_provider_name = best_prov.name
            _current_model = best_mod
            _current_url = best_prov.url
            _current_protocol = best_prov.protocol

            # Build API options for the detected engine
            try:
                from env_optimizer import build_api_options
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
                print(f"[⚡ WATCHDOG] Iniciado → {best_prov.name} / {best_mod}"
                      f" | ctx={_current_api_opts.get('num_ctx', '?')}")
    except Exception:
        pass

    # ── Start background daemon ───────────────────────────────────────────────
    t = threading.Thread(
        target=_watchdog_loop,
        args=(interval_seconds, verbose),
        name="GravityEngineWatchdog",
        daemon=True
    )
    t.start()
    return t


if __name__ == "__main__":
    print("Iniciando Gravity Engine Watchdog V5.0 en modo diagnóstico...")
    start(interval_seconds=15, verbose=True)
    while True:
        state = get_active_state()
        hw = state.get("hardware", {})
        print(f"\n[Status] Motor: {state['provider']} | Modelo: {state['model']}"
              f" | ctx={state['api_opts'].get('num_ctx', '?')}"
              f" | VRAM={hw.get('vram_mb', '?')}MB")
        time.sleep(20)
