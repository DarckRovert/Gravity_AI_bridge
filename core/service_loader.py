"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               GRAVITY AI - CORE SERVICE LOADER V15.1 PRO                     ║
║           Dynamic and Exception-Tolerant Lazy Loader for Services            ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

import importlib
import sys
from core.logger import log

_SERVICES_STATUS = {}

def load_module(module_name: str):
    """
    Safely imports a module dynamically.
    If the import fails, logs the error and returns None instead of crashing.
    """
    try:
        if module_name in sys.modules:
            return sys.modules[module_name]
        
        log.debug(f"[ServiceLoader] Safely importing dynamic module: {module_name}")
        module = importlib.import_module(module_name)
        _SERVICES_STATUS[module_name] = "loaded"
        return module
    except Exception as e:
        log.error(f"[ServiceLoader] Failed to dynamically load module '{module_name}': {e}", exc_info=True)
        _SERVICES_STATUS[module_name] = "failed"
        return None

def start_service(module_name: str, start_func_name: str = "start", *args, **kwargs) -> bool:
    """
    Safely loads a module and executes its startup function.
    Returns True if the service started successfully, False otherwise.
    """
    module = load_module(module_name)
    if not module:
        log.warning(f"[ServiceLoader] Skipping startup for service '{module_name}' because it could not be imported.")
        _SERVICES_STATUS[module_name] = "failed"
        return False
        
    start_func = getattr(module, start_func_name, None)
    if not start_func:
        log.warning(f"[ServiceLoader] Module '{module_name}' has no '{start_func_name}' function. Marking as active (no startup needed).")
        _SERVICES_STATUS[module_name] = "active"
        return True
        
    try:
        log.info(f"[ServiceLoader] Starting background service: {module_name}.{start_func_name}()")
        start_func(*args, **kwargs)
        _SERVICES_STATUS[module_name] = "active"
        return True
    except Exception as e:
        log.error(f"[ServiceLoader] Crash detected during startup of service '{module_name}': {e}", exc_info=True)
        _SERVICES_STATUS[module_name] = "failed"
        return False

def get_status(module_name: str) -> str:
    """Returns the current runtime status of a service."""
    return _SERVICES_STATUS.get(module_name, "unknown")

def get_all_statuses() -> dict:
    """Returns a copy of the services status map."""
    return _SERVICES_STATUS.copy()
