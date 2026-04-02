"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V2.1    ║
║     Multimodelo | Persistencia | Agentes     ║
╚══════════════════════════════════════════════╝
Comandos:
  !modelos       — Lista los modelos de Ollama disponibles
  !usar <nombre> — Cambia de modelo y guarda la preferencia
  /leer <ruta>   — Audita un archivo físico
  !aprende <reg> — Memoria permanente de largo plazo
  !olvida        — Borra reglas aprendidas
  !limpiar       — Limpia el historial de sesión
  !reglas        — Lista tus reglas actuales
  salir          — Cierra el Auditor
"""

import sys
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich import box

# ─── Configuración base ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
HISTORY_FILE = os.path.join(BASE_DIR, "_history.json")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

console = Console()


# ─── Gestor de Ajustes ───────────────────────────────────────────────────────
class SettingsManager:
    """Gestiona la persistencia del modelo preferido e idiomas."""
    def __init__(self):
        self.default_data = {
            "last_model": "deepseek-r1:8b",
            "agent_language": "en",
            "user_language": "es"
        }
        self.data = self._load()

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return {**self.default_data, **json.load(f)}
            except: pass
        return self.default_data

    def save(self, key, value):
        self.data[key] = value
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    @property
    def current_model(self): return self.data.get("last_model")


# ─── Gestor de Memoria ───────────────────────────────────────────────────────
class MemoryManager:
    """Historial de sesión y base de conocimiento."""
    def __init__(self):
        self.history = self._load(HISTORY_FILE, [])
        self.knowledge = self._load(KNOWLEDGE_FILE, [])

    def _load(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return default

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_turn(self, u_cont, a_cont):
        self.history = (self.history + [{"role": "user", "content": u_cont}, {"role": "assistant", "content": a_cont}])[-12:]
        self._save(HISTORY_FILE, self.history)

    def learn(self, rule):
        if rule and rule not in self.knowledge:
            self.knowledge.append(rule); self._save(KNOWLEDGE_FILE, self.knowledge); return True
        return False

    def clear(self): self.history = []; self._save(HISTORY_FILE, [])
    def forget(self): self.knowledge = []; self._save(KNOWLEDGE_FILE, [])


# ─── Cliente Ollama ───────────────────────────────────────────────────────────
class OllamaClient:
    """Comunicación con el servidor local."""
    def __init__(self, model):
        self.model = model

    def get_available_models(self):
        """Retorna lista de modelos locales."""
        try:
            with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=3) as r:
                return json.loads(r.read().decode())["models"]
        except: return []

    def chat(self, messages):
        payload = json.dumps({"model": self.model, "messages": messages, "stream": False}).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode())["message"]["content"]
        except Exception as e:
            raise ConnectionError(f"Ollama Error: {e}")


# ─── Lógica del Auditor ───────────────────────────────────────────────────────
class AuditorCLI:
    def __init__(self, as_agent=False):
        self.settings = SettingsManager()
        self.memory = MemoryManager()
        self.client = OllamaClient(self.settings.current_model)
        self.as_agent = as_agent

    def _get_system_prompt(self):
        rules = "\n".join(f"- {r}" for r in self.memory.knowledge) if self.memory.knowledge else "None"
        
        # Modo Agente: English high-precision communication
        if self.as_agent:
            return f"""You are the Gravity AI Senior Auditor. You are communicating with another AI Agent.
PROTOCOL:
- RESPOND IN ENGLISH for technical speed and precision.
- Be concise, direct, and rigorous.
- Focus on security, performance, and scalability.
USER RULES TO FOLLOW:
{rules}"""
        
        # Modo Usuario: Spanish professional interaction
        return f"""Eres el Auditor Senior de Gravity AI. Eres un experto riguroso y directo.
PROTOCOL:
- RESPONDE SIEMPRE EN ESPAÑOL.
- Usa Markdown.
- Critica constructivamente basándote en estándares de la industria.
REGLAS APRENDIDAS:
{rules}"""

    def list_models_table(self):
        models = self.client.get_available_models()
        table = Table(title="🤖 Modelos Disponibles en Ollama", border_style="cyan", box=box.ROUNDED)
        table.add_column("Nombre", style="bold green"); table.add_column("Tamaño", style="dim"); table.add_column("Formato")
        for m in models:
            size_gb = f"{m['size'] / 1024**3:.2f} GB"
            table.add_row(m['name'], size_gb, m.get('details', {}).get('format', 'N/A'))
        console.print(table)

    def run_chat(self):
        # Pantalla de bienvenida
        console.print(Panel(Text("GRAVITY AI BRIDGE V2.1\nMultimodelo activado", justify="center", style="bold cyan"), border_style="bright_blue"))
        
        # Verificar si el último modelo existe
        models = [m['name'] for m in self.client.get_available_models()]
        if self.settings.current_model not in models and models:
            console.print(f"[bold red]! El modelo configurado '{self.settings.current_model}' no está disponible.[/]")
            choice = Prompt.ask("Selecciona uno de tus modelos locales", choices=models)
            self.settings.save("last_model", choice)
            self.client.model = choice
        
        console.print(f"[bold cyan]*[ Auditor usando:[/] [bold yellow]{self.client.model}[/] [dim](Graba tus preferencias con !usar)[/]\n")

        while True:
            try:
                inp = input(">> ").strip()
                if not inp or inp.lower() in ('salir', 'exit'): break
                
                if inp.startswith('!modelos'): self.list_models_table(); continue
                if inp.startswith('!usar '):
                    new_m = inp[6:].strip()
                    self.settings.save("last_model", new_m); self.client.model = new_m
                    console.print(f"[bold green]✓ Modelo cambiado a: {new_m}[/]"); continue
                if inp.startswith('!limpiar'): self.memory.clear(); print("[!] Sesión limpia."); continue
                if inp.startswith('!reglas'): self._show_rules(); continue
                if inp.startswith('!aprende '): 
                    if self.memory.learn(inp[9:]): console.print("[+] Regla aprendida.")
                    continue
                
                # Proceso de consulta
                p = inp
                if inp.startswith('/leer '):
                    path = inp[6:].strip()
                    if os.path.exists(path):
                        p = f"Analiza este archivo:\n\n```{open(path, 'r', encoding='utf-8').read()}```"
                        console.print(f"[+] Cargado {path}")
                    else: print("[!] No existe."); continue

                msg = [{"role": "system", "content": self._get_system_prompt()}] + self.memory.history + [{"role": "user", "content": p}]
                console.print(f"[dim]Cerebro ({self.client.model}) pensando...[/]")
                ans = self.client.chat(msg)
                console.print(Rule(style="cyan")); console.print(Markdown(ans)); console.print(Rule(style="cyan"))
                self.memory.add_turn(p, ans)

            except Exception as e: console.print(f"[bold red]Error:[/] {e}")

    def _show_rules(self):
        for i, r in enumerate(self.memory.knowledge, 1): print(f"{i}. {r}")


def main():
    # Detectar si se llama con argumentos (Modo Agente)
    args = sys.argv[1:]
    if args:
        # Si se incluye '--agent' o similar, o simplemente tiene argumentos
        auditor = AuditorCLI(as_agent=True)
        try:
            print(auditor.client.chat([{"role": "system", "content": auditor._get_system_prompt()}, {"role": "user", "content": " ".join(args)}]))
        except Exception as e: print(f"ERROR: {e}"); sys.exit(1)
    else:
        AuditorCLI().run_chat()

if __name__ == "__main__":
    main()
