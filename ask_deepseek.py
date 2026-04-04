"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE — AUDITOR SENIOR V5.1    ║
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
APP_VERSION = "5.1"
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
                with urllib.request.urlopen(req, timeout=1800) as r: 
                    return json.loads(r.read().decode())["message"]["content"]
            else:
                full_content = ""
                is_thinking = False
                with urllib.request.urlopen(req, timeout=1800) as r:
                    for line in r:
                        if line:
                            data = safe_parse_json_line(line.decode('utf-8'))
                            if data and "message" in data:
                                chunk = data["message"].get("content", "")
                                full_content += chunk
                                
                                # Detección de bloques de razonamiento (DeepSeek-R1)
                                if "<think>" in chunk:
                                    is_thinking = True
                                    sys.stdout.write("\033[2m") # Dim
                                if is_thinking:
                                    sys.stdout.write(chunk)
                                    if "</think>" in chunk:
                                        is_thinking = False
                                        sys.stdout.write("\033[0m") # Reset
                                else:
                                    sys.stdout.write(chunk)
                                sys.stdout.flush()
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
                with urllib.request.urlopen(req, timeout=1800) as r: 
                    res = json.loads(r.read().decode())
                    return res["choices"][0]["message"]["content"]
            else:
                full_content = ""
                is_thinking = False
                with urllib.request.urlopen(req, timeout=1800) as r:
                    for line in r:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data: ") and line_str != "data: [DONE]":
                            data = safe_parse_json_line(line_str[6:])
                            if data and "choices" in data and len(data["choices"]) > 0:
                                chunk = data["choices"][0].get("delta", {}).get("content", "")
                                if not chunk: continue
                                full_content += chunk
                                
                                if "<think>" in chunk:
                                    is_thinking = True
                                    sys.stdout.write("\033[2m")
                                if is_thinking:
                                    sys.stdout.write(chunk)
                                    if "</think>" in chunk:
                                        is_thinking = False
                                        sys.stdout.write("\033[0m")
                                else:
                                    sys.stdout.write(chunk)
                                sys.stdout.flush()
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
        
        # Inicializar Watchdog de auto-switch ANTES de crear el cliente
        import engine_watchdog
        engine_watchdog.start(interval_seconds=30, verbose=not as_agent)
        
        # Usar el estado del watchdog si ya tiene datos, si no, caer al settings.json
        watchdog_state = engine_watchdog.get_active_state()
        if watchdog_state["provider"]:
            self.provider = watchdog_state["protocol"]
            base_url = watchdog_state["url"]
            detected_model = watchdog_state["model"]
        else:
            self.provider = self.settings.data.get("provider", "ollama")
            base_url = self.settings.data.get("api_url", "http://localhost:11434")
            detected_model = self.settings.current_model
        
        if self.provider in ["openai", "lm_studio", "lemonade"]:
            self.client = OpenAIClient(detected_model, base_url)
        else:
            self.client = OllamaClient(detected_model, base_url)
        
        # Registrar callback para que cuando el Watchdog detecte un cambio,
        # el cliente del Auditor se actualice silenciosamente en tiempo real
        def _on_switch(new_prov, new_model):
            if new_prov.protocol in ["openai", "lm_studio", "lemonade"]:
                self.client = OpenAIClient(new_model, new_prov.url)
            else:
                self.client = OllamaClient(new_model, new_prov.url)
            self.provider = new_prov.protocol
            if os.name == 'nt':
                os.system(f"title GRAVITY AI ^| {new_model} ^| {new_prov.name.upper()} [AUTO-SWITCH]")
        
        engine_watchdog.on_provider_switch(_on_switch)
            
        if os.name == 'nt': os.system(f"title GRAVITY AI ^| {self.client.model} ^| {watchdog_state.get('provider', self.provider).upper()}")


    def _get_system_prompt(self):
        m = self.settings.data.get("mode", "auditor")
        rules = "\n".join(f"- {r}" for r in self.memory.knowledge) if self.memory.knowledge else "Ninguna"
        
        if self.as_agent: 
            return (f"You are the Gravity AI Senior Auditor. Your mission is to respond DIRECTLY, "
                    f"TECHNICALLY and EXCLUSIVELY in TECHNICAL ENGLISH to the external AI Agent logic.\n"
                    f"RULES:\n{rules}")
        
        if m == "coder": return f"Eres CTO Experto. Responde SÓLO con código optimizado. Nada de explicaciones largas.\nREGLAS:\n{rules}"
        if m == "creativo": return f"Eres un creativo visionario. Piensa out-of-the-box.\nREGLAS:\n{rules}"
        if m == "revisor": return f"Eres un revisor de PR estricto. Busca bugs, race conditions y vulnerabilidades.\nREGLAS:\n{rules}"
        
        return f"Eres el Auditor Senior de Gravity AI. Riguroso y experto. Responde en ESPAÑOL.\nREGLAS:\n{rules}"

    def show_info(self):
        import engine_watchdog
        from turbo_kv import describe as kv_describe
        state = engine_watchdog.get_active_state()
        hw = state.get("hardware", {})
        opts = state.get("api_opts", {})

        t = Table(
            title=f"📊 Gravity AI V{APP_VERSION} — Status God Emperor",
            box=box.ROUNDED, border_style="bright_blue"
        )
        t.add_column("Sistema", style="bold cyan", min_width=20)
        t.add_column("Detalle", style="yellow")

        # Engine
        t.add_row("Motor Activo", f"{state.get('provider') or self.provider} ({self.client.api_url})")
        t.add_row("Modelo", self.client.model)
        t.add_row("Protocolo", (state.get("protocol") or self.provider).upper())
        t.add_row("Contexto Activo", f"{opts.get('num_ctx', self.settings.options.get('num_ctx', '?')):,} tokens")
        t.add_row("Tokens Usados", str(self.memory.get_estimated_tokens(self._get_system_prompt())))
        t.add_row("Bridge Server", f"localhost:{self.settings.data.get('bridge_port', 7860)}")
        t.add_row(Rule(style="dim"), "")

        # Hardware
        if hw:
            t.add_row("GPU", hw.get("gpu_name", "Unknown"))
            vram_mb = hw.get("vram_mb", 0)
            t.add_row("VRAM", f"{vram_mb:,} MB ({vram_mb/1024:.1f} GB) | {'iGPU Shared' if hw.get('is_igpu') else 'dGPU Dedicated'}")
            t.add_row("RAM Total", f"{hw.get('total_ram_mb', 0):,} MB ({hw.get('total_ram_mb',0)//1024} GB)")
            t.add_row("Backend GPU", hw.get("gpu_type", "cpu").upper())
            if hw.get("gfx_version"):
                t.add_row("ROCm GFX", hw["gfx_version"])
        else:
            t.add_row("Hardware", "[dim]Ejecuta !scan para detectar[/dim]")

        t.add_row(Rule(style="dim"), "")
        # KV Optimization
        t.add_row("KV-Cache (TurboQuant)", kv_describe(state.get("protocol", "ollama")))
        t.add_row("Modo", self.settings.data.get("mode", "auditor").upper())
        console.print(t)


    def _draw_welcome_ui(self):
        from rich.align import Align
        try:
            f_logo = pyfiglet.figlet_format("GRAVITY AI", font="doom")
            console.print(Align.center(f"[bold bright_cyan]{f_logo}[/]"))
        except: console.print("[bold cyan]GRAVITY AI[/]")
            
    def handle_input(self, inp):
        """Procesa una entrada (pregunta o comando) y retorna True si debe continuar el chat."""
        if not inp: return True
        if inp.lower() in ('salir', 'exit', 'quit'): return False
        
        # Comandos de Sistema
        if inp == '!info': self.show_info(); return True
        if inp == '!version': console.print(f"[bold cyan]Gravity AI Bridge V{APP_VERSION}[/]"); return True
        if inp.startswith('!integrar'): 
            args = inp.split(' ')
            tool = args[1] if len(args) > 1 else 'todo'
            from ide_integrator import IDEIntegrator
            IDEIntegrator.integrate(tool); return True
        if inp == '!scan':
            with console.status("[cyan]Escaneando puertos locales..."):
                for s in ProviderScanner.scan_all(): 
                    console.print(f"[{'X' if s.is_healthy else ' '}] {s.name} ({s.model_count} modelos)")
            return True
        if inp.startswith('!modo '):
            self.settings.save("mode", inp[6:])
            console.print(f"[green]Modo '{inp[6:]}' activo.[/]"); return True
        if inp == '!streaming': 
            cur = self.settings.options.get("streaming", True)
            self.settings.update_param("streaming", not cur)
            console.print(f"[green]Streaming: {'ON' if not cur else 'OFF'}[/]"); return True
        if inp.startswith('!usar '):
            mod = inp[6:].strip()
            self.settings.save("last_model", mod)
            self.client.model = mod
            console.print(f"[green]Completado. Usando {mod}[/]"); return True
        if inp == '!modelos':
            from provider_scanner import ProviderScanner
            scans = ProviderScanner.scan_all()
            for s in scans:
                if s.is_healthy:
                    console.print(f"[bold cyan]{s.name}[/]: " + ", ".join(m["name"] for m in s.models))
            return True
        if inp.startswith('!aprende '):
            regla = inp[9:].strip()
            if self.memory.learn(regla):
                console.print(f"[green]Regla aprendida y persistida.[/]")
            else:
                console.print("[yellow]Ya conocía esta regla.[/]")
            return True
        if inp == '!exportar-md':
            h = self.memory.history
            c = "\n\n".join(f"**{'Usuario' if m['role']=='user' else 'Gravity AI'}**: \n{m['content']}" for m in h)
            with open(f"export_{int(time.time())}.md", "w", encoding="utf-8") as f: f.write(c)
            console.print("[green]Sesión exportada a archivo Markdown local.[/]"); return True
        if inp.startswith('!guardar '):
            self.memory.save_snapshot(inp[9:]); console.print("[green]Snapshot guardado.[/]"); return True
        if inp.startswith('!cargar '):
            if self.memory.load_snapshot(inp[8:]): console.print("[green]Snapshot restaurado.[/]")
            else: console.print("[red]No existe.[/]"); return True
        if inp == '!saves': console.print(", ".join(self.memory.list_snapshots())); return True
        if inp.startswith('!selector '):
            # Show which model would be selected for a given query without executing it
            test_query = inp[10:].strip()
            try:
                from model_selector import classify_task, find_best_model, describe_selection
                from provider_scanner import ProviderScanner
                scans = ProviderScanner.scan_all()
                all_models = []
                for s in scans:
                    if s.is_healthy:
                        all_models.extend(m["name"] for m in s.models)
                if not all_models:
                    all_models = [self.client.model]
                task = classify_task(test_query)
                best = find_best_model(task, all_models)
                task_labels = {"code": "Codigo/Auditoria", "reason": "Razonamiento Profundo", "any": "General (cualquiera)"}
                t = Table(title="Smart Model Selector — Preview", box=box.SIMPLE)
                t.add_column("Campo", style="cyan"); t.add_column("Valor", style="yellow")
                t.add_row("Query", test_query[:60])
                t.add_row("Tarea detectada", task_labels.get(task, task))
                t.add_row("Modelo elegido", best or "Ninguno disponible")
                t.add_row("Modelos disponibles", ", ".join(all_models[:5]))
                console.print(t)
            except Exception as e:
                console.print(f"[red]Error en selector: {e}[/]")
            return True

        if inp == '!comprimir': self.memory.compress(self.client, self.settings.options, self._get_system_prompt()); return True
        if inp == '!limpiar': self.memory.clear(); console.print("[yellow]Chat purgado.[/]"); return True

        p = inp
        
        # Inyectores de contexto
        if inp == '/leer-git':
            try:
                diff = subprocess.check_output(["git", "diff", "HEAD"], stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
                p = f"Analiza mis cambios recientes sin comitear:\n```diff\n{diff}\n```"
                console.print("[blue]Git diff en memoria.[/]")
            except: console.print("[red]No hay repositorio git aquí.[/]"); return True
            
        elif inp.startswith('/leer-url '):
            try:
                html = urllib.request.urlopen(inp[10:], timeout=5).read().decode('utf-8', errors='ignore')
                p = f"Analiza esta web ({inp[10:]}):\n```\n{html[:15000]}...\n```"
                console.print("[blue]URL extraída (truncada por seguridad).[/]")
            except: console.print("[red]Error bajando URL.[/]"); return True
            
        elif inp.startswith('/leer '):
            path = inp[6:].strip()
            if os.path.exists(path):
                for c in ['utf-8', 'latin-1']:
                    try: p = f"Examina ({path}):\n```\n{open(path, 'r', encoding=c).read()}\n```"; break
                    except: pass
                console.print("[blue]Archivo en memoria.[/]")
            else: console.print("[red]No existe.[/]"); return True
            
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
            else: console.print("[red]Carpeta no existe.[/]"); return True

        # ── Smart Model Selection ─────────────────────────────────────────────
        # Lee el caché del watchdog (0ms) en lugar de scan_all() (1-2s por query)
        try:
            import engine_watchdog
            import model_selector

            state = engine_watchdog.get_active_state()

            # Obtener modelos del caché (actualizado cada 30s por el watchdog en background)
            cached = model_selector._available_models_cache
            all_cached_models = []
            for model_list in cached.values():
                all_cached_models.extend(model_list)

            # Deduplicar manteniendo orden
            seen = set()
            available_model_names = []
            for m in all_cached_models:
                if m not in seen:
                    seen.add(m)
                    available_model_names.append(m)

            # Si el caché está vacío (primer arranque), usar el modelo actual
            if not available_model_names:
                available_model_names = [self.client.model]

            # Inicializar tracker si es el primer uso
            if model_selector.get_active_model() is None:
                model_selector.set_active_model(self.client.model)

            optimal_model, did_switch = model_selector.get_optimal_model(
                text=p,
                protocol=state.get("protocol") or self.provider,
                provider_name=state.get("provider") or self.provider,
                available_models=available_model_names,
                history=self.memory.history,
                verbose=not self.as_agent
            )

            # Aplicar el switch si el selector eligió un modelo diferente
            if did_switch and optimal_model:
                self.client.model = optimal_model
                if os.name == 'nt':
                    os.system(f"title GRAVITY AI ^| {optimal_model} ^| {self.provider.upper()} [SMART]")

        except Exception:
            pass  # Silencioso: nunca interrumpir el flujo por el selector


        # ── Petición a IA ─────────────────────────────────────────────────────
        msg = [{"role": "system", "content": self._get_system_prompt()}] + self.memory.history + [{"role": "user", "content": p}]

        start_time = time.time()
        console.print(Rule(style="cyan"))

        # Opciones optimizadas por hardware (ctx dinámico, etc.)
        try:
            import engine_watchdog
            live_opts = engine_watchdog.get_optimized_options(self.settings.options)
        except Exception:
            live_opts = self.settings.options

        is_streaming = live_opts.get("streaming", True)
        if is_streaming:
            console.print(f"[cyan]✨ {self.client.model} | ctx={live_opts.get('num_ctx','?'):,}...[/]")
            ans = self.client.chat(msg, options=live_opts)
        else:
            with console.status(f"[cyan]✨ {self.client.model}...[/]", spinner="dots"):
                ans = self.client.chat(msg, options=live_opts)
            console.print(Markdown(ans))

        elapsed = time.time() - start_time
        self.memory.add_turn(p, ans)

        if not self.as_agent:
            ctx_used = live_opts.get('num_ctx', '?')
            bar = f"{self.provider.upper()} │ {self.client.model} │ ctx={ctx_used:,} │ {elapsed:.1f}s"
            console.print(Panel(Text(bar, justify="center", style="dim white"), border_style="dim white"))

        return True


    def run_chat(self):
        self._draw_welcome_ui()
        while True:
            try:
                usage = self.memory.get_estimated_tokens(self._get_system_prompt())
                limit = self.settings.options.get('num_ctx', 2048)
                pct = usage/limit if limit > 0 else 0
                if pct > self.settings.options.get('warning_threshold', 0.85):
                    if self.settings.options.get("auto_compress", True): self.memory.compress(self.client, self.settings.options, self._get_system_prompt())
                
                inp = Prompt.ask("[bold green]>>[/]").strip()
                if not self.handle_input(inp): break
            except Exception as e: console.print(f"\n[red]Error fatal:[/] {e}")

def main():
    # Detectamos si se ejecuta por pipe (ej: git diff | gravity "audita")
    if not sys.stdin.isatty():
        try:
            piped_data = sys.stdin.read()
            args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Analiza esto:"
            cli = AuditorCLI(as_agent=True)
            query = f"{args}\n\n```\n{piped_data}\n```"
            cli.handle_input(query)
        except EOFError: pass
        return

    # Si se pasan argumentos, modo agente (una respuesta y salir)
    if len(sys.argv) > 1:
        cli = AuditorCLI(as_agent=True)
        inp = " ".join(sys.argv[1:])
        cli.handle_input(inp)
    else:
        AuditorCLI().run_chat()

if __name__ == "__main__":
    main()

