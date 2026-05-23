"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               GRAVITY AI - CORE INTEGRATION MANAGER V15.1 PRO                ║
║           Dynamic Scanner, Loader, and Orchestrator of Plugins               ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

import os
import sys
import importlib
import inspect
import threading
from typing import Dict, Any, Optional
from core.logger import log
from core.base_plugin import GravityIntegration

_LOADED_INTEGRATIONS: Dict[str, Dict[str, Any]] = {}
_manager_lock = threading.Lock()
INTEGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "integrations")

def get_integrations_path() -> str:
    return INTEGRATIONS_DIR

def scan_and_load_integrations() -> dict:
    """
    Scans the '/integrations' folder for directories containing subclasses of GravityIntegration.
    Imports and instantiates them, registering them dynamically.
    """
    with _manager_lock:
        if not os.path.exists(INTEGRATIONS_DIR):
            try:
                os.makedirs(INTEGRATIONS_DIR, exist_ok=True)
                log.info(f"[IntegrationManager] Created empty integrations directory at: {INTEGRATIONS_DIR}")
            except Exception as e:
                log.error(f"[IntegrationManager] Failed to create integrations directory: {e}")
                return {}

        # Asegurar que el directorio raíz del proyecto y de las integraciones estén en el path
        root_dir = os.path.dirname(INTEGRATIONS_DIR)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
            
        log.info("[IntegrationManager] Scanning '/integrations' directory for plugins...")
        
        for item in os.listdir(INTEGRATIONS_DIR):
            item_path = os.path.join(INTEGRATIONS_DIR, item)
            if not os.path.isdir(item_path) or item.startswith("__") or item.startswith("."):
                continue
                
            plugin_module_name = f"integrations.{item}"
            try:
                # Buscar archivo de punto de entrada (por defecto cargamos __init__.py en el folder de la integración)
                log.debug(f"[IntegrationManager] Loading plugin package: {plugin_module_name}")
                module = importlib.import_module(plugin_module_name)
                
                # Buscar subclases de GravityIntegration
                found_class = False
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, GravityIntegration) and obj is not GravityIntegration:
                        try:
                            instance = obj()
                            _LOADED_INTEGRATIONS[instance.name] = {
                                "instance": instance,
                                "module": module,
                                "folder": item,
                                "status": "loaded"
                            }
                            log.info(f"[IntegrationManager] Successfully registered plugin: '{instance.name}' ({instance.description})")
                            found_class = True
                        except Exception as inst_err:
                            log.error(f"[IntegrationManager] Failed to instantiate plugin class {name} from {plugin_module_name}: {inst_err}")
                
                if not found_class:
                    log.debug(f"[IntegrationManager] Loaded module '{plugin_module_name}' but found no valid GravityIntegration subclass.")
                    
            except Exception as mod_err:
                log.error(f"[IntegrationManager] Error loading plugin folder '{item}': {mod_err}", exc_info=True)
                
        return _LOADED_INTEGRATIONS.copy()

def initialize_all() -> bool:
    """Initializes all successfully loaded integrations."""
    if not _LOADED_INTEGRATIONS:
        scan_and_load_integrations()
        
    with _manager_lock:
        all_ok = True
        for name, data in _LOADED_INTEGRATIONS.items():
            if data["status"] != "loaded":
                continue
            try:
                log.info(f"[IntegrationManager] Initializing integration plugin: '{name}'...")
                success = data["instance"].initialize()
                if success:
                    data["status"] = "active"
                    log.info(f"[IntegrationManager] Plugin '{name}' initialized successfully.")
                else:
                    data["status"] = "failed"
                    log.error(f"[IntegrationManager] Plugin '{name}' reported initialization failure.")
                    all_ok = False
            except Exception as e:
                data["status"] = "failed"
                log.error(f"[IntegrationManager] Crash occurred during initialization of plugin '{name}': {e}", exc_info=True)
                all_ok = False
                
        return all_ok

def shutdown_all() -> bool:
    """Tears down and cleans up all active integrations."""
    with _manager_lock:
        all_ok = True
        for name, data in _LOADED_INTEGRATIONS.items():
            if data["status"] != "active":
                continue
            try:
                log.info(f"[IntegrationManager] Shutting down plugin: '{name}'...")
                success = data["instance"].shutdown()
                if success:
                    data["status"] = "stopped"
                    log.info(f"[IntegrationManager] Plugin '{name}' stopped cleanly.")
                else:
                    data["status"] = "failed"
                    log.error(f"[IntegrationManager] Plugin '{name}' reported shutdown errors.")
                    all_ok = False
            except Exception as e:
                data["status"] = "failed"
                log.error(f"[IntegrationManager] Crash occurred during shutdown of plugin '{name}': {e}", exc_info=True)
                all_ok = False
                
        return all_ok

def get_plugin(name: str) -> Optional[GravityIntegration]:
    """Retrieves the active instance of a registered plugin."""
    with _manager_lock:
        plugin_data = _LOADED_INTEGRATIONS.get(name)
        return plugin_data["instance"] if plugin_data and plugin_data["status"] == "active" else None

def get_all_plugin_statuses() -> dict:
    """Returns a dictionary showing names, descriptions, and statuses of all plugins."""
    with _manager_lock:
        return {
            name: {
                "description": data["instance"].description,
                "status": data["status"]
            }
            for name, data in _LOADED_INTEGRATIONS.items()
        }

