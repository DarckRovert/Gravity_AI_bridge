"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V4.0    ║
║     Modo God-Tier | Proxy Server Ready       ║
╚══════════════════════════════════════════════╝
"""
import sys
import json
import os
import urllib.request
import urllib.error
import time
import subprocess
from datetime import datetime

# Forzar codificación UTF-8 en Windows para evitar "idiomas extraños" o caracteres rotos
if sys.stdout.encoding != 'utf-8':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except: pass
if sys.stdin and sys.stdin.encoding != 'utf-8':
    import io
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    except: pass


from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.align import Align
from rich import box
import pyfiglet
import shutil

from provider_scanner import ProviderScanner

try:
    import pyreadline3
except ImportError:
    pass

# ─── Configuración base ──────────────────────────────────────────────────────
APP_VERSION = "4.2"
BASE_DIR = os.path.dirname(__file__)
HISTORY_FILE = os.path.join(BASE_DIR, "_history.json")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "_knowledge.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")
SAVES_DIR = os.path.join(BASE_DIR, "_saves")

if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

console = Console()

# ─── Gestor de Ajustes ───────────────────────────────────────────────────────
class SettingsManager:
    def __init__(self):
        self.default_data = {
            "provider": "ollama",
            "api_url": "http://localhost:11434",
            "last_model": "deepseek-r1:8b",
            "mode": "auditor",
            "agent_language": "en",
            "user_language": "es",
            "bridge_port": 7860,
            "advanced_params": {
                "num_ctx": 131072,
                "temperature": 0.6,
                "top_p": 0.9,
                "warning_threshold": 0.85,
                "streaming": True,
                "auto_compress": True
            }
        }
        self.data = self._load()

    def _load(self):
        merged = self.default_data.copy()
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                    if "advanced_params" in stored:
                        stored["advanced_params"] = {**self.default_data["advanced_params"], **stored["advanced_params"]}
                    merged = {**self.default_data, **stored}
            except Exception as e:
                console.print(f"[bold red]⚠ Alerta:[/] {e}. Cargando defaults.")
        return merged
        
    def heal(self):
        # Auto-heal: Ensure all fields are saved to disk manually
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except: pass
        
        return merged

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
            elif isinstance(primary_params.get(param_key), bool) or value.lower() in ("true", "false"):
                value = str(value).lower() == "true"
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
            except:
                shutil.copy2(path, path + ".bak")
                return default
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
    
    def compress(self, api_client, options, system_prompt):
        if len(self.history) < 6: return False
        
        console.print("[yellow]⏳ Comprimiendo contexto para liberar memoria...[/]")
        prompt = "Instrucción de Sistema: Escribe un resumen ultra-compacto pero extremadamente detallado de los conocimientos técnicos y de contexto de nuestra conversación actual. Usa bullet points."
        msg = [{"role": "system", "content": system_prompt}] + self.history + [{"role": "user", "content": prompt}]
        
        # Desactivamos streaming para la compresión silenciosa
        silent_opts = options.copy()
        silent_opts["streaming"] = False
        summary = api_client.chat(msg, options=silent_opts)
        
        self.history = [
            {"role": "user", "content": "[Sistema: Resumen del historial anterior generado por ti]"},
            {"role": "assistant", "content": summary}
        ]
        self._save(HISTORY_FILE, self.history)
        console.print("[bold green]✓ Historial comprimido.[/]")
        return True

    def save_snapshot(self, name):
        p = os.path.join(SAVES_DIR, f"{name}.json")
        self._save(p, self.history)
        
    def load_snapshot(self, name):
        p = os.path.join(SAVES_DIR, f"{name}.json")
        if os.path.exists(p):
            self.history = self._load(p, [])
            self._save(HISTORY_FILE, self.history)
            return True
        return False

    def list_snapshots(self):
        return [f.replace(".json", "") for f in os.listdir(SAVES_DIR) if f.endswith(".json")]

# ─── Clientes de IA ──────────────────────────────────────────────────────────
class AIClient:
    def __init__(self, model, api_url):
        self.model = model
        self.api_url = api_url.rstrip('/')

def safe_parse_json_line(line):
    try: return json.loads(line)
    except: return None

class OllamaClient(AIClient):
    def chat(self, messages, options=None):
        do_stream = options.get("streaming", True) if options else True
        payload_dict = {"model": self.model, "messages": messages, "stream": do_stream}
        if options:
            valid_keys = ['num_ctx', 'temperature', 'top_p', 'top_k', 'repeat_penalty', 'seed', 'num_predict']
            payload_dict["options"] = {k: v for k, v in options.items() if k in valid_keys}
        
        req = urllib.request.Request(f"{self.api_url}/api/chat", data=json.dumps(payload_dict).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            if not do_stream:
                with urllib.request.urlopen(req, timeout=600) as r: 
                    return json.loads(r.read().decode())["message"]["content"]
            else:
                full_content = ""
                with urllib.request.urlopen(req, timeout=600) as r:
                    for line in r:
                        if line:
                            data = safe_parse_json_line(line.decode('utf-8'))
                            if data and "message" in data:
                                chunk = data["message"].get("content", "")
                                full_content += chunk
                                sys.stdout.write(chunk); sys.stdout.flush()
                print()
                return full_content
        except Exception as e: raise ConnectionError(f"Ollama Error: {e}")

class OpenAIClient(AIClient):
    def chat(self, messages, options=None):
        do_stream = options.get("streaming", True) if options else True
        payload_dict = {"model": self.model, "messages": messages, "stream": do_stream}
        if options:
            if "temperature" in options: payload_dict["temperature"] = options["temperature"]
            
        req = urllib.request.Request(f"{self.api_url}/v1/chat/completions", data=json.dumps(payload_dict).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            if not do_stream:
                with urllib.request.urlopen(req, timeout=600) as r: 
                    res = json.loads(r.read().decode())
                    return res["choices"][0]["message"]["content"]
            else:
                full_content = ""
                with urllib.request.urlopen(req, timeout=600) as r:
                    for line in r:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data: ") and line_str != "data: [DONE]":
                            data = safe_parse_json_line(line_str[6:])
                            if data and "choices" in data and len(data["choices"]) > 0:
                                chunk = data["choices"][0].get("delta", {}).get("content", "")
                                full_content += chunk
                                sys.stdout.write(chunk); sys.stdout.flush()
                print()
                return full_content
        except Exception as e: raise ConnectionError(f"OpenAI/LM Studio Error: {e}")

# ─── Integracion movida a ide_integrator.py ────────────────────────────────

# ─── Interfaz del Auditor ────────────────────────────────────────────────────
class AuditorCLI:
    def __init__(self, as_agent=False):
        self.settings = SettingsManager()
        self.memory = MemoryManager()
        self.as_agent = as_agent
        self.provider = self.settings.data.get("provider", "ollama")
        base_url = self.settings.data.get("api_url", "http://localhost:11434")
        
        if self.provider in ["openai", "lm_studio", "lemonade"]: self.client = OpenAIClient(self.settings.current_model, base_url)
        else: self.client = OllamaClient(self.settings.current_model, base_url)
            
        if os.name == 'nt': os.system(f"title GRAVITY AI ^| {self.client.model} ^| {self.provider.upper()}")

    def _get_system_prompt(self):
        m = self.settings.data.get("mode", "auditor")
        rules = "\n".join(f"- {r}" for r in self.memory.knowledge) if self.memory.knowledge else "Ninguna"
        
        if self.as_agent: 
            return (f"Eres el Auditor Senior de Gravity AI. Tu misión es responder de forma DIRECTA, "
                    f"TÉCNICA y EXCLUSIVAMENTE en ESPAÑOL a la lógica del Agente Externo que te consulta.\n"
                    f"REGLAS:\n{rules}")
        
        if m == "coder": return f"Eres CTO Experto. Responde SÓLO con código optimizado. Nada de explicaciones largas.\nREGLAS:\n{rules}"
        if m == "creativo": return f"Eres un creativo visionario. Piensa out-of-the-box.\nREGLAS:\n{rules}"
        if m == "revisor": return f"Eres un revisor de PR estricto. Busca bugs, race conditions y vulnerabilidades.\nREGLAS:\n{rules}"
        
        return f"Eres el Auditor Senior de Gravity AI. Riguroso y experto. Responde en ESPAÑOL.\nREGLAS:\n{rules}"

    def show_info(self):
        t = Table(title=f"📊 Estado V{APP_VERSION} ({self.settings.data.get('mode', 'auditor').upper()})", box=box.ROUNDED)
        t.add_column("Aspecto", style="cyan"); t.add_column("Detalle", style="yellow")
        t.add_row("Proveedor", f"{self.provider.upper()} ({self.client.api_url})")
        t.add_row("Modelo Activo", self.client.model)
        t.add_row("Tokens Estimado", str(self.memory.get_estimated_tokens(self._get_system_prompt())))
        t.add_row("Server Bridge", f"localhost:{self.settings.data.get('bridge_port', 7860)}")
        console.print(t)

    def _draw_welcome_ui(self):
        from rich.align import Align
        try:
            f_logo = pyfiglet.figlet_format("GRAVITY AI", font="doom")
            console.print(Align.center(f"[bold bright_cyan]{f_logo}[/]"))
        except: console.print("[bold cyan]GRAVITY AI[/]")
            
        header = Panel(Text(f"AUDITOR SENIOR V{APP_VERSION} — GOD TIER", justify="center", style="bold bright_white"), style="on bright_black", box=box.HEAVY_EDGE)
        console.print(header)
        
        c = """[bold yellow]!info[/]         Estado.    [bold cyan]/leer <file>[/] Inyectar txt. 
