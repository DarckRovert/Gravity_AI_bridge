"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI PROVIDER SCANNER V16.0 PRO [Diamond Edition]  ║
║     Delegates to ProviderManager + ProviderRegistry         ║
╚══════════════════════════════════════════════════════════════╝

This file is a BACKWARDS-COMPATIBLE wrapper around the new
ProviderRegistry/ProviderManager system introduced in V16.0 PRO.
All existing callers (health_check.py, engine_watchdog.py, etc.)
continue to work without modification, under full reentrant thread safety.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAST_SCAN_FILE: str = os.path.join(BASE_DIR, "_last_scan.json")

# Cerrojo reentrante global para prevenir corrupciones en lecturas/escrituras concurrentes
_scan_lock: threading.RLock = threading.RLock()

# Re-export ProviderResult from the canonical location for backwards compat
from providers.base import ProviderResult  # noqa: F401

# ── Public API (unchanged from V6) ────────────────────────────────────────────


def scan_all_providers(force: bool = False) -> List[Any]:
    """
    Scans all local AND cloud providers using the V7 ProviderRegistry.
    Returns list of ProviderResult objects (backwards-compatible).
    """
    from core.provider_manager import scan_all

    results = scan_all(force=force)
    _save_last_scan(results)
    return results


def auto_select_best(
    task: str = "any", prefer_local: bool = True
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Auto-selects the best provider and model for the given task.
    Returns (ProviderResult | None, model_name | None).
    """
    from core.provider_manager import get_best

    return get_best(task)


def get_provider_by_name(name: str) -> Optional[Any]:
    """Returns ProviderResult for a specific provider name, or None."""
    results = scan_all_providers()
    name_l: str = name.lower()
    return next((r for r in results if r.name.lower() == name_l), None)


def get_available_models(provider_name: str) -> List[str]:
    """Returns list of model names for a given provider."""
    r = get_provider_by_name(provider_name)
    return [m["name"] for m in r.models] if r and r.is_healthy else []


def get_all_local_providers() -> List[Any]:
    return [
        r for r in scan_all_providers() if getattr(r, "category", "local") == "local"
    ]


def get_all_cloud_providers() -> List[Any]:
    return [
        r for r in scan_all_providers() if getattr(r, "category", "local") == "cloud"
    ]


def get_provider_count() -> Dict[str, int]:
    results = scan_all_providers()
    local: int = sum(
        1
        for r in results
        if getattr(r, "category", "local") == "local" and r.is_healthy
    )
    cloud: int = sum(
        1
        for r in results
        if getattr(r, "category", "local") == "cloud" and r.is_healthy
    )
    return {
        "local": local,
        "cloud": cloud,
        "total": len(results),
        "healthy": local + cloud,
    }


# ── Legacy aliases (V5/V6 callers) ────────────────────────────────────────────


def scan_providers() -> List[Any]:
    return scan_all_providers()


def select_best_provider(results: List[Any]) -> Tuple[Optional[Any], Optional[str]]:
    healthy: List[Any] = [r for r in results if r.is_healthy and r.models]
    if not healthy:
        return None, None
    best = sorted(healthy, key=lambda r: (-r.model_count, r.response_ms))[0]
    model: str = best.active_model or best.models[0]["name"]
    return best, model


# ── Persistence ────────────────────────────────────────────────────────────────


def _save_last_scan(results: List[Any]) -> None:
    """Guarda de forma thread-safe los resultados de escaneo en _last_scan.json."""
    try:
        data: Dict[str, Any] = {
            "scan_time": time.time(),
            "providers": [
                {
                    "name": r.name,
                    "url": r.url,
                    "protocol": r.protocol,
                    "category": getattr(r, "category", "local"),
                    "is_healthy": r.is_healthy,
                    "model_count": r.model_count,
                    "active_model": r.active_model,
                    "response_ms": r.response_ms,
                    "models": r.models[:3],
                }
                for r in results
            ],
        }
        with _scan_lock:
            tmp_file = LAST_SCAN_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Reemplazo atómico con reintentos para Windows
            for i in range(5):
                try:
                    os.replace(tmp_file, LAST_SCAN_FILE)
                    break
                except PermissionError:
                    time.sleep(0.05)
            else:
                os.replace(tmp_file, LAST_SCAN_FILE)
    except Exception:
        pass


def load_last_scan() -> Dict[str, Any]:
    """Carga de forma thread-safe los resultados de escaneo desde _last_scan.json."""
    try:
        with _scan_lock:
            if not os.path.exists(LAST_SCAN_FILE):
                return {}
            with open(LAST_SCAN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {}
