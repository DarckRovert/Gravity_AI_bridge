"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — BRIDGE SERVER V7.1                          ║
║     Enrutador Universal OpenAI-Compatible                    ║
╚══════════════════════════════════════════════════════════════╝

Proxy universal:
Intercepta llamadas compatibles con OpenAI y las redirige al
ProviderManager (que maneja Ollama, LM Studio, OpenAI, Anthropic, Gemini, etc).
El texto devuelto se reempaqueta en formato OpenAI SSE para
que IDEs como Cursor, Aider, o Continue.dev funcionen con cualquier IA.
"""

import json
import time
import uuid
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import sys

# ── Windows UTF-8 Safety (V7.1) ──────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from rich.console import Console
import provider_manager

console = Console()
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "_settings.json")


def get_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"bridge_port": 7860}


# ── V7 Auto-Scanner ────────────────────────────────────────────────────────
def background_scanner():
    while True:
        try:
            # Refresh internal ProviderRegistry implicitly
            provider_manager.scan_all()
        except Exception:
            pass
        time.sleep(30)


# ── Reasoning Stripper ─────────────────────────────────────────────────────
class ReasoningStripper:
    """Silencia tokens inyectados por modelos con razonamiento como Gemma 4 o DeepSeek-R1 
    para no manchar el código en los IDEs como Cursor/Aider."""
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
                # Buscamos la etiqueta de inicio más cercana
                closest_start = -1
                for tag in self.start_tags:
                    pos = self.buffer.find(tag)
                    if pos != -1 and (closest_start == -1 or pos < closest_start):
                        closest_start = pos
                
                if closest_start != -1:
                    output += self.buffer[:closest_start]
                    self.buffer = self.buffer[closest_start:]  # Mover puntero al inicio del tag
                    # Evaluar cuál tag es (para limpiarlo completamente)
                    matched_tag = next((t for t in self.start_tags if self.buffer.startswith(t)), None)
                    if matched_tag:
                        self.buffer = self.buffer[len(matched_tag):]
                        self.in_reasoning = True
                else:
                    # Posible prefijo parcial de start_tag?
                    # Si termina en '<' o algo así, podríamos esperar, pero es stream muy fino.
                    if any(tag.startswith(self.buffer[-1:]) for tag in self.start_tags):
                        break # hold in buffer
                    output += self.buffer
                    self.buffer = ""
            else:
                # En razonamiento. Suprimir hasta el end_tag.
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
                    self.buffer = "" # descartar todo mientras se esté razonando
                    break # salir a esperar más chunks
        
        return output

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class GravityBridgeHandler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self._serve_dashboard()
        elif self.path == "/health":
            self._serve_health()
        elif self.path == "/v1/models":
            self._serve_models()
        elif self.path == "/v1/status":
            self._serve_status()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_dashboard(self):
        port = get_settings().get("bridge_port", 7860)
        best_p, best_m = provider_manager.get_best()
        target = f"{best_p.name} ({best_m})" if best_p else "—"

        scans = provider_manager.scan_all()
        
        html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8">
<title>Gravity AI Bridge V7.1 Omni-Tier</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;padding:40px;max-width:800px;margin:auto}}
  h1{{color:#58a6ff}}pre{{background:#161b22;padding:15px;border-radius:6px;color:#7ee787}}
  table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #30363d;padding:8px 12px;text-align:left}}
  th{{background:#161b22;color:#58a6ff}}.ok{{color:#3fb950}}.err{{color:#f85149}}.cloud{{color:#c471ed}}
</style></head>
<body>
<h1>Gravity AI Bridge V7.1 🌐</h1>
<p>Proxy Universal (Local + Cloud)</p>
<h3>Configuración en IDE (Cursor/Aider/Continue)</h3>
<pre>Base URL: http://localhost:{port}/v1
API Key:  gravity-local</pre>
<h3>Ruteo Activo</h3>
<p>Procesando peticiones vía → <strong>{target}</strong></p>
<h3>Motores Detectados (Local + Cloud)</h3>
<table><tr><th>Proveedor</th><th>Tipo</th><th>Estado</th><th>Modelos</th></tr>
{"".join(f'<tr><td>{s.name}</td><td class="{"cloud" if getattr(s,"category","")=="cloud" else "ok"}">{"☁ Cloud" if getattr(s,"category","")=="cloud" else "💻 Local"}</td><td class="{"ok" if s.is_healthy else "err"}">{"✅ ONLINE" if s.is_healthy else "🔴 Offline"}</td><td>{len(s.models)}</td></tr>' for s in scans)}
</table>
</body></html>"""
        body = html.encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type",   "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionAbortedError: pass

    def _serve_health(self):
        scans = provider_manager.scan_all()
        summary = [{"name": s.name, "healthy": s.is_healthy, "models": len(s.models)} for s in scans]
        body = json.dumps({"status": "ok", "backends": summary}).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError): pass

    def _serve_models(self):
        scans = provider_manager.scan_all()
        all_models = [{"id": "gravity-bridge-auto", "object": "model", "owned_by": "Gravity AI"}]
        seen = {"gravity-bridge-auto"}
        for s in scans:
            if s.is_healthy:
                for m in s.models:
                    if m["name"] not in seen:
                        seen.add(m["name"])
                        all_models.append({"id": m["name"], "object": "model", "owned_by": s.name})
        resp = json.dumps({"object": "list", "data": all_models}).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(resp)
        except (ConnectionAbortedError, BrokenPipeError): pass

    def _serve_status(self):
        best_p, best_m = provider_manager.get_best()
        scans = provider_manager.scan_all()
        status = {
            "version": "7.0",
            "bridge_online": True,
            "active_provider": best_p.name if best_p else None,
            "active_model": best_m,
            "backends": [
                {"name": s.name, "category": getattr(s,"category","local"), "healthy": s.is_healthy, "models": len(s.models)}
                for s in scans
            ]
        }
        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/v1/completions"):
            self.send_response(404)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            payload   = json.loads(post_data.decode("utf-8"))
            
            messages     = payload.get("messages", [])
            req_model    = payload.get("model", "gravity-bridge-auto")
            is_streaming = payload.get("stream", True)
            
            # OpenAI specific options
            options = {}
            for k in ("temperature", "top_p", "max_tokens", "stop"):
                if k in payload:
                    options[k] = payload[k]

            # Route model
            target_prov = None
            target_mod  = req_model
            if req_model == "gravity-bridge-auto":
                bp, bm = provider_manager.get_best()
                if bp:
                    target_prov = bp.name
                    target_mod  = bm
            else:
                # Find which provider owns this model
                for r in provider_manager.scan_all():
                    if r.is_healthy and any(m["name"] == req_model for m in r.models):
                        target_prov = r.name
                        break
            
            if not target_prov:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"error":"No active AI providers available."}')
                return

            chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            start_time = time.time()
            
            # Tracking cost input
            input_chars = sum(len(m.get("content","")) for m in messages)
            stripper = ReasoningStripper()

            if is_streaming:
                self.send_response(200)
                self.send_header("Content-Type",  "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection",    "keep-alive")
                self._send_cors()
                self.end_headers()
                
                output_chars = 0
                for chunk_text in provider_manager.stream(messages, model=target_mod, provider=target_prov, options=options):
                    if not chunk_text: continue
                    clean_chunk = stripper.process_chunk(chunk_text)
                    if not clean_chunk: continue
                    
                    output_chars += len(clean_chunk)
                    chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": target_mod,
                        "choices": [{"index": 0, "delta": {"content": clean_chunk}, "finish_reason": None}]
                    }
                    try:
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        break
                
                # Send terminal chunk
                final = {
                    "id": chat_id, "object": "chat.completion.chunk", "model": target_mod,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
                try:
                    self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except Exception:
                    pass
                
            else:
                raw_text = provider_manager.complete(messages, model=target_mod, provider=target_prov, options=options)
                full_text = stripper.process_chunk(raw_text)
                output_chars = len(full_text)
                resp = {
                    "id": chat_id,
                    "object": "chat.completion",
                    "model": target_mod,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": input_chars//4, "completion_tokens": output_chars//4, "total_tokens": (input_chars+output_chars)//4}
                }
                body = json.dumps(resp).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)

            elapsed = time.time() - start_time
            client_name = self.headers.get("User-Agent", "Unknown").split()[0]
            print(f"[{time.strftime('%H:%M:%S')}] [{target_prov}] [{client_name}] {target_mod} ({elapsed:.1f}s)")
            
            # Record cost
            from cost_tracker import CostTracker
            plugin = provider_manager.get_plugin(target_prov)
            if plugin and getattr(plugin, "category", "") == "cloud":
                usd = CostTracker.estimate(target_prov, target_mod, input_chars, output_chars)
                CostTracker.record(target_prov, target_mod, input_chars//4, output_chars//4, usd)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error":"{str(e)}"}}\n'.encode())

    def log_message(self, fmt, *args):
        pass  # Suppress internal python logging


def run_server():
    port = get_settings().get("bridge_port", 7860)

    # Initial scan
    provider_manager.scan_all()

    # Start background scanner
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()

    console.print(f"\n[bold cyan]┌──────────────────────────────────────────────────────────┐[/]")
    console.print(f"[bold cyan]│[/]  [bold bright_white]GRAVITY BRIDGE SERVER V7.0 Omni-Tier[/]                    [bold cyan]│[/]")
    console.print(f"[bold cyan]│[/]  ► Base URL: [green]http://localhost:{port}/v1[/]                    [bold cyan]│[/]")
    console.print(f"[bold cyan]│[/]  ► IDE Ready:[yellow] SSE Wrapper Universal Activo[/]              [bold cyan]│[/]")
    
    best_p, best_m = provider_manager.get_best()
    if best_p:
        icon = "☁ Cloud" if getattr(best_p,"category","") == "cloud" else "💻 Local"
        target_display = f"[{icon}] {best_p.name} ({best_m})"
        pad = " " * max(0, 55 - len(target_display))
        console.print(f"[bold cyan]│[/]  Ruteo Defecto: [magenta]{target_display}[/]{pad}[bold cyan]│[/]")
    else:
        console.print(f"[bold cyan]│[/]  [red]Sin detectados. Configura API Keys o inicia locales[/]    [bold cyan]│[/]")
    
    console.print(f"[bold cyan]└──────────────────────────────────────────────────────────┘[/]\n")

    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nApagando servidor proxy V7.0...")
        server.server_close()


if __name__ == "__main__":
    run_server()
