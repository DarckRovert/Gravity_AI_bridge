"""
╔══════════════════════════════════════════════════════╗
║     GRAVITY AI ENGINE WATCHDOG V4.3                  ║
║     Motor de Auto-Detección y Auto-Switch de IA      ║
╚══════════════════════════════════════════════════════╝

Este módulo corre en segundo plano como un hilo demonio.
Su única función: detectar qué motor de IA está disponible
y actualizar el proveedor activo de forma completamente
transparente para el usuario.

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
_lock = threading.Lock()
_on_switch_callbacks = []  # Lista de callbacks a ejecutar cuando haya un cambio


def get_active_state():
    """Devuelve el estado actual del motor de IA de forma segura."""
    with _lock:
        return {
            "provider": _current_provider_name,
            "model": _current_model,
            "url": _current_url,
            "protocol": _current_protocol
        }


def on_provider_switch(callback):
    """Registra un callback que se ejecutará cuando el proveedor cambie."""
    _on_switch_callbacks.append(callback)


def _persist_settings(provider_result, model_name):
    """Actualiza _settings.json de forma segura sin borrar las preferencias del usuario."""
    try:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        
        # Solo actualizamos los campos de proveedor, respetando preferencias de usuario
        data["provider"] = provider_result.protocol
        data["api_url"] = provider_result.url
        data["last_model"] = model_name
        
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass  # Silencioso: no interrumpimos el flujo por un fallo en disco


def _watchdog_loop(interval_seconds=30, verbose=False):
    """Bucle principal del watchdog. Corre en un hilo separado."""
    global _current_provider_name, _current_model, _current_url, _current_protocol

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
                        
                        # Persistir en disco de forma segura
                        _persist_settings(best_prov, best_mod)
                        
                        if verbose and old_name is not None:
                            print(f"\n[⚡ WATCHDOG] Switch detectado: {old_name}/{old_model} → {best_prov.name}/{best_mod}")
                        
                        # Ejecutar callbacks registrados (ej: actualizar el cliente en AuditorCLI)
                        for cb in _on_switch_callbacks:
                            try:
                                cb(best_prov, best_mod)
                            except Exception:
                                pass

        except Exception:
            pass  # Tolerante a fallos de red

        time.sleep(interval_seconds)


def start(interval_seconds=30, verbose=False):
    """
    Inicia el watchdog en un hilo demonio de baja prioridad.
    
    Args:
        interval_seconds: Con qué frecuencia re-escanear los proveedores.
        verbose: Si True, imprime mensajes de consola cuando hay un switch.
    
    Returns:
        El hilo demonio ya iniciado.
    """
    # Realizar un escaneo inicial SINCRÓNICO para tener datos antes de arrancar
    try:
        scans = ProviderScanner.scan_all()
        best_prov, best_mod = ProviderScanner.auto_select_best(scans)
        if best_prov and best_mod:
            global _current_provider_name, _current_model, _current_url, _current_protocol
            _current_provider_name = best_prov.name
            _current_model = best_mod
            _current_url = best_prov.url
            _current_protocol = best_prov.protocol
            _persist_settings(best_prov, best_mod)
    except Exception:
        pass

    t = threading.Thread(
        target=_watchdog_loop,
        args=(interval_seconds, verbose),
        name="GravityEngineWatchdog",
        daemon=True  # Se mata automáticamente cuando el proceso principal termina
    )
    t.start()
    return t


if __name__ == "__main__":
    # Modo diagnóstico: muestra el estado del watchdog en tiempo real
    print("Iniciando Gravity Engine Watchdog en modo diagnóstico...")
    start(interval_seconds=10, verbose=True)
    while True:
        state = get_active_state()
        print(f"[Watchdog Status] Proveedor: {state['provider']} | Modelo: {state['model']} | URL: {state['url']}")
        time.sleep(15)
