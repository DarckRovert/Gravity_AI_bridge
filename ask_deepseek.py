"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V8.0 PRO              ║
║     CLI Frontend | RAG | Tools | Multi-model                 ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys
import io
import json
import os
import time
from datetime import datetime

# UTF-8 enforcement (Windows)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
if sys.stdin and sys.stdin.encoding != "utf-8":
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    except Exception:
        pass

from rich.console  import Console
from rich.panel    import Panel
from rich.prompt   import Prompt, Confirm
from rich.table    import Table
from rich.columns  import Columns
from rich.align    import Align
from rich          import box
import pyfiglet


# ── V8.0 Integrations ──────────────────────────────────────────────────────────
import provider_manager
from core.config_manager import config
from session_manager import SessionManager
from cost_tracker    import CostTracker
from tool_executor   import executor as tools
from rag.retriever   import RAGRetriever, RAGIndexer
from cache_engine    import CacheEngine
import hardware_profiler
from core.verification_agent import VerificationAgent
from key_manager import KeyManager
import data_guardian as guardian


try:
    import pyreadline3
except ImportError:
    pass

# ── Reasoning Stripper (V7.1 Optimization) ──────────────────────────────────
class ReasoningStripper:
    def __init__(self):
        self.in_reasoning = False
        self.buffer = ""
        self.start_tags = ["<think>", "<|canal>pensamiento"]
        self.end_tags   = ["</think>", "<channel|>"]

    def process_chunk(self, text: str) -> str:
        self.buffer += text
        output = ""
        while self.buffer:
            if not self.in_reasoning:
                closest_start = -1
                for tag in self.start_tags:
                    pos = self.buffer.find(tag)
                    if pos != -1 and (closest_start == -1 or pos < closest_start):
                        closest_start = pos
                if closest_start != -1:
                    output += self.buffer[:closest_start]
                    self.buffer = self.buffer[closest_start:]
                    matched_tag = next((t for t in self.start_tags if self.buffer.startswith(t)), None)
                    if matched_tag:
                        self.buffer = self.buffer[len(matched_tag):]
                        self.in_reasoning = True
                else:
                    if any(tag.startswith(self.buffer[-1:]) for tag in self.start_tags): break
                    output += self.buffer
                    self.buffer = ""
            else:
                closest_end = -1
                for tag in self.end_tags:
                    pos = self.buffer.find(tag)
                    if pos != -1 and (closest_end == -1 or pos < closest_end):
                        closest_end = pos
                if closest_end != -1:
                    self.buffer = self.buffer[closest_end:]
                    matched_tag = next((t for t in self.end_tags if self.buffer.startswith(t)), None)
                    if matched_tag:
                        self.buffer = self.buffer[len(matched_tag):]
                        self.in_reasoning = False
                else:
                    self.buffer = ""
                    break
        return output

APP_VERSION    = "8.0 PRO"
BASE_DIR       = os.path.dirname(__file__)
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")

console = Console()

class SettingsManager:
    """Surgical wrapper for ConfigManager V8.0 compatibility."""
    def __init__(self):
        self.config = config
        self.data = {
            "mode": config.get("profile", "production"),
            "agent_language": config.get("model.agent_language", "en"),
            "user_language": config.get("model.user_language", "es"),
            "model_locked": False,
            "locked_model": config.get("model.default_model", "gravity-bridge-auto"),
            "locked_provider": config.get("model.default_provider", "LM Studio"),
            "advanced_params": {
                "num_ctx": config.get("model.ctx_size", 32768),
                "temperature": config.get("model.temperature", 0.6),
                "top_p": config.get("model.top_p", 0.9),
                "streaming": config.get("model.stream", True),
            }
        }

    def save(self):
        config.config["model"]["ctx_size"] = self.data["advanced_params"]["num_ctx"]
        config.config["model"]["temperature"] = self.data["advanced_params"]["temperature"]
        config.save()

    @property
    def mode(self): return self.data.get("mode", "production")
    @mode.setter
    def mode(self, v): self.data["mode"] = v; self.save()


FIRST_RUN_FILE = os.path.join(BASE_DIR, "_first_run_done")


