"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V2    ║
║         Powered by Ollama + DeepSeek         ║
╚══════════════════════════════════════════════╝
Comandos disponibles:
  /leer <ruta>   — Carga un archivo y lo audita
  !aprende <reg> — Guarda una regla en la memoria permanente
  !olvida        — Borra todas las reglas aprendidas
  !limpiar       — Limpia el historial de la sesión actual
  !reglas        — Lista las reglas que el Auditor recuerda
  salir / exit   — Cierra el Auditor
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

# ─── Configuración global ────────────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "_history.json")
KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), "_knowledge.json")
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1:8b"
MAX_HISTORY = 12  # máximo de turnos a mantener en memoria de sesión

SYSTEM_PROMPT_TEMPLATE = """\
Eres el **Auditor Senior** del sistema Gravity AI. Eres un experto técnico riguroso, \
directo y con criterio propio. Tu misión es auditar código, arquitecturas y decisiones \
técnicas con el nivel de exigencia de un Senior de 15 años de experiencia.

**PROTOCOLO DE AUDITORÍA:**
- Responde siempre en español.
- Señala problemas de seguridad, rendimiento y mantenibilidad sin rodeos.
- Sugiere la solución concreta, no solo el problema.
- Usa Markdown en tus respuestas: encabezados, listas, bloques de código.
- Si el código es bueno, dilo también. No hagas crítica destructiva, sino constructiva.

**REGLAS APRENDIDAS DEL USUARIO (máxima prioridad):**
{rules}
"""

console = Console()


# ─── Gestor de Memoria ───────────────────────────────────────────────────────
class MemoryManager:
    """Gestiona la memoria de sesión (historial) y la de largo plazo (reglas)."""

    def __init__(self):
        self.history: list[dict] = self._load(HISTORY_FILE, [])
        self.knowledge: list[str] = self._load(KNOWLEDGE_FILE, [])

    @staticmethod
    def _load(path: str, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
        return default

    @staticmethod
    def _save(path: str, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_turn(self, user_content: str, assistant_content: str):
        self.history.append({"role": "user", "content": user_content})
        self.history.append({"role": "assistant", "content": assistant_content})
        # Mantener solo los últimos MAX_HISTORY mensajes
        self.history = self.history[-MAX_HISTORY:]
        self._save(HISTORY_FILE, self.history)

    def clear_history(self):
        self.history = []
        self._save(HISTORY_FILE, [])

    def learn(self, rule: str):
        if rule and rule not in self.knowledge:
            self.knowledge.append(rule)
            self._save(KNOWLEDGE_FILE, self.knowledge)
            return True
        return False

    def forget_all(self):
        self.knowledge = []
        self._save(KNOWLEDGE_FILE, [])

    def get_system_prompt(self) -> str:
        if self.knowledge:
            rules_text = "\n".join(f"- {r}" for r in self.knowledge)
        else:
            rules_text = "_(Sin reglas aprendidas todavía. Usa `!aprende <regla>` para añadir.)_"
        return SYSTEM_PROMPT_TEMPLATE.format(rules=rules_text)

    def build_messages(self, user_input: str) -> list[dict]:
        return (
            [{"role": "system", "content": self.get_system_prompt()}]
            + self.history
            + [{"role": "user", "content": user_input}]
        )


# ─── Cliente Ollama ───────────────────────────────────────────────────────────
class OllamaClient:
    """Maneja la comunicación con la API local de Ollama."""

    def __init__(self, url: str = OLLAMA_URL, model: str = MODEL):
        self.url = url
        self.model = model

    def chat(self, messages: list[dict]) -> str:
        payload = json.dumps(
            {"model": self.model, "messages": messages, "stream": False}
        ).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["message"]["content"]
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"No se pudo conectar con Ollama en {self.url}.\n"
                f"Asegúrate de que Ollama esté corriendo. Detalle: {e}"
            ) from e

    def ping(self) -> bool:
        """Verifica que Ollama responda."""
        try:
            urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=5
            )
            return True
        except Exception:
            return False


