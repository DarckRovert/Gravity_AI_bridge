"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — IDE INTEGRATOR V15.0 PRO [Diamond-Tier Edition]         ║
║         Módulo aislado para configurar integraciones con IDEs                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Modulo aislado para configurar IDEs de forma segura y thread-safe.
Garantiza exclusión mutua de I/O en la creación de archivos de configuración.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cerrojo reentrante global para prevenir colisiones concurrentes de I/O
_ide_lock: threading.RLock = threading.RLock()


def _safe_write_file(path: str, content: str) -> None:
    """
    Escribe un archivo de forma atómica y thread-safe.
    Escribe en un archivo temporal (.tmp) y luego lo reemplaza de forma atómica
    manejando reintentos por posibles PermissionError en Windows.
    """
    tmp_path: str = path + ".tmp"
    dir_name: str = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    for i in range(5):
        try:
            os.replace(tmp_path, path)
            return
        except PermissionError:
            time.sleep(0.05)
    
    # Intento final forzado (si falla, propagará la excepción)
    os.replace(tmp_path, path)


class IDEIntegrator:
    @staticmethod
    def integrate(tool: str) -> None:
        """
        Integra el ecosistema Gravity con la herramienta IDE indicada.
        """
        tool = tool.strip().lower()
        with _ide_lock:
            if tool == "continue":
                IDEIntegrator._configure_continue()
            elif tool == "aider":
                IDEIntegrator._configure_aider()
            elif tool == "cursor":
                IDEIntegrator._configure_cursor()
            elif tool == "todo":
                IDEIntegrator._configure_continue()
                IDEIntegrator._configure_aider()
                IDEIntegrator._configure_cursor()
            else:
                print(f"[!] Herramienta no reconocida: {tool}. Opciones: continue, aider, cursor, todo")

    @staticmethod
    def _configure_continue() -> None:
        """Configura Continue.dev creando .continue/config.yaml."""
        target_dir: str = os.path.join(BASE_DIR, ".continue")
        cfg: str = (
            "name: Gravity Local V15.0 PRO [Diamond-Tier Edition]\n"
            "version: 10.0.0\n"
            "schema: v1\n"
            "models:\n"
            "  - name: \"Gravity Bridge\"\n"
            "    provider: openai\n"
            "    model: gravity-bridge-auto\n"
            "    apiBase: \"http://localhost:7860/v1\"\n"
            "    apiKey: \"gravity-local\"\n"
        )
        path: str = os.path.join(target_dir, "config.yaml")
        with _ide_lock:
            _safe_write_file(path, cfg)
        print("[OK] Continue.dev configurado en .continue/config.yaml")

    @staticmethod
    def _configure_aider() -> None:
        """Configura Aider creando aider.conf.yml."""
        cfg: str = (
            "openai-api-base: http://localhost:7860/v1\n"
            "openai-api-key: gravity-local\n"
            "model: openai/gravity-bridge-auto\n"
            "auto-commits: false\n"
        )
        path: str = os.path.join(BASE_DIR, "aider.conf.yml")
        with _ide_lock:
            _safe_write_file(path, cfg)
        print("[OK] aider.conf.yml creado en la raiz")

    @staticmethod
    def _configure_cursor() -> None:
        """Configura Cursor en la carpeta de integraciones."""
        target_dir: str = os.path.join(BASE_DIR, "_integrations")
        cfg: Dict[str, Any] = {
            "models": [{
                "name": "Gravity Bridge",
                "provider": "openai",
                "baseUrl": "http://localhost:7860/v1",
                "apiKey": "gravity-local"
            }]
        }
        path: str = os.path.join(target_dir, "cursor.json")
        with _ide_lock:
            content = json.dumps(cfg, indent=2, ensure_ascii=False)
            _safe_write_file(path, content)
        print("[OK] Cursor configurado en _integrations/cursor.json")


if __name__ == "__main__":
    import sys
    tool_arg: str = sys.argv[1] if len(sys.argv) > 1 else "todo"
    IDEIntegrator.integrate(tool_arg)


