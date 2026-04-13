import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    """
    Manages application configuration with YAML support and auto-migration from JSON.
    Supports profiles (dev, prod, test).
    """
    DEFAULT_CONFIG = {
        "version": "9.0",
        "profile": "production",
        "server": {
            "host": "0.0.0.0",
            "port": 7860,
            "cors_allow_all": True
        },
        "model": {
            "default_provider": "LM Studio",
            "default_model": "gravity-bridge-auto",
            "ctx_size": 32768,
            "temperature": 0.6,
            "top_p": 0.9,
            "stream": True
        },
        "observability": {
            "log_level": "INFO",
            "audit_enabled": True,
            "prometheus_enabled": True
        }
    }

    def __init__(self, config_path: str = "config.yaml", old_settings: str = "_settings.json"):
        self.config_path = Path(config_path)
        self.old_settings_path = Path(old_settings)
        self.config = self.DEFAULT_CONFIG.copy()
        
        self.load()

    def load(self):
        """Loads config from YAML, migrates from JSON if necessary."""
        # 1. Intentar migrar si no existe el YAML pero sí el JSON
        if not self.config_path.exists() and self.old_settings_path.exists():
            self._migrate_from_json()
            return

        # 2. Cargar YAML si existe
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._deep_update(self.config, user_config)
            except Exception as e:
                print(f"[CONFIG ERROR] Falló la carga de {self.config_path}: {e}")

    def _migrate_from_json(self):
        """Migrates legacy _settings.json to new config.yaml structure."""
        print(f"[CONFIG] Migrando {self.old_settings_path} a {self.config_path}...")
        try:
            with open(self.old_settings_path, "r", encoding="utf-8") as f:
                old = json.load(f)
            
            # Map old to new
            self.config["server"]["port"] = old.get("bridge_port", 7860)
            self.config["model"]["default_provider"] = old.get("provider", "LM Studio")
            self.config["model"]["default_model"] = old.get("last_model", "gravity-bridge-auto")
            
            adv = old.get("advanced_params", {})
            self.config["model"]["ctx_size"] = adv.get("num_ctx", 32768)
            self.config["model"]["temperature"] = adv.get("temperature", 0.6)
            self.config["model"]["stream"] = adv.get("streaming", True)
            
            self.save()
            print("[CONFIG] Migración completada con éxito.")
        except Exception as e:
            print(f"[CONFIG ERROR] Falló la migración: {e}")

    def _deep_update(self, base_dict: dict, update_with: dict):
        for k, v in update_with.items():
            if isinstance(v, dict) and k in base_dict and isinstance(base_dict[k], dict):
                self._deep_update(base_dict[k], v)
            else:
                base_dict[k] = v

    def save(self):
        """Saves current config to YAML."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[CONFIG ERROR] No se pudo guardar {self.config_path}: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get nested value using dot notation (e.g. 'server.port')."""
        keys = key_path.split(".")
        val = self.config
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val

# Global instance
config = ConfigManager()
