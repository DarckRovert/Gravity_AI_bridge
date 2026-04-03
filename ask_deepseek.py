"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V2.3    ║
║     Contexto 256k | TurboQuant Ready         ║
╚══════════════════════════════════════════════╝
Comandos:
  !modelos       — Lista los modelos de Ollama disponibles
  !usar <nombre> — Cambia de modelo y guarda la preferencia
  /leer <ruta>   — Audita un archivo físico
  !ajustes       — Muestra los parámetros técnicos (Contexto, Temp)
  !set <k> <v>   — Cambia un ajuste (ej: !set temperature 0.4)
  !aprende <reg> — Memoria permanente de largo plazo
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
    def __init__(self):
        self.default_data = {
            "last_model": "deepseek-r1:8b",
            "agent_language": "en",
            "user_language": "es",
            "advanced_params": {
                "num_ctx": 131072,
                "temperature": 0.6,
                "top_p": 0.9,
                "warning_threshold": 0.95
            }
        }
        self.data = self._load()

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                    if "advanced_params" in stored:
                        stored["advanced_params"] = {**self.default_data["advanced_params"], **stored["advanced_params"]}
                    return {**self.default_data, **stored}
            except: pass
        return self.default_data

    def save_all(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def save(self, key, value):
        self.data[key] = value
        self.save_all()

    def update_param(self, param_key, value):
        if "advanced_params" not in self.data: self.data["advanced_params"] = self.default_data["advanced_params"]
        primary_params = self.default_data["advanced_params"]
        try:
            if isinstance(primary_params.get(param_key), int): value = int(value)
            elif isinstance(primary_params.get(param_key), float): value = float(value)
        except: pass
        self.data["advanced_params"][param_key] = value
        self.save_all()

    @property
    def current_model(self): return self.data.get("last_model")
    
    @property
    def options(self): return self.data.get("advanced_params", {})


# ─── Gestor de Memoria ───────────────────────────────────────────────────────
class MemoryManager:
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
        self.history.append({"role": "user", "content": u_cont})
        self.history.append({"role": "assistant", "content": a_cont})
        self._save(HISTORY_FILE, self.history)

    def get_estimated_tokens(self, system_prompt):
        total_chars = len(system_prompt)
        for m in self.history: total_chars += len(m['content'])
        return total_chars // 3 

    def learn(self, rule):
        if rule and rule not in self.knowledge:
            self.knowledge.append(rule); self._save(KNOWLEDGE_FILE, self.knowledge); return True
        return False

    def clear(self): self.history = []; self._save(HISTORY_FILE, [])
    def forget(self): self.knowledge = []; self._save(KNOWLEDGE_FILE, [])


# ─── Cliente Ollama ───────────────────────────────────────────────────────────
class OllamaClient:
    def __init__(self, model):
        self.model = model

    def get_available_models(self):
        try:
            with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=3) as r:
                return json.loads(r.read().decode())["models"]
        except: return []

    def chat(self, messages, options=None):
        payload_dict = {"model": self.model, "messages": messages, "stream": False}
        if options: payload_dict["options"] = options
        
        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r: 
                return json.loads(r.read().decode())["message"]["content"]
        except Exception as e:
            raise ConnectionError(f"Ollama Error: {e}")


