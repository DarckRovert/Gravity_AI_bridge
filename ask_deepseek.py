"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V7.0 Omni-Tier        ║
║     CLI Frontend | RAG | Tools | Multi-model                 ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys
import json
import os
import time
from datetime import datetime

# UTF-8 enforcement (Windows)
if sys.stdout.encoding != "utf-8":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass
if sys.stdin and sys.stdin.encoding != "utf-8":
    import io
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    except Exception:
        pass

from rich.console  import Console
from rich.panel    import Panel
from rich.prompt   import Prompt
from rich.table    import Table
from rich          import box
import pyfiglet

# ── V7.0 Integrations ──────────────────────────────────────────────────────────
import provider_manager
from session_manager import SessionManager
from cost_tracker    import CostTracker
from tool_executor   import executor as tools
from rag.retriever   import RAGRetriever, RAGIndexer

try:
    import pyreadline3
except ImportError:
    pass

APP_VERSION    = "7.0 Omni-Tier"
BASE_DIR       = os.path.dirname(__file__)
SETTINGS_FILE  = os.path.join(BASE_DIR, "_settings.json")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")

console = Console()

class SettingsManager:
    def __init__(self):
        self.default_data = {
            "mode": "auditor",
            "agent_language": "en",
            "user_language": "es",
            "model_locked": False,
            "locked_model": "",
            "locked_provider": "",
            "advanced_params": {
                "num_ctx": 131072,
                "temperature": 0.6,
                "top_p": 0.9,
                "streaming": True,
            },
        }
        self.data = self._load()

    def _load(self):
        m = self.default_data.copy()
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                    for k,v in stored.items():
                        if isinstance(v, dict) and k in m:
                            m[k].update(v)
                        else:
                            m[k] = v
        except Exception:
            pass
        return m

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    @property
    def mode(self): return self.data.get("mode", "auditor")
    @mode.setter
    def mode(self, v): self.data["mode"] = v; self.save()


