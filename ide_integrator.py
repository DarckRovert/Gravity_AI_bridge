"""
ide_integrator.py — Gravity AI Bridge V7.1 Omni-Tier
Modulo aislado para configurar IDEs. Sin dependencias de Rich ni SettingsManager.
Se puede importar de forma segura desde el instalador.
"""
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class IDEIntegrator:
    @staticmethod
    def integrate(tool):
        tool = tool.strip().lower()
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
    def _configure_continue():
        target_dir = os.path.join(BASE_DIR, ".continue")
        os.makedirs(target_dir, exist_ok=True)
        cfg = (
            "name: Gravity Local V7.0 Omni-Tier\n"
            "version: 7.0.0\n"
            "schema: v1\n"
            "models:\n"
            "  - name: \"Gravity Bridge\"\n"
            "    provider: openai\n"
            "    model: gravity-bridge-auto\n"
            "    apiBase: \"http://localhost:7860/v1\"\n"
            "    apiKey: \"gravity-local\"\n"
        )
        path = os.path.join(target_dir, "config.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(cfg)
        print("[OK] Continue.dev configurado en .continue/config.yaml")

    @staticmethod
    def _configure_aider():
        cfg = (
            "openai-api-base: http://localhost:7860/v1\n"
            "openai-api-key: gravity-local\n"
            "model: openai/gravity-bridge-auto\n"
            "auto-commits: false\n"
        )
        path = os.path.join(BASE_DIR, "aider.conf.yml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(cfg)
        print("[OK] aider.conf.yml creado en la raiz")

    @staticmethod
    def _configure_cursor():
        target_dir = os.path.join(BASE_DIR, "_integrations")
        os.makedirs(target_dir, exist_ok=True)
        cfg = {
            "models": [{
                "name": "Gravity Bridge",
                "provider": "openai",
                "baseUrl": "http://localhost:7860/v1",
                "apiKey": "gravity-local"
            }]
        }
        path = os.path.join(target_dir, "cursor.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print("[OK] Cursor configurado en _integrations/cursor.json")


if __name__ == "__main__":
    import sys
    tool = sys.argv[1] if len(sys.argv) > 1 else "todo"
    IDEIntegrator.integrate(tool)
