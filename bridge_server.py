"""
╔══════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE SERVER (Proxy V4.0)    ║
║     Enrutador Universal OpenAI Compatible    ║
╚══════════════════════════════════════════════╝
"""

import json
import time
import socket
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import os

from rich.console import Console
from rich.table import Table
from rich import box

from provider_scanner import ProviderScanner

console = Console()

# Config global
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "_settings.json")
cached_scans = []
last_scan_time = 0
active_target_url = None
active_target_model = None

def get_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except:
        return {"bridge_port": 7860}

def background_scanner():
    global cached_scans, last_scan_time, active_target_url, active_target_model
    while True:
        try:
            scans = ProviderScanner.scan_all()
            cached_scans = scans
            last_scan_time = time.time()
            best_prov, best_mod = ProviderScanner.auto_select_best(scans)
            if best_prov:
                active_target_url = best_prov.url
                active_target_model = best_mod
        except Exception as e:
            print(f"[Scanner Error] {e}")
        time.sleep(30)

class GravityBridgeHandler(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        global cached_scans, active_target_model, active_target_url
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
            <html><body style="font-family:sans-serif; background:#0d1117; color:#c9d1d9; padding:40px;">
                <h1 style="color:#58a6ff;">Gravity AI Bridge Server V4.0 🚀</h1>
                <p>El proxy unificado está <strong>ONLINE</strong>.</p>
                <h3>Configuración de tu IDE:</h3>
                <pre style="background:#161b22; padding:15px; border-radius:6px;">
Base URL: http://localhost:{get_settings().get('bridge_port', 7860)}/v1
API Key:  gravity-local</pre>
                <h3>Backend Activo:</h3>
                <p>Enrutando hacia: <strong>{active_target_url}</strong> (Modelo: {active_target_model})</p>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            summary = [{"name": s.name, "healthy": s.is_healthy, "models": len(s.models)} for s in cached_scans]
            self.wfile.write(json.dumps({"status": "ok", "backends": summary}).encode('utf-8'))
            
        elif self.path == '/v1/models':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors()
            self.end_headers()
            
            all_models = []
            seen = set()
            # FAKE MODEL for auto-routing
            all_models.append({
                "id": "gravity-bridge-auto",
                "object": "model",
                "owned_by": "Gravity AI Ecosystem"
            })
            for s in cached_scans:
                if s.is_healthy:
                    for m in s.models:
                        if m["name"] not in seen:
                            seen.add(m["name"])
                            all_models.append({
                                "id": m["name"],
                                "object": "model",
                                "owned_by": s.name
                            })
                            
            resp = {"object": "list", "data": all_models}
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global cached_scans, active_target_model, active_target_url
        
        if self.path in ['/v1/chat/completions', '/v1/completions']:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                req_model = payload.get('model', 'gravity-bridge-auto')
                
                target_url = active_target_url
                target_model = active_target_model
                
                # Check if specific model was requested and find its provider
                if req_model != 'gravity-bridge-auto':
                    for s in cached_scans:
                        if s.is_healthy and any(m["name"] == req_model for m in s.models):
                            target_url = s.url
                            target_model = req_model
                            break
                            
                if not target_url:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b"No active AI providers available on your system.")
                    return
                    
                # Replace model name before proxying
                payload["model"] = target_model
                
                # BUG 4 FIX: Check if target protocol is Ollama to parse paths
                target_protocol = "openai"
                for s in cached_scans:
                    if s.url == target_url:
                        target_protocol = s.protocol
                        break
                        
                target_path = self.path
                if target_protocol == "ollama":
                    if self.path == '/v1/chat/completions':
                        target_path = '/api/chat'
                    elif self.path == '/v1/completions':
                        target_path = '/api/generate'

                proxy_data = json.dumps(payload).encode('utf-8')
                
                # Forward to actual provider
                req = urllib.request.Request(f"{target_url}{target_path}", data=proxy_data, headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
                
                start_time = time.time()
                try:
                    with urllib.request.urlopen(req) as response:
                        self.send_response(response.getcode())
                        for header_name, header_value in response.getheaders():
                            if header_name.lower() not in ['transfer-encoding', 'connection']:
                                self.send_header(header_name, header_value)
                        self.send_cors()
                        self.end_headers()
                        
                        # Relay the stream byte by byte to IDE
                        while True:
                            chunk = response.read(1024)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            self.wfile.flush()
                            
                    elapsed = time.time() - start_time
                    client_name = self.headers.get('User-Agent', 'Unknown-Client').split()[0]
                    print(f"[{time.strftime('%H:%M:%S')}] [{client_name}] {self.path} -> {target_model} ({elapsed:.1f}s)")
                    
                except urllib.error.HTTPError as e:
                    self.send_response(e.code)
                    self.end_headers()
                    self.wfile.write(e.read())
                    print(f"[Error Proxying] {e.code}")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(e).encode('utf-8'))
                    
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass # Override default logger to keep our clean console

def run_server():
    port = get_settings().get("bridge_port", 7860)
    
    try:
        global cached_scans, last_scan_time, active_target_url, active_target_model
        cached_scans = ProviderScanner.scan_all()
        last_scan_time = time.time()
        best_prov, best_mod = ProviderScanner.auto_select_best(cached_scans)
        if best_prov:
            active_target_url = best_prov.url
            active_target_model = best_mod
    except: pass
    
    # Iniciar scanner background
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    
    # Esperar primer escaneo (max 3s)
    print("Iniciando componentes del servidor...")
    time.sleep(2.5) 
    
    server = ThreadingHTTPServer(('0.0.0.0', port), GravityBridgeHandler)
    
    console.print(f"\n[bold cyan]┌────────────────────────────────────────────────────────┐[/]")
    console.print(f"[bold cyan]│[/]  [bold bright_white]GRAVITY BRIDGE SERVER V4.1 — ONLINE[/]                   [bold cyan]│[/]")
    console.print(f"[bold cyan]│[/]  ► Base URL: [green]http://localhost:{port}/v1[/]                  [bold cyan]│[/]")
    if active_target_url:
        target_display = f"{active_target_url} ({active_target_model})"
        # Padding to keep box aligned visually
        pad = " " * max(0, 43 - len(target_display))
        console.print(f"[bold cyan]│[/]  Activo: [yellow]{target_display}[/]{pad} [bold cyan]│[/]")
    else:
        console.print(f"[bold cyan]│[/]  [red]No se detectaron proveedores. Esperando...[/]            [bold cyan]│[/]")
    console.print(f"[bold cyan]│[/]                                                        [bold cyan]│[/]")
    console.print(f"[bold cyan]│[/]  [dim]Log de peticiones (en tiempo real):[/]                   [bold cyan]│[/]")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nApagando servidor...")
        server.server_close()

if __name__ == "__main__":
    run_server()