class AuditorCLI:
    def __init__(self):
        self.sm = SettingsManager()
        self.history = []
        self.session = SessionManager(self.history)
        self.system_prompt = self._load_system_prompt()
        self.history.append({"role": "system", "content": self.system_prompt})
        provider_manager.scan_all() # Initial sync

    def _load_system_prompt(self):
        base = (
            f"You are Gravity AI v{APP_VERSION}, an elite Senior Software Architect/Auditor. "
            "You prioritize secure, scalable, and Zero-Overhead code. "
            f"Communicate with the user strictly in {self.sm.data['user_language']} limit to cold, technical facts. "
            "You have access to tools. To use a tool, reply in the format: {{ tool: tool_name | kwarg: value }} "
        )
        try:
            if os.path.exists(KNOWLEDGE_FILE):
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    kb = json.load(f)
                    lines = kb.get("persistent_rules", [])
                    if lines:
                        base += "\n\nCRITICAL KNOWLEDGE:\n" + "\n".join(lines)
        except Exception:
            pass
        return base

    def banner(self):
        console.clear()
        f = pyfiglet.Figlet(font="slant")
        title = f.renderText("GRAVITY AI").rstrip()
        
        # Determine active provider
        auto_p, auto_m = provider_manager.get_best()
        locked = self.sm.data.get("model_locked", False)
        
        if locked and self.sm.data.get("locked_model"):
            curr_prov = self.sm.data.get("locked_provider", "locked")
            curr_mod  = self.sm.data.get("locked_model")
        else:
            curr_prov = auto_p.name if auto_p else "None"
            curr_mod  = auto_m if auto_m else "None"

        c = CostTracker.get_daily_cost()
        
        logo = f"""[bold bright_white]{title}[/]
[bold cyan]v{APP_VERSION} ⸺ Omni-Tier Architecture[/]
[dim]Local & Cloud orchestration active[/]"""
        
        stats = f"""[green]✓ System Online[/]
» Engine: [bold yellow]{curr_prov}[/]
» Model:  [bold bright_white]{curr_mod}[/]
» State:  [{"red" if locked else "green"}]{"LOCKED" if locked else "AUTO"}[/]
» Mode:   [cyan]{self.sm.mode.upper()}[/]
» Usg:    [yellow]${c:.3f}[/]"""

        from rich.columns import Columns
        console.print(Panel(
            Columns([logo, stats], expand=True), 
            border_style="cyan", 
            box=box.DOUBLE
        ))

    def cmd_help(self):
        t = Table(show_header=False, box=None, padding=(0,2))
        t.add_row("[cyan]/model[/]", "Despliega picker UI interactivo para cambiar modelo/provider al vuelo.")
        t.add_row("[cyan]/providers[/]", "Muestra estado y latencia de todos los motores locales y cloud.")
        t.add_row("[cyan]/rag <query>[/]", "Busca en el índice de documentos local.")
        t.add_row("[cyan]/search <query>[/]", "Búsqueda web en vivo (inyecta contexto al prompt).")
        t.add_row("[cyan]/index <ruta>[/]", "Añade un archivo o carpeta al índice RAG local.")
        t.add_row("[cyan]/clear[/]", "Limpia el contexto actual de la conversación.")
        t.add_row("[cyan]/cost[/]", "Muestra desglose de costes por API/modelo de hoy.")
        t.add_row("[cyan]/branch <name>[/]", "Crea un fork de la sesión actual.")
        t.add_row("[cyan]/export[/]", "Exporta la sesión actual a HTML.")
        t.add_row("[cyan]/exit[/]", "Sale del auditor.")
        console.print(Panel(t, title="Comandos Locales", border_style="blue"))

    def cmd_providers(self):
        scans = provider_manager.scan_all()
        t = Table(title="Motores Detectados (Local + Cloud)")
        t.add_column("Proveedor", style="cyan")
        t.add_column("Categoría", style="magenta")
        t.add_column("Latencia", justify="right", style="yellow")
        t.add_column("Modelos", justify="right")
        t.add_column("Estado")
        
        for s in scans:
            st = "[green]ONLINE[/]" if s.is_healthy else "[red]OFFLINE[/]"
            cat = getattr(s, "category", "local")
            lat = f"{s.response_ms}ms" if s.is_healthy else "-"
            t.add_row(s.name, cat.upper(), lat, str(len(s.models)), st)
        console.print(t)

    def process_command(self, user_input: str) -> bool:
        """Returns True if command intercepted and handled, False to continue as prompt."""
        cmd = user_input.split(" ")[0].lower()
        args = user_input[len(cmd):].strip()

        if cmd in ("exit", "quit", "/exit", "/quit"):
            console.print("[dim]Desconectando puente RTO...[/]")
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
            path = self.session.export_html()
            console.print(f"[green]✓ HTML exportado a: {path}[/]")
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
            
        if cmd == "/search":
            if not args: return True
            console.print("[dim]Buscando en DuckDuckGo/Brave...[/]")
            succ, out = tools.execute_tool("web_search", query=args)
            console.print(Panel(out, title="Web Search", border_style="cyan"))
            self.history.append({"role": "user", "content": f"System Injected Web Context:\n{out}"})
            return True

        return False

    def _picker_ui(self):
        """Simple inline picker to override models."""
        scans = [s for s in provider_manager.scan_all() if s.is_healthy and s.models]
        if not scans:
            console.print("[red]No hay proveedores saludables disponibles.[/]")
            return
            
        console.print("[cyan]¿Qué motor deseas forzar?[/]")
        for i, s in enumerate(scans):
            console.print(f"[{i}] {s.name} ({len(s.models)} modelos)")
        console.print("[A] Automático (Ruteo Dinámico inteligente)")
        
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
        except: return
        
        console.print(f"\n[cyan]Modelos en {prov.name}:[/]")
        for j, m in enumerate(prov.models):
            console.print(f"[{j}] {m['name']}")
        
        sel2 = Prompt.ask("Selecciona modelo", default="0")
        try:
            midx = int(sel2)
            mod  = prov.models[midx]["name"]
        except: return
        
        self.sm.data["model_locked"] = True
        self.sm.data["locked_model"] = mod
        self.sm.data["locked_provider"] = prov.name
        self.sm.save()
        console.print(f"[green]✓ Todo ruteo forzado a {prov.name} -> {mod}[/]")
        time.sleep(1)

    def interactive_loop(self):
        self.banner()
        while True:
            try:
                user_msg = Prompt.ask("\n[bold cyan]Gravity[/]")
                if not user_msg.strip():
                    continue
                    
                if self.process_command(user_msg):
                    continue
                    
                self.history.append({"role": "user", "content": user_msg})
                
                # Check locked vs auto
                if self.sm.data.get("model_locked") and self.sm.data.get("locked_model"):
                    tgt_p = self.sm.data.get("locked_provider")
                    tgt_m = self.sm.data.get("locked_model")
                else:
                    bp, tgt_m = provider_manager.get_best()
                    tgt_p = bp.name if bp else None
                
                if not tgt_p:
                    console.print("[red]ERROR: Ningún motor de IA disponible. Iniciar uno local o añadir Key.[/]")
                    self.history.pop()
                    continue

                console.print(f"[dim]Conectando con {tgt_p} ({tgt_m})...[/]")
                
                # RAG context injection heuristic
                if "busca en" in user_msg.lower() or "del contexto" in user_msg.lower() or "en mi codigo" in user_msg.lower():
                    ctx = RAGRetriever.retrieve_as_context(user_msg)
                    if ctx:
                        console.print("[dim]Contexto RAG inyectado localmente...[/]")
                        self.history[-1]["content"] = f"{ctx}\n\nUser Query: {user_msg}"
                
                opts = self.sm.data.get("advanced_params", {})
                full_resp = []
                
                console.print("\n[bold green]Auditor:[/]", end=" ", flush=True)
                
                t0 = time.time()
                try:
                    for chunk in provider_manager.stream(self.history, tgt_m, tgt_p, opts):
                        if chunk:
                            print(chunk, end="", flush=True)
                            full_resp.append(chunk)
                except Exception as e:
                    console.print(f"\n[red][Exception][/] {e}")
                
                elapsed = time.time() - t0
                final_text = "".join(full_resp)
                self.history.append({"role": "assistant", "content": final_text})
                
                print()  # newline
                
                # Auto Tool Execution check
                t_runs = tools.parse_and_execute_all(final_text)
                for tname, succ, out in t_runs:
                    color = "green" if succ else "red"
                    console.print(Panel(out[:800] + ("..." if len(out)>800 else ""), title=f"[{color}]Tool: {tname}[/]", border_style=color))
                    self.history.append({"role": "user", "content": f"System Output from {tname}:\n{out[:2000]}"})
                
                # Update metrics
                CostTracker.record(tgt_p, tgt_m, len(user_msg)//4, len(final_text)//4, CostTracker.estimate(tgt_p, tgt_m, len(user_msg), len(final_text)))
                tps = (len(final_text)//4) / elapsed if elapsed > 0 else 0
                console.print(f"[dim]({elapsed:.1f}s | {tps:.1f} tok/s | Cost: ${CostTracker.estimate(tgt_p, tgt_m, len(user_msg), len(final_text)):.4f})[/]")
                
            except KeyboardInterrupt:
                console.print("\n[dim]Usa '/exit' para salir.[/]")
            except Exception as e:
                console.print(f"[red]Fatal Error:[/] {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo pipe / ejecución directa (script injection)
        prompt = sys.argv[1]
        cli = AuditorCLI()
        bp, bm = provider_manager.get_best()
        if not bp: sys.exit(1)
        cli.history.append({"role": "user", "content": prompt})
        resp = provider_manager.complete(cli.history, bm, bp.name, cli.sm.data.get("advanced_params", {}))
        print(resp)
        # Parse tools inside pipe output
        for tname, succ, out in tools.parse_and_execute_all(resp):
            if not succ: print(f"[Tool {tname} Error] {out}")
    else:
        cli = AuditorCLI()
        cli.interactive_loop()