[bold yellow]!modo <m>[/]     Personal.  [bold cyan]/leer-git[/]    Inyectar diff actual.
[bold yellow]!scan[/]         Red local. [bold cyan]/leer-url[/]    Inyectar página web.
[bold magenta]!guardar <n>[/]  Snapshot.  [bold magenta]!comprimir[/]   Liberar memoria RAM ctx.
[bold magenta]!saves[/]        Cargar.    [bold green]!integrar[/]    Conectar con VS Code/IDE.
"""
        console.print(Align.center(Panel(c, title="[bold bright_white]⚡ ARSENAL V4.2 ⚡[/]", border_style="bright_blue", padding=(0, 2))))

    def run_chat(self):
        self._draw_welcome_ui()

        while True:
            try:
                usage = self.memory.get_estimated_tokens(self._get_system_prompt())
                limit = self.settings.options.get('num_ctx', 2048)
                pct = usage/limit if limit > 0 else 0
                
                if pct > self.settings.options.get('warning_threshold', 0.85):
                    if self.settings.options.get("auto_compress", True): self.memory.compress(self.client, self.settings.options, self._get_system_prompt())
                    else: console.print(f"[bold red]⚠ ALERTA: Contexto crítico ({pct*100:.0f}%). Escribe !limpiar o !comprimir.[/]")

                inp = Prompt.ask("[bold green]>>[/]").strip()
                if not inp or inp.lower() in ('salir', 'exit', 'quit'): break
                
                # Comandos de Sistema
                if inp == '!info': self.show_info(); continue
                if inp == '!version': console.print(f"[bold cyan]Gravity AI Bridge V{APP_VERSION}[/]"); continue
                if inp.startswith('!integrar'): 
                    args = inp.split(' ')
                    tool = args[1] if len(args) > 1 else 'todo'
                    from ide_integrator import IDEIntegrator
                    IDEIntegrator.integrate(tool); continue
                if inp == '!scan':
                    with console.status("[cyan]Escaneando puertos locales..."):
                        for s in ProviderScanner.scan_all(): 
                            console.print(f"[{'X' if s.is_healthy else ' '}] {s.name} ({s.model_count} modelos)")
                    continue
                if inp.startswith('!modo '):
                    self.settings.save("mode", inp[6:])
                    console.print(f"[green]Modo '{inp[6:]}' activo.[/]"); continue
                if inp == '!streaming': 
                    cur = self.settings.options.get("streaming", True)
                    self.settings.update_param("streaming", not cur)
                    console.print(f"[green]Streaming: {'ON' if not cur else 'OFF'}[/]"); continue
                if inp.startswith('!usar '):
                    mod = inp[6:].strip()
                    self.settings.save("last_model", mod)
                    self.client.model = mod
                    console.print(f"[green]Completado. Usando {mod}[/]"); continue
                if inp == '!modelos':
                    from provider_scanner import ProviderScanner
                    scans = ProviderScanner.scan_all()
                    for s in scans:
                        if s.is_healthy:
                            console.print(f"[bold cyan]{s.name}[/]: " + ", ".join(m["name"] for m in s.models))
                    continue
                if inp.startswith('!aprende '):
                    regla = inp[9:].strip()
                    if self.memory.learn(regla):
                        console.print(f"[green]Regla aprendida y persistida.[/]")
                    else:
                        console.print("[yellow]Ya conocía esta regla.[/]")
                    continue
                if inp == '!exportar-md':
                    h = self.memory.history
                    c = "\n\n".join(f"**{'Usuario' if m['role']=='user' else 'Gravity AI'}**: \n{m['content']}" for m in h)
                    with open(f"export_{int(time.time())}.md", "w", encoding="utf-8") as f: f.write(c)
                    console.print("[green]Sesión exportada a archivo Markdown local.[/]"); continue
                if inp.startswith('!guardar '):
                    self.memory.save_snapshot(inp[9:]); console.print("[green]Snapshot guardado.[/]"); continue
                if inp.startswith('!cargar '):
                    if self.memory.load_snapshot(inp[8:]): console.print("[green]Snapshot restaurado.[/]")
                    else: console.print("[red]No existe.[/]"); continue
                if inp == '!saves': console.print(", ".join(self.memory.list_snapshots())); continue
                if inp == '!comprimir': self.memory.compress(self.client, self.settings.options, self._get_system_prompt()); continue
                if inp == '!limpiar': self.memory.clear(); console.print("[yellow]Chat purgado.[/]"); continue

                p = inp
                
                # Inyectores de contexto
                if inp == '/leer-git':
                    try:
                        diff = subprocess.check_output(["git", "diff", "HEAD"], stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
                        p = f"Analiza mis cambios recientes sin comitear:\n```diff\n{diff}\n```"
                        console.print("[blue]Git diff en memoria.[/]")
                    except: console.print("[red]No hay repositorio git aquí.[/]"); continue
                    
                elif inp.startswith('/leer-url '):
                    try:
                        html = urllib.request.urlopen(inp[10:], timeout=5).read().decode('utf-8', errors='ignore')
                        p = f"Analiza esta web ({inp[10:]}):\n```\n{html[:15000]}...\n```"
                        console.print("[blue]URL extraída (truncada por seguridad).[/]")
                    except: console.print("[red]Error bajando URL.[/]"); continue
                    
                elif inp.startswith('/leer '):
                    path = inp[6:].strip()
                    if os.path.exists(path):
                        for c in ['utf-8', 'latin-1']:
                            try: p = f"Examina ({path}):\n```\n{open(path, 'r', encoding=c).read()}\n```"; break
                            except: pass
                        console.print("[blue]Archivo en memoria.[/]")
                    else: console.print("[red]No existe.[/]"); continue
                    
                elif inp.startswith('/leer-carpeta '):
                    folder = inp[14:].strip()
                    if os.path.exists(folder):
                        console.print(f"[cyan]Escaneando carpeta {folder}...[/]")
                        valid_exts = {'.py', '.js', '.ts', '.json', '.md', '.txt', '.yaml', '.toml', '.rs', '.go', '.java', '.c', '.cpp', '.h'}
                        combined = ""
                        for root, _, files in os.walk(folder):
                            if '.git' in root or 'node_modules' in root or '.venv' in root: continue
                            for file in files:
                                if any(file.endswith(ext) for ext in valid_exts):
                                    fp = os.path.join(root, file)
                                    try: combined += f"\n--- Archivo: {fp} ---\n{open(fp, 'r', encoding='utf-8').read()}\n"
                                    except: pass
                        p = f"Analiza la estructura y código de este proyecto:\n{combined[:50000]}"
                        console.print(f"[blue]Proyecto completo inyectado (truncado a 50k chars máximos preventivos).[/]")
                    else: console.print("[red]Carpeta no existe.[/]"); continue


                # Petición a IA
                msg = [{"role": "system", "content": self._get_system_prompt()}] + self.memory.history + [{"role": "user", "content": p}]
                
                start_time = time.time()
                ans = ""
                console.print(Rule(style="cyan"))
                
                is_streaming = self.settings.options.get("streaming", True)
                if is_streaming:
                    console.print(f"[cyan]✨ {self.client.model}...[/]")
                    ans = self.client.chat(msg, options=self.settings.options)
                else:
                    with console.status(f"[cyan]✨ {self.client.model}...[/]", spinner="dots"):
                        ans = self.client.chat(msg, options=self.settings.options)
                    console.print(Markdown(ans))
                    
                elapsed = time.time() - start_time
                
                self.memory.add_turn(p, ans)
                bar = f"{self.provider.upper()} │ {self.client.model} │ {self.settings.data.get('mode', 'auditor')} │ {elapsed:.1f}s"
                console.print(Panel(Text(bar, justify="center", style="dim white"), border_style="dim white"))

            except Exception as e: console.print(f"\n[red]Error fatal:[/] {e}")

def main():
    # Detectamos si se ejecuta por pipe (ej: git diff | gravity "audita")
    if not sys.stdin.isatty():
        piped_data = sys.stdin.read()
        args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Analiza esto:"
        cli = AuditorCLI(as_agent=True)
        try:
            res = cli.client.chat([
                {"role":"system","content":cli._get_system_prompt()},
                {"role":"user","content":f"{args}\n\n```\n{piped_data}\n```"}
            ], options=cli.settings.options)
            
            # Limpiar rastro de razonamiento interno si existe para no ensuciar la terminal del usuario
            if "<think>" in res and "</think>" in res:
                res = res.split("</think>")[-1].strip()
            
            print(res)
        except Exception as e: print(f"ERROR: {e}")
        return

    # Si se pasan argumentos, modo agente (una respuesta y salir)
    if len(sys.argv) > 1:
        cli = AuditorCLI(as_agent=True)
        try:
            res = cli.client.chat([
                {"role":"system","content":cli._get_system_prompt()},
                {"role":"user","content":" ".join(sys.argv[1:])}
            ], options=cli.settings.options)
            
            if "<think>" in res and "</think>" in res:
                res = res.split("</think>")[-1].strip()
                
            print(res)
        except Exception as e: print(f"ERROR: {e}")
    else:
        AuditorCLI().run_chat()

if __name__ == "__main__":
    main()