def first_run_check():
    """Wizard de bienvenida para primera ejecución. Ejecuta solo una vez."""
    if os.path.exists(FIRST_RUN_FILE):
        return
    _console = Console()
    _console.clear()
    fig = pyfiglet.Figlet(font="slant")
    _console.print(f"[bold bright_cyan]{fig.renderText('GRAVITY AI').rstrip()}[/]")
    _console.print(Panel(
        Align.center(
            "[bold white]Bienvenido a Gravity AI Bridge V8.0 PRO[/]\n"
            "[dim]Primera ejecución detectada. Configuración inicial.[/]"
        ),
        border_style="cyan", box=box.DOUBLE, padding=(1, 6)
    ))
    _console.print()

    # ── Detectar motores locales ──────────────────────────────────────────────
    import urllib.request as _ur
    engines_found = {}
    for port, name in [(11434, "Ollama"), (1234, "LM Studio"), (8080, "KoboldCPP"), (8000, "vLLM")]:
        try:
            _ur.urlopen(f"http://localhost:{port}", timeout=1)
            engines_found[name] = f"http://localhost:{port}"
        except Exception:
            pass

    if engines_found:
        _console.print(f"[green]✓ Motores locales detectados:[/] {', '.join(engines_found.keys())}")
    else:
        _console.print("[yellow]⚠  No se detectaron motores de IA locales.[/]")
        _console.print("[dim]  Instala Ollama (ollama.ai) para usar modelos locales, o configura un proveedor cloud.[/]")

    _console.print()

    # ── Ofrecer configurar API key cloud ─────────────────────────────────────
    if not engines_found:
        if Confirm.ask("[cyan]¿Deseas configurar una API Key de proveedor cloud ahora?[/]", default=True):
            proveedores = ["openai", "anthropic", "groq", "google", "cohere", "otro"]
            for i, p in enumerate(proveedores):
                _console.print(f"  [{i}] {p}")
            sel = Prompt.ask("Proveedor", default="0")
            try:
                prov = proveedores[int(sel)]
            except Exception:
                prov = sel
            key = Prompt.ask(f"API Key para [cyan]{prov}[/]", password=True)
            if key.strip():
                from key_manager import KeyManager
                KeyManager.set_key(prov, key.strip())
                _console.print(f"[green]✓ Clave guardada cifrada.[/]")
        _console.print()

    # ── Tutorial rápido ───────────────────────────────────────────────────────
    t = Table(title="[bold cyan]Comandos esenciales para empezar[/]", box=box.SIMPLE_HEAD, padding=(0,2))
    t.add_column("Comando", style="cyan", width=24)
    t.add_column("Qué hace")
    t.add_row("/help",         "Lista todos los comandos disponibles")
    t.add_row("/model",        "Cambia el motor o modelo activo")
    t.add_row("/keys set",     "Añade una API Key cifrada")
    t.add_row("/search",       "Búsqueda web en vivo con inyección de contexto")
    t.add_row("/verify",       "Audita un archivo con el Agente de Verificación")
    t.add_row("!aprende",      "Persiste una regla en el knowledge base")
    t.add_row("/plan",         "Modo planificación antes de codificar")
    t.add_row("/exit",         "Salir limpiamente")
    _console.print(t)
    _console.print()
    _console.print("[dim]Este mensaje solo aparece la primera vez. Escribe [bold]/help[/] en cualquier momento.[/]")
    _console.print()
    input("  Presiona ENTER para iniciar...")

    # Marcar como hecho
    try:
        with open(FIRST_RUN_FILE, "w") as f:
            f.write("done")
    except Exception:
        pass


