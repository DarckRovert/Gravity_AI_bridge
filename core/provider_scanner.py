"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI PROVIDER SCANNER V7.1 — Compatibility Wrapper ║
║     Delegates to ProviderManager + ProviderRegistry         ║
╚══════════════════════════════════════════════════════════════╝
This file is a BACKWARDS-COMPATIBLE wrapper around the new
ProviderRegistry/ProviderManager system introduced in V7.1.
All existing callers (health_check.py, engine_watchdog.py, etc.)
continue to work without modification.
"""

import os
import json
import time

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAST_SCAN_FILE = os.path.join(BASE_DIR, "_last_scan.json")

# Re-export ProviderResult from the canonical location for backwards compat
from providers.base import ProviderResult  # noqa: F401


# ── Public API (unchanged from V6) ────────────────────────────────────────────

def scan_all_providers(force: bool = False) -> list:
    """
    Scans all local AND cloud providers using the V7 ProviderRegistry.
    Returns list of ProviderResult objects (backwards-compatible).
    """
    from core.provider_manager import scan_all
    results = scan_all(force=force)
    _save_last_scan(results)
    return results


def auto_select_best(task: str = "any", prefer_local: bool = True) -> tuple:
    """
    Auto-selects the best provider and model for the given task.
    Returns (ProviderResult | None, model_name | None).
    """
    from core.provider_manager import get_best
    return get_best(task)


def get_provider_by_name(name: str):
    """Returns ProviderResult for a specific provider name, or None."""
    results = scan_all_providers()
    name_l  = name.lower()
    return next((r for r in results if r.name.lower() == name_l), None)


def get_available_models(provider_name: str) -> list:
    """Returns list of model names for a given provider."""
    r = get_provider_by_name(provider_name)
    return [m["name"] for m in r.models] if r and r.is_healthy else []


def get_all_local_providers() -> list:
    return [r for r in scan_all_providers() if getattr(r, "category", "local") == "local"]


def get_all_cloud_providers() -> list:
    return [r for r in scan_all_providers() if getattr(r, "category", "local") == "cloud"]


def get_provider_count() -> dict:
    results = scan_all_providers()
    local   = sum(1 for r in results if getattr(r,"category","local") == "local"  and r.is_healthy)
    cloud   = sum(1 for r in results if getattr(r,"category","local") == "cloud"  and r.is_healthy)
    return {"local": local, "cloud": cloud, "total": len(results), "healthy": local + cloud}


# ── Legacy aliases (V5/V6 callers) ────────────────────────────────────────────

def scan_providers() -> list:
    return scan_all_providers()


def select_best_provider(results: list) -> tuple:
    healthy = [r for r in results if r.is_healthy and r.models]
    if not healthy:
        return None, None
    best  = sorted(healthy, key=lambda r: (-r.model_count, r.response_ms))[0]
    model = best.active_model or best.models[0]["name"]
    return best, model


# ── Persistence ────────────────────────────────────────────────────────────────

def _save_last_scan(results: list) -> None:
    try:
        data = {
            "scan_time": time.time(),
            "providers": [
                {
                    "name":       r.name,
                    "url":        r.url,
                    "protocol":   r.protocol,
                    "category":   getattr(r, "category", "local"),
                    "is_healthy": r.is_healthy,
                    "model_count": r.model_count,
                    "active_model": r.active_model,
                    "response_ms": r.response_ms,
                    "models":      r.models[:3],
                }
                for r in results
            ],
        }
        with open(LAST_SCAN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load_last_scan() -> dict:
    try:
        with open(LAST_SCAN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