# ─── Interfaz CLI del Auditor ─────────────────────────────────────────────────
class AuditorCLI:
    """Interfaz de línea de comandos enriquecida para el Auditor Senior."""

    def __init__(self):
        self.memory = MemoryManager()
        self.client = OllamaClient()

    def _banner(self):
        console.clear()
        banner = Text()
        banner.append("  ██████╗ ██████╗  █████╗ ██╗   ██╗██╗████████╗██╗   ██╗\n", style="bold cyan")
        banner.append("  ██╔════╝ ██╔══██╗██╔══██╗██║   ██║██║╚══██╔══╝╚██╗ ██╔╝\n", style="bold cyan")
        banner.append("  ██║  ███╗██████╔╝███████║██║   ██║██║   ██║    ╚████╔╝ \n", style="bold blue")
        banner.append("  ██║   ██║██╔══██╗██╔══██║╚██╗ ██╔╝██║   ██║    ╚██╔╝  \n", style="bold blue")
        banner.append("  ╚██████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║   ██║     ██║   \n", style="bold magenta")
        banner.append("   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝   ╚═╝     ╚═╝   \n", style="bold magenta")
        banner.append("          AI BRIDGE — AUDITOR SENIOR V2.0\n", style="bold white")
        console.print(Panel(banner, border_style="bright_cyan", padding=(0, 2)))

        # Tabla de estado
        status_table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 1))
        status_table.add_column("key", style="bold yellow")
        status_table.add_column("value", style="white")
        ollama_ok = self.client.ping()
        status_table.add_row("🤖 Modelo", MODEL)
        status_table.add_row(
            "🔌 Ollama",
            "[bold green]✓ Conectado[/]" if ollama_ok else "[bold red]✗ Sin conexión[/]",
        )
        status_table.add_row("💾 Reglas en memoria", str(len(self.memory.knowledge)))
        status_table.add_row("💬 Historial de sesión", f"{len(self.memory.history) // 2} turnos")
        status_table.add_row(
            "📅 Sesión iniciada",
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        )
        console.print(status_table)

        # Ayuda rápida
        help_text = (
            "[bold cyan]/leer[/] [dim]<ruta>[/]  "
            "[bold cyan]!aprende[/] [dim]<regla>[/]  "
            "[bold cyan]!olvida[/]  "
            "[bold cyan]!limpiar[/]  "
            "[bold cyan]!reglas[/]  "
            "[bold cyan]salir[/]"
        )
        console.print(
            Panel(help_text, title="Comandos", border_style="dim", padding=(0, 1))
        )
        console.print()

        if not ollama_ok:
            console.print(
                Panel(
                    "[bold red]⚠ Ollama no responde.[/] Inicia el servicio con [bold yellow]ollama serve[/] "
                    "y asegúrate de tener el modelo:[/]\n[dim]  ollama pull deepseek-r1:8b[/]",
                    border_style="red",
                )
            )

    def _handle_leer(self, path: str) -> str | None:
        """Carga un archivo y devuelve su contenido como prompt de auditoría."""
        path = path.strip().strip('"').strip("'")
        if not os.path.exists(path):
            console.print(f"[bold red]✗[/] Archivo no encontrado: [yellow]{path}[/]")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            console.print(f"[bold red]✗[/] Error leyendo el archivo: {e}")
            return None

        ext = os.path.splitext(path)[1].lstrip(".")
        lang = ext if ext else "text"
        console.print(
            Panel(
                f"[bold green]✓[/] Archivo cargado: [cyan]{os.path.basename(path)}[/] "
                f"[dim]({len(content.splitlines())} líneas)[/]",
                border_style="green",
            )
        )
        return (
            f"A continuación está el contenido del archivo `{os.path.basename(path)}`. "
            f"Por favor, auditalo completamente:\n\n```{lang}\n{content}\n```"
        )

    def _show_rules(self):
        if not self.memory.knowledge:
            console.print("[dim]No hay reglas aprendidas todavía.[/]")
            return
        table = Table(
            title="📚 Reglas en Memoria Permanente",
            box=box.ROUNDED,
            border_style="cyan",
            show_lines=True,
        )
        table.add_column("#", style="bold yellow", width=4)
        table.add_column("Regla", style="white")
        for i, rule in enumerate(self.memory.knowledge, 1):
            table.add_row(str(i), rule)
        console.print(table)

    def _think_and_respond(self, user_input: str):
        """Envía el mensaje al LLM y renderiza la respuesta."""
        messages = self.memory.build_messages(user_input)
        with console.status(
            "[bold cyan]🧠 El Auditor está analizando...[/]", spinner="dots"
        ):
            response = self.client.chat(messages)

        self.memory.add_turn(user_input, response)
        console.print(Rule("[bold cyan]Auditor Senior[/]", style="cyan"))
        console.print(Markdown(response))
        console.print(Rule(style="dim"))
        console.print()

    def run(self):
        """Bucle principal de la interfaz interactiva."""
        self._banner()

        while True:
            try:
                user_input = Prompt.ask("[bold yellow]▶ Tú[/]").strip()

                if not user_input:
                    continue

                # Salida
                if user_input.lower() in ("salir", "exit", "quit"):
                    console.print(
                        Panel(
                            "[bold cyan]Hasta pronto. El Auditor cierra sesión.[/]",
                            border_style="cyan",
                        )
                    )
                    break

                # !limpiar
                elif user_input.startswith("!limpiar"):
                    self.memory.clear_history()
                    console.print("[bold green]✓[/] Historial de sesión borrado.")

                # !aprende
                elif user_input.startswith("!aprende "):
                    rule = user_input[9:].strip()
                    if not rule:
                        console.print("[red]✗[/] Debes escribir la regla después de [cyan]!aprende[/].")
                        continue
                    if self.memory.learn(rule):
                        console.print(
                            Panel(
                                f"[bold green]✓ Aprendido:[/] {rule}",
                                border_style="green",
                            )
                        )
                    else:
                        console.print("[yellow]⚠[/] Esa regla ya existe en la memoria.")

                # !olvida
                elif user_input.startswith("!olvida"):
                    self.memory.forget_all()
                    console.print("[bold yellow]⚠[/] Todas las reglas aprendidas han sido borradas.")

                # !reglas
                elif user_input.startswith("!reglas"):
                    self._show_rules()

                # /leer
                elif user_input.startswith("/leer "):
                    path = user_input[6:]
                    prompt = self._handle_leer(path)
                    if prompt:
                        self._think_and_respond(prompt)

                # Pregunta normal
                else:
                    self._think_and_respond(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Interrumpido. Escribe [cyan]salir[/] para salir correctamente.[/]")
            except ConnectionError as e:
                console.print(
                    Panel(f"[bold red]Error de conexión:[/]\n{e}", border_style="red")
                )
            except Exception as e:
                console.print(
                    Panel(f"[bold red]Error inesperado:[/] {e}", border_style="red")
                )


# ─── Punto de entrada ─────────────────────────────────────────────────────────
def main():
    if len(sys.argv) > 1:
        # Modo headless: consulta directa desde CLI sin interfaz interactiva
        question = " ".join(sys.argv[1:])
        client = OllamaClient()
        memory = MemoryManager()
        messages = memory.build_messages(question)
        try:
            answer = client.chat(messages)
            console.print(Markdown(answer))
        except ConnectionError as e:
            console.print(f"[bold red]Error:[/] {e}")
            sys.exit(1)
    else:
        AuditorCLI().run()


if __name__ == "__main__":
    main()