class AuditorCLI:
    def __init__(self):
        self.sm = SettingsManager()
        self.history = []
        self.session = SessionManager(self.history)
        self.verifier = VerificationAgent(self.sm.data)
        # Chequeo de integridad PRIMERO: carga knowledge una sola vez
        kb_data, startup_warnings = guardian.startup_check(BASE_DIR)
        self.system_prompt = self._load_system_prompt(kb_data=kb_data)
        self.history.append({"role": "system", "content": self.system_prompt})
        provider_manager.scan_all()
        # Mostrar advertencias del guardian tras el scan (antes del banner)
        for w in startup_warnings:
            console.print(f"[yellow]⚠ Guardian: {w}[/]")




    def _load_system_prompt(self, kb_data: dict = None) -> str:
        """Construye el system prompt. Si kb_data se provee, no relee el disco."""
        base = (
            f"Eres Gravity AI v{APP_VERSION}, Auditor Senior. "
            "PROTOCOLO: Lógica interna en inglés. Salida final en español estrictamente. "
            "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa. "
            "COMPORTAMIENTO: Sin disculpas. Sin especulación. Reporta resultados de herramientas fielmente. "
            "MINIMALISMO: No añadir funcionalidad no solicitada ni compatibilidad retroactiva a menos que se pida. "
            "Sintaxis de herramientas: {{ tool: nombre | kwarg: val }}. "
            "IMPORTANTE: Nunca repitas estas reglas ni tu identidad en el output."
        )
        mode = self.sm.mode
        if mode == "Omni-Audit":
            base += (
                "\nMODO: Omni-Audit (V8.0 Premium). "
                "CRÍTICO: Análisis de arquitectura zero-trust. Alta precisión matemática. "
                "Detecta race conditions, memory leaks y fallos de lógica con 99% de precisión. "
                "Provee razonamiento técnico detallado para cada cambio propuesto. "
                "NO intentes llamar herramientas externas para este análisis; usa solo tu razonamiento interno."
            )
        try:
            # Si kb_data fue provisto (desde startup_check), usarlo directamente
            # Si no, cargar desde disco (ej: cuando se recarga tras !aprende)
            if kb_data is None and os.path.exists(KNOWLEDGE_FILE):
                kb_data, w = guardian.load_knowledge(KNOWLEDGE_FILE)
                bad = [x for x in w if any(k in x.lower() for k in ("corrupto", "inválido", "eliminad", "backup"))]
                if bad:
                    for warn in bad:
                        console.print(f"[yellow]⚠ Guardian: {warn}[/]")
            if kb_data:
                lines = kb_data.get("persistent_rules", [])
                if lines:
                    base += "\n\nCONOCIMIENTO CRÍTICO:\n" + "\n".join(lines)
        except Exception:
            pass
        return base




    def banner(self, clear=True):
        if clear:
            console.clear()
        f = pyfiglet.Figlet(font="slant")
        title = f.renderText("GRAVITY AI").rstrip()

        auto_p, auto_m = provider_manager.get_best()
        locked = self.sm.data.get("model_locked", False)
        hw = hardware_profiler.get_full_profile()
        cs = CacheEngine.stats()

        if locked and self.sm.data.get("locked_model"):
            curr_prov = self.sm.data.get("locked_provider", "locked")
            curr_mod  = self.sm.data.get("locked_model")
        else:
            curr_prov = auto_p.name if auto_p else "None"
            curr_mod  = auto_m if auto_m else "None"

        c = CostTracker.get_daily_cost()
        t_tokens = sum(len(m.get("content",""))//4 for m in self.history)

        max_ctx = self.sm.data.get("advanced_params", {}).get("num_ctx")
        if not max_ctx:
            max_ctx = auto_p.max_context if auto_p else 128000

        logo = f"""[bold bright_white]{title}[/]
[bold cyan]v{APP_VERSION} ⸺ Omni-Tier Architecture[/]
[dim]Orquestación Local & Cloud activa[/]
[dim]Historial: {t_tokens:,} / {max_ctx:,} tokens[/]"""

        stats = f"""[green]✓ Sistema Online[/]
» Motor: [bold yellow]{curr_prov}[/]
» Modelo:  [bold bright_white]{curr_mod}[/]
» Estado:  [{"red" if locked else "green"}]{"FORZADO" if locked else "AUTO"}[/]
» Modo:   [cyan]{self.sm.mode.upper()}[/]
» Gasto:    [yellow]${c:.3f}[/]"""

        hw_panel = f"""[bold magenta]⚛ Telemetría[/]
» GPU:   [dim]{hw['gpu_name'][:18]}[/]
» VRAM:  [bold blue]{hw['vram_mb']:,} MB[/]
» RAM:   [dim]{hw['total_ram_mb']:,} MB[/]
» NPU:   [{"green" if hw['npu_name'] else "white"}]{hw['npu_name'][:18] if hw['npu_name'] else "Inactivo"}[/]
» Modo:  [dim]{hw['gpu_type'].upper()}[/]"""

        console.print(Panel(
            Columns([logo, stats, hw_panel], expand=True),
            border_style="cyan",
            box=box.DOUBLE
        ))


    def cmd_help(self):
        t = Table(show_header=True, box=box.SIMPLE, padding=(0,2))
        t.add_column("Comando", style="cyan", width=28)
        t.add_column("Descripción")

        t.add_row("/model",           "Picker interactivo para cambiar modelo/proveedor al vuelo.")
        t.add_row("/mode",            "Cambiar modo: production / development / Omni-Audit.")
        t.add_row("/providers",       "Estado y latencia de todos los motores locales y cloud.")
        t.add_row("/keys list|set|del", "Gestiona claves API de proveedores cloud (cifradas).")
        t.add_row("/rag <búsqueda>", "Busca en el índice de documentos local.")
        t.add_row("/search <búsqueda>", "Búsqueda web en vivo (inyecta contexto al prompt).")
        t.add_row("/index <ruta>", "Añade un archivo o carpeta al índice RAG local.")
        t.add_row("/clear", "Limpia el contexto actual de la conversación.")
        t.add_row("/cost", "Muestra desglose de costes por API/modelo de hoy.")
        t.add_row("/save [nombre]", "Guarda la sesión actual en disco.")
        t.add_row("/load <nombre>", "Carga una sesión guardada.")
        t.add_row("/sessions", "Lista todas las sesiones guardadas.")
        t.add_row("/branch <nombre>", "Crea un fork de la sesión actual.")
        t.add_row("/export", "Exporta la sesión actual a HTML.")
        t.add_row("/export md", "Exporta la sesión actual a Markdown.")
        t.add_row("/plan <tarea>", "Activa el modo planificación antes de codificar.")
        t.add_row("/verify <archivo>", "Audita un archivo con el Agente de Verificación.")
        t.add_row("/mcp <ruta>", "Conecta con un servidor MCP externo (stdio).")
        t.add_row("!aprende <texto>", "Persiste una regla en el knowledge base local.")
        t.add_row("/exit", "Sale del auditor guardando el historial de razonamiento.")
        console.print(Panel(t, title="[bold cyan]Comandos Disponibles — Gravity AI V8.0[/]", border_style="blue"))

    def cmd_providers(self):
        scans = provider_manager.scan_all()
        t = Table(title="Motores Detectados (Local + Cloud)", box=box.SIMPLE_HEAD)
        t.add_column("Proveedor", style="cyan")
        t.add_column("Categoría", style="magenta")
        t.add_column("Latencia", justify="right", style="yellow")
        t.add_column("Modelos", justify="right")
        t.add_column("Estado")

        for s in scans:
            st  = "[green]ONLINE[/]" if s.is_healthy else "[red]OFFLINE[/]"
            cat = getattr(s, "category", "local")
            lat = f"{s.response_ms}ms" if s.is_healthy else "-"
            t.add_row(s.name, cat.upper(), lat, str(len(s.models)), st)
        console.print(t)

    def cmd_keys(self, args: str):
        """Gestiona API keys via KeyManager."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0].lower() if parts else "list"

        if subcmd == "list":
            configured = KeyManager.list_configured()
            if not configured:
                console.print("[yellow]Sin claves API configuradas.[/]")
                return
            t = Table(title="Claves API Configuradas", box=box.SIMPLE_HEAD)
            t.add_column("Proveedor", style="cyan")
            t.add_column("Clave (enmascarada)", style="dim")
            for p in configured:
                t.add_row(p, KeyManager.mask(p))
            console.print(t)

        elif subcmd == "set":
            target = parts[1].strip().lower() if len(parts) > 1 else None
            if not target:
                # Mostrar proveedores conocidos
                all_known = KeyManager.list_all_known()
                t = Table(title="Proveedores Cloud Conocidos", box=box.SIMPLE_HEAD)
                t.add_column("#", justify="right", style="dim")
                t.add_column("ID", style="cyan")
                t.add_column("Nombre", style="white")
                t.add_column("Estado")
                for i, (pid, meta) in enumerate(all_known.items(), 1):
                    st = "[green]✓[/]" if meta["has_key"] else "[dim]—[/]"
                    t.add_row(str(i), pid, meta["display"], st)
                console.print(t)
                target = Prompt.ask("Proveedor (id exacto)").strip().lower()
            new_key = Prompt.ask(f"API Key para [cyan]{target}[/]", password=True)
            if new_key:
                KeyManager.set_key(target, new_key)
                console.print(f"[green]✓ Clave guardada para {target} (cifrada).[/]")
            else:
                console.print("[red]Operación cancelada.[/]")

        elif subcmd == "del":
            target = parts[1].strip().lower() if len(parts) > 1 else Prompt.ask("Proveedor a eliminar")
            if KeyManager.delete_key(target):
                console.print(f"[green]✓ Clave de {target} eliminada.[/]")
            else:
                console.print(f"[yellow]No había clave configurada para {target}.[/]")

        else:
            console.print("[red]Uso: /keys list | /keys set [proveedor] | /keys del <proveedor>[/]")

    def cmd_aprende(self, texto: str):
        """Persiste una regla en _knowledge.json bajo persistent_rules."""
        if not texto.strip():
            console.print("[red]Especifica el texto a aprender.[/]")
            return
        try:
            # Cargar con validación
            kb, w_load = guardian.load_knowledge(KNOWLEDGE_FILE)
            if w_load:
                bad = [x for x in w_load if "eliminad" in x.lower() or "backup" in x.lower()]
                for warn in bad:
                    console.print(f"[yellow]⚠ {warn}[/]")

            rules = kb.get("persistent_rules", [])
            entry = f"[{datetime.now().strftime('%Y-%m-%d')}] {texto.strip()}"

            # No permitir duplicados exactos
            stripped_new = entry.split('] ', 1)[-1].lower().strip()
            existing_stripped = [r.split('] ', 1)[-1].lower().strip() for r in rules]
            if stripped_new in existing_stripped:
                console.print(f"[yellow]Regla ya existe en el knowledge base (duplicado ignorado).[/]")
                return

            rules.append(entry)
            kb["persistent_rules"] = rules

            # Escritura atómica vía guardian
            ok, w_save = guardian.save_knowledge(KNOWLEDGE_FILE, kb)
            if ok:
                console.print(f"[green]✓ Regla persistida en _knowledge.json[/] [dim]({len(rules)} total)[/]")
            else:
                for w in w_save:
                    console.print(f"[red]Error: {w}[/]")
                return

            # Reload system prompt
            self.system_prompt = self._load_system_prompt()
            if self.history and self.history[0]["role"] == "system":
                self.history[0]["content"] = self.system_prompt
        except Exception as e:
            console.print(f"[red]Error escribiendo knowledge: {e}[/]")



    def cmd_verify(self, file_path: str):
        """Audita un archivo con el VerificationAgent."""
        path = file_path.strip().strip('"').strip("'")
        if not os.path.exists(path):
            # Intentar relativo al BASE_DIR
            path = os.path.join(BASE_DIR, path)
        if not os.path.exists(path):
            console.print(f"[red]Archivo no encontrado: {file_path}[/]")
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            result = self.verifier.audit_edit(path, content, content)
            score_color = "green" if result["score"] >= 80 else ("yellow" if result["score"] >= 50 else "red")
            console.print(f"\n[bold]Resultado de Verificación:[/] [{score_color}]Score {result['score']}/100[/]")
            if result["findings"]:
                for finding in result["findings"]:
                    lvl = finding["level"]
                    clr = "red" if lvl == "CRITICAL" else ("yellow" if lvl == "WARNING" else "dim")
                    console.print(f"  [{clr}][{lvl}][/] {finding['message']}")
            else:
                console.print("  [green]Sin hallazgos. Archivo limpio.[/]")
        except Exception as e:
            console.print(f"[red]Error en verificación: {e}[/]")

    def _mcp_session(self, server_path: str):
        """Inicia una sesión MCP real con MCPAdapter."""
        from core.mcp_adapter import MCPAdapter
        path = server_path.strip().strip('"').strip("'")
        if not os.path.exists(path):
            console.print(f"[red]Ruta no encontrada: {path}[/]")
            return
        adapter = MCPAdapter(path)
        console.print(f"[dim]Conectando con servidor MCP: {path}...[/]")
        if not adapter.connect():
            console.print("[red]No se pudo iniciar el proceso MCP.[/]")
            return
        tools_available = adapter.list_tools()
        if tools_available:
            console.print(f"[green]✓ Conectado. {len(tools_available)} herramientas disponibles:[/]")
            for tool in tools_available:
                console.print(f"  [cyan]{tool.get('name', '?')}[/] — {tool.get('description', '')}")
        else:
            console.print("[yellow]Conectado pero sin herramientas listadas.[/]")
        console.print("[dim]Sesión MCP activa. Escribe '/mcp-exit' para desconectar.[/]")
        try:
            while True:
                call = Prompt.ask("[bold magenta]MCP[/]")
                if call.strip() in ("/mcp-exit", "exit", "quit"):
                    break
                # Intentar parsear: tool_name arg1=val1 arg2=val2
                tokens = call.split()
                if not tokens:
                    continue
                tname = tokens[0]
                kwargs = {}
                for tok in tokens[1:]:
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        kwargs[k] = v
                resp = adapter.call_tool(tname, kwargs)
                console.print(Panel(json.dumps(resp, indent=2, ensure_ascii=False), title=f"[cyan]MCP: {tname}[/]"))
        except KeyboardInterrupt:
            pass
        adapter.disconnect()
        console.print("[dim]Sesión MCP cerrada.[/]")

    def process_command(self, user_input: str) -> bool:
        """Returns True si el comando fue interceptado y manejado, False para continuar como prompt."""
        parts = user_input.strip().split(None, 1)
        cmd   = parts[0].lower()
        args  = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("exit", "quit", "/exit", "/quit"):
            console.print("[yellow]Optimizando sesión antes de cerrar...[/]")
            saved = self.session.cleanup_reasoning()
            console.print(f"[green]✓ Purga completa. ({saved} tokens de razonamiento eliminados permanentemente).[/]")
            console.print("[dim]Desconectando puente...[/]")
            sys.exit(0)

        if cmd == "/help":
            self.cmd_help()
            return True

        if cmd == "/providers":
            self.cmd_providers()
            return True

        if cmd == "/clear":
            self.history.clear()
            self.history.append({"role": "system", "content": self.system_prompt})
            console.print("[green]✓ Historial borrado.[/]")
            return True

        if cmd == "/cost":
            console.print(Panel(CostTracker.summary_text(), title="[yellow]Consumo API[/]"))
            return True

        if cmd == "/branch":
            name = args or "fork"
            real = self.session.fork(name)
            console.print(f"[green]✓ Fork creado: {real}. (Sesión actual sigue intacta).[/]")
            return True

        if cmd == "/export":
            if args.strip().lower() == "md":
                path = self.session.export_markdown()
                console.print(f"[green]✓ Markdown exportado: {path}[/]")
            else:
                path = self.session.export_html()
                console.print(f"[green]✓ HTML exportado: {path}[/]")
            return True

        if cmd == "/save":
            name = args or datetime.now().strftime("session_%Y%m%d_%H%M%S")
            path = self.session.save(name)
            console.print(f"[green]✓ Sesión guardada: {path}[/]")
            return True

        if cmd == "/load":
            if not args:
                console.print("[red]Especifica el nombre de sesión. Usa /sessions para listar.[/]")
                return True
            if self.session.load(args):
                console.print(f"[green]✓ Sesión '{args}' cargada. ({len(self.history)} mensajes)[/]")
            else:
                console.print(f"[red]Sesión '{args}' no encontrada.[/]")
            return True

        if cmd == "/sessions":
            saves = self.session.list_saves()
            if not saves:
                console.print("[yellow]Sin sesiones guardadas.[/]")
                return True
            t = Table(title="Sesiones Guardadas", box=box.SIMPLE_HEAD)
            t.add_column("Nombre", style="cyan")
            t.add_column("Tamaño", justify="right")
            t.add_column("Modificado")
            for s in saves:
                t.add_row(s["name"], f"{s['size_kb']} KB", s["modified"])
            console.print(t)
            return True

        if cmd == "/keys":
            self.cmd_keys(args)
            return True

        if cmd == "!aprende":
            self.cmd_aprende(args)
            return True

        if cmd == "/verify":
            self.cmd_verify(args)
            return True

        if cmd == "/index":
            if not args:
                console.print("[red]Especifica ruta a archivo o carpeta.[/]")
                return True
            if not os.path.exists(args):
                console.print(f"[red]Ruta no existe: {args}[/]")
                return True
            num = RAGIndexer.index_file(args) if os.path.isfile(args) else RAGIndexer.index_folder(args)[1]
            console.print(f"[green]✓ Indexación completa. ({num} chunks añadidos)[/]")
            return True

        if cmd == "/rag":
            if not args:
                console.print("[red]Provee una búsqueda.[/]")
                return True
            res = RAGRetriever.retrieve(args)
            if not res:
                console.print("[yellow]0 resultados.[/]")
                return True
            for i, r in enumerate(res):
                console.print(f"\n[cyan]Fragmento {i+1} (similitud {r['similarity']:.2f}) - {r['source']}[/]")
                console.print(r["text"][:300] + "...")
            return True

        if cmd == "/model":
            self._picker_ui()
            self.banner()
            return True

        if cmd == "/plan":
            if not args:
                console.print("[red]Especifica la tarea para planificar.[/]")
                return True
            console.print(f"[bold yellow]Modo Planificación Activado:[/]\n[dim]Investigando dependencias y arquitectura para: {args}[/]")
            plan_inject = f"PLANNING MODE: Antes de codificar, investiga la tarea siguiente y provee un Plan de Implementación detallado. Luego espera confirmación para ejecutar: {args}"
            self.history.append({"role": "user", "content": plan_inject})
            # Continuar sin hacer return True para que se procese el historial
            return False

        if cmd == "/mode":
            modes = ["production", "development", "Omni-Audit"]
            t = Table(title="Modos disponibles", box=box.SIMPLE_HEAD)
            t.add_column("#", justify="right", style="dim", width=4)
            t.add_column("Modo", style="cyan")
            t.add_column("Descripción")
            descs = {
                "production": "Respuestas directas. Sin razonamiento extravagante. Para uso productivo.",
                "development": "Debug verbose. Traceback completo. Para desarrollo e integración.",
                "Omni-Audit": "Zero-trust. Análisis arquitectónico maximalista. Detección de bugs profunda."
            }
            for i, m in enumerate(modes):
                marker = "[green]● [/]" if m == self.sm.mode else "  "
                t.add_row(str(i), marker + m, descs.get(m, ""))
            console.print(t)
            sel = Prompt.ask("Selecciona modo", choices=["0","1","2"], default="0")
            new_mode = modes[int(sel)]
            self.sm.mode = new_mode
            self.system_prompt = self._load_system_prompt()
            if self.history and self.history[0]["role"] == "system":
                self.history[0]["content"] = self.system_prompt
            console.print(f"[green]✓ Modo cambiado a [bold]{new_mode}[/][/]")
            return True

        if cmd == "/mcp":

            if not args:
                console.print("[red]Uso: /mcp <ruta_al_servidor_mcp>[/]")
                return True
            self._mcp_session(args)
            return True

        if cmd == "/search":
            if not args: return True
            console.print("[dim]Buscando...[/]")
            succ, out = tools.execute_tool("web_search", query=args)
            console.print(Panel(out, title="Web Search", border_style="cyan"))
            self.history.append({"role": "user", "content": f"Contexto Web Inyectado:\n{out}"})
            return True

        return False

    def _picker_ui(self):
        """Picker interactivo para forzar proveedor/modelo."""
        scans = [s for s in provider_manager.scan_all() if s.is_healthy and s.models]
        if not scans:
            console.print("[red]No hay proveedores saludables disponibles.[/]")
            return

        console.print("[cyan]¿Qué motor deseas forzar?[/]")
        for i, s in enumerate(scans):
            console.print(f"  [{i}] {s.name} ({len(s.models)} modelos)")
        console.print("  [A] Automático (Ruteo Dinámico inteligente)")

        sel = Prompt.ask("Selección", default="A")
        if sel.lower() == 'a':
            self.sm.data["model_locked"] = False
            self.sm.save()
            console.print("[green]Modo Automático activado.[/]")
            time.sleep(1)
            return

        try:
            pidx = int(sel)
            prov = scans[pidx]
        except (ValueError, IndexError):
            return

        console.print(f"\n[cyan]Modelos en {prov.name}:[/]")
        for j, m in enumerate(prov.models):
            console.print(f"  [{j}] {m['name']}")

        sel2 = Prompt.ask("Selecciona modelo", default="0")
        try:
            midx = int(sel2)
            mod  = prov.models[midx]["name"]
        except (ValueError, IndexError):
            return

        self.sm.data["model_locked"] = True
        self.sm.data["locked_model"] = mod
        self.sm.data["locked_provider"] = prov.name
        self.sm.save()
        console.print(f"[green]✓ Todo ruteo forzado a {prov.name} → {mod}[/]")
        time.sleep(1)

    def _get_active_provider_and_model(self) -> tuple[str | None, str | None]:
        """Devuelve (provider_name, model_name) según estado locked/auto."""
        if self.sm.data.get("model_locked") and self.sm.data.get("locked_model"):
            return self.sm.data.get("locked_provider"), self.sm.data.get("locked_model")
        bp, bm = provider_manager.get_best()
        return (bp.name if bp else None), bm

    def interactive_loop(self):
        self.banner()
        while True:
            try:
                # Prompt con info del modelo activo
                tgt_p, tgt_m = self._get_active_provider_and_model()
                model_hint = f"[dim]{tgt_m[:25]}[/] " if tgt_m else ""
                user_msg = Prompt.ask(f"\n[bold cyan]Gravity[/] {model_hint}")

                if not user_msg.strip():
                    continue

                if self.process_command(user_msg):
                    continue

                self.history.append({"role": "user", "content": user_msg})

                tgt_p, tgt_m = self._get_active_provider_and_model()

                if not tgt_p:
                    console.print("[red]ERROR: Ningún motor de IA disponible. Inicia uno local o añade una Key con /keys set.[/]")
                    self.history.pop()
                    continue

                console.print(f"[dim]→ {tgt_p} / {tgt_m}[/]")

                # RAG context injection heuristic
                if "busca en" in user_msg.lower() or "del contexto" in user_msg.lower() or "en mi codigo" in user_msg.lower():
                    ctx = RAGRetriever.retrieve_as_context(user_msg)
                    if ctx:
                        console.print("[dim]Contexto RAG inyectado...[/]")
                        self.history[-1]["content"] = f"{ctx}\n\nConsulta: {user_msg}"

                opts = self.sm.data.get("advanced_params", {})
                full_resp = []
                stripper  = ReasoningStripper()
                ttft      = 0
                is_cache_hit = False

                # Cache check
                cached = CacheEngine.get(self.history, tgt_m)
                if cached:
                    console.print(f"\n[bold green]Auditor [dim](CACHE)[/]:[/]\n {cached}")
                    final_text   = cached
                    elapsed      = 0.001
                    is_cache_hit = True
                else:
                    console.print("\n[bold green]Auditor:[/]", end=" ")
                    t0 = time.time()
                    try:
                        for chunk in provider_manager.stream(self.history, tgt_m, tgt_p, opts):
                            if chunk:
                                if ttft == 0:
                                    ttft = round((time.time() - t0) * 1000)
                                clean_chunk = stripper.process_chunk(chunk)
                                if clean_chunk:
                                    print(clean_chunk, end="", flush=True)
                                full_resp.append(chunk)
                    except Exception as e:
                        import traceback
                        console.print(f"\n[red][Error de Provider][/] {e}")
                        console.print(f"[dim]{traceback.format_exc()}[/]")

                    elapsed    = time.time() - t0
                    final_text = "".join(full_resp)
                    CacheEngine.set(self.history, tgt_m, final_text, tgt_p)

                self.history.append({"role": "assistant", "content": final_text})
                print()

                # Auto Tool Execution
                t_runs = tools.parse_and_execute_all(final_text)
                for tname, succ, out in t_runs:
                    color = "green" if succ else "red"
                    console.print(Panel(out[:800] + ("..." if len(out) > 800 else ""), title=f"[{color}]Tool: {tname}[/]", border_style=color))
                    self.history.append({"role": "user", "content": f"Output de {tname}:\n{out[:2000]}"})

                # Métricas de sesión (footer compacto, sin redibujar banner)
                in_tok  = len(user_msg) // 4
                out_tok = len(final_text) // 4
                cost    = CostTracker.estimate(tgt_p, tgt_m, len(user_msg), len(final_text))
                CostTracker.record(tgt_p, tgt_m, in_tok, out_tok, cost)
                tps = out_tok / elapsed if elapsed > 0 else 0
                ttft_str = f"TTFT: {ttft}ms | " if not is_cache_hit else "CACHE | "
                console.print(f"[dim]({elapsed:.1f}s | {tps:.0f} tok/s | {ttft_str}${cost:.5f})[/]")

                # Sliding Window context management
                trimmed = self.session.trim_history(128000)
                if trimmed > 0:
                    console.print(f"[dim](Contexto optimizado: {trimmed} mensajes antiguos descartados.)[/]")

            except KeyboardInterrupt:
                console.print("\n[dim]Usa '/exit' para salir correctamente.[/]")
            except Exception as e:
                import traceback
                console.print(f"[red]Error fatal en loop:[/] {e}")
                console.print(f"[dim]{traceback.format_exc()}[/]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo pipe / ejecución directa
        prompt = " ".join(sys.argv[1:])
        # No mostrar first_run en modo pipe
        cli = AuditorCLI()
        bp, bm = provider_manager.get_best()
        if not bp:
            print("ERROR: Sin proveedor disponible. Usa /keys set o inicia un motor local.")
            sys.exit(1)
        cli.history.append({"role": "user", "content": prompt})
        resp = provider_manager.complete(cli.history, bm, bp.name, cli.sm.data.get("advanced_params", {}))
        print(resp)
        for tname, succ, out in tools.parse_and_execute_all(resp):
            if not succ:
                print(f"[Tool {tname} Error] {out}")
    else:
        first_run_check()
        cli = AuditorCLI()
        cli.interactive_loop()