# ─── Interfaz del Auditor ────────────────────────────────────────────────────
class AuditorCLI:
    def __init__(self, as_agent=False):
        self.settings = SettingsManager()
        self.memory = MemoryManager()
        self.client = OllamaClient(self.settings.current_model)
        self.as_agent = as_agent

    def _get_system_prompt(self):
        rules = "\n".join(f"- {r}" for r in self.memory.knowledge) if self.memory.knowledge else "Ninguna"
        if self.as_agent:
            return f"Gravity AI Senior Auditor. IA-to-IA English Mode.\nRULES:\n{rules}"
        return f"Eres el Auditor Senior de Gravity AI. Riguroso y experto. Responde en ESPAÑOL.\nREGLAS:\n{rules}"

    def show_settings(self):
        table = Table(title="⚙️ Parámetros de V2.3 (Extreme Context)", box=box.ROUNDED)
        table.add_column("Ajuste", style="cyan"); table.add_column("Valor", style="yellow")
        table.add_row("Modelo", self.client.model)
        for k, v in self.settings.options.items(): table.add_row(k, str(v))
        
        usage = self.memory.get_estimated_tokens(self._get_system_prompt())
        limit = self.settings.options.get('num_ctx', 2048)
        table.add_row("Uso de Contexto Est.", f"{usage} / {limit} ({(usage/limit)*100:.1f}%)")
        console.print(table)

    def _list_models(self):
        models = self.client.get_available_models()
        tab = Table(title="🤖 Inventario Local", box=box.SIMPLE); tab.add_column("Nombre"); tab.add_column("Peso")
        for m in models: tab.add_row(m['name'], f"{m['size']/1024**3:.1f} GB")
        console.print(tab)

    def run_chat(self):
        console.print(Panel(Text("GRAVITY AI BRIDGE V2.3\nContexto Pesado Activo", justify="center", style="bold cyan")))
        console.print(f"[bold cyan]*[ Cerebro:[/] [bold yellow]{self.client.model}[/] [dim]Opciones avanzadas cargadas.[/]\n")

        while True:
            try:
                # Comprobar límite de 95%
                usage = self.memory.get_estimated_tokens(self._get_system_prompt())
                limit = self.settings.options.get('num_ctx', 2048)
                if usage > (limit * self.settings.options.get('warning_threshold', 0.95)):
                    console.print("[bold red]⚠ ALERTA: Has superado el 95% del contexto permitido.[/]")

                inp = Prompt.ask("[bold green]>>[/]").strip()
                if not inp or inp.lower() in ('salir', 'exit'): break
                
                if inp == '!ajustes': self.show_settings(); continue
                if inp.startswith('!set '):
                    try:
                        parts = inp.split(' ')
                        self.settings.update_param(parts[1], parts[2])
                        console.print(f"[green]✓ {parts[1]} actualizado.[/]"); continue
                    except: console.print("[red]Uso: !set <key> <value>[/]"); continue

                if inp == '!modelos': self._list_models(); continue
                if inp.startswith('!usar '):
                    m = inp[6:].strip(); self.settings.save("last_model", m); self.client.model = m
                    console.print(f"[green]✓ Usando {m}[/]"); continue
                
                if inp == '!limpiar': self.memory.clear(); console.print("[yellow]Sesión limpia.[/]"); continue
                if inp == '!reglas': 
                    for i, r in enumerate(self.memory.knowledge, 1): print(f"{i}. {r}")
                    continue
                if inp.startswith('!aprende '):
                    if self.memory.learn(inp[9:]): console.print("[green]Regla grabada.[/]")
                    continue

                # Procesar entrada
                p = inp
                if inp.startswith('/leer '):
                    path = inp[6:].strip()
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8') as f: p = f"Analiza este archivo:\n\n```\n{f.read()}\n```"
                        console.print(f"[blue]Archivo {path} cargado.[/]")
                    else: console.print("[red]No existe.[/]"); continue

                msg = [{"role": "system", "content": self._get_system_prompt()}] + self.memory.history + [{"role": "user", "content": p}]
                console.print(f"[dim]DeepSeek pensando ({usage} tokens)...[/]")
                ans = self.client.chat(msg, options=self.settings.options)
                console.print(Rule(style="cyan")); console.print(Markdown(ans)); console.print(Rule(style="cyan"))
                self.memory.add_turn(p, ans)

            except Exception as e: console.print(f"[red]Error:[/] {e}")

def main():
    args = sys.argv[1:]
    if args:
        a = AuditorCLI(as_agent=True)
        try:
            print(a.client.chat([{"role":"system","content":a._get_system_prompt()},{"role":"user","content":" ".join(args)}], options=a.settings.options))
        except Exception as e: print(f"ERROR: {e}")
    else:
        AuditorCLI().run_chat()

if __name__ == "__main__":
    main()
