"""
â•”â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â•—
â•‘     GRAVITY AI â€” BRIDGE SERVER V8.0 PRO                          â•‘
â•‘     Enrutador Universal OpenAI-Compatible                    â•‘
â•šâ• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• 
"""

import json
import time
import uuid
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import sys

# â”€â”€ Windows UTF-8 Safety (V8.0) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import provider_manager
from core.logger import log
from core.audit_log import audit_logger
from core.config_manager import config
from core.rate_limiter import check_access
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data

class Console_Safe:
    def print(self, *args, **kwargs):
        try: print(*args)
        except Exception: pass

console = Console_Safe()

# â”€â”€ Scanner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def background_scanner():
    while True:
        try: provider_manager.scan_all()
        except Exception: pass
        time.sleep(30)

# â”€â”€ Reasoning Stripper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€ HTTP Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class GravityBridgeHandler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200); self._send_cors(); self.end_headers()

    def do_GET(self):
        routes = {
            "/": self._serve_dashboard,
            "/health": self._serve_health,
            "/v1/models": self._serve_models,
            "/v1/status": self._serve_status,
            "/v1/audit": self._serve_audit,
            "/metrics": self._serve_metrics
        }
        if self.path in routes: routes[self.path]()
        else: self.send_response(404); self.end_headers()

    def _serve_dashboard(self):
        port = config.get("server.port", 7860)
        best_p, best_m = provider_manager.get_best()
        target = f"{best_p.name} ({best_m})" if best_p else "---"
        scans = provider_manager.scan_all()
        
        # ── Dashboard WOW Aesthetic V8.0 ───────────────────────────────────────────
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gravity AI Bridge V8.0 - DarckRovert</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
  :root {{ --bg: #0b0e14; --card: #151921; --accent: #4f46e5; --accent-glow: rgba(79, 70, 229, 0.4); --text: #f1f5f9; --text-dim: #94a3b8; --border: #2d333b; --success: #22c55e; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; line-height: 1.6; }}
  .container {{ max-width: 1000px; margin: 60px auto; padding: 20px; }}
  
  /* Glassmorphism Header */
  header {{ background: rgba(21, 25, 33, 0.8); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 20px; padding: 30px; margin-bottom: 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
  .logo-block h1 {{ font-size: 24px; font-weight: 800; margin: 0; color: var(--text); letter-spacing: -1px; }}
  .logo-block p {{ color: var(--text-dim); margin: 5px 0 0; font-size: 14px; }}
  
  .status-badge {{ background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: var(--success); padding: 8px 16px; border-radius: 50px; font-weight: 600; font-size: 12px; display: flex; align-items: center; gap: 8px; }}
  .pulse {{ width: 10px; height: 10px; background: var(--success); border-radius: 50%; box-shadow: 0 0 10px var(--success); animation: pulse-animation 2s infinite; }}
  @keyframes pulse-animation {{ 0% {{ transform: scale(0.95); opacity: 0.7; }} 50% {{ transform: scale(1.1); opacity: 1; }} 100% {{ transform: scale(0.95); opacity: 0.7; }} }}

  /* Grid Stats */
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; transition: 0.3s; }}
  .stat-card:hover {{ border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow); transform: translateY(-3px); }}
  .stat-card h3 {{ font-size: 12px; text-transform: uppercase; color: var(--text-dim); margin-top: 0; margin-bottom: 20px; letter-spacing: 1px; }}
  .stat-card .value {{ font-size: 20px; font-weight: 600; color: #fff; }}
  .stat-card .url {{ font-family: monospace; font-size: 14px; background: #000; padding: 8px; border-radius: 8px; margin-top: 15px; color: #7ee787; }}

  /* Table UI */
  .table-container {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; background: rgba(255,255,255,0.02); color: var(--text-dim); text-transform: uppercase; font-size: 11px; padding: 15px 20px; letter-spacing: 1px; border-bottom: 1px solid var(--border); }}
  td {{ padding: 15px 20px; border-bottom: 1px solid var(--border); font-size: 14px; }}
  tr:last-child td {{ border: none; }}
  .badge-p {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}
  .badge-p.cloud {{ background: rgba(147, 51, 234, 0.1); color: #c084fc; border: 1px solid rgba(147, 51, 234, 0.2); }}
  .badge-p.local {{ background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); }}

  footer {{ text-align: center; margin-top: 60px; color: var(--text-dim); font-size: 12px; }}
  footer a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo-block">
      <h1>GRAVITY BRIDGE V8.0</h1>
      <p>By DarckRovert &bull; Production Tier</p>
    </div>
    <div class="status-badge"><div class="pulse"></div> ONLINE</div>
  </header>

  <div class="stats-grid">
    <div class="stat-card">
      <h3>Enrutamiento Activo</h3>
      <div class="value">{target}</div>
      <div class="url">Endpoint: http://localhost:{port}/v1</div>
    </div>
    <div class="stat-card">
      <h3>Seguridad y Métricas</h3>
      <div class="value">Rate Limiting Activo</div>
      <p style="font-size: 12px; color: var(--text-dim); margin-top: 15px;">Monitorización NPU/GPU habilitada en <a href="/metrics" style="color:var(--accent);">/metrics</a></p>
    </div>
  </div>

  <div class="table-container">
    <table>
      <thead><tr><th>Proveedor</th><th>Categoría</th><th>Estado</th><th>Modelos</th></tr></thead>
      <tbody>
      {"".join(f'<tr><td><strong>{s.name}</strong></td><td><span class="badge-p {"cloud" if getattr(s,"category","")=="cloud" else "local"}">{"CLOUD" if getattr(s,"category","")=="cloud" else "LOCAL"}</span></td><td><span style="color:{"var(--success)" if s.is_healthy else "#ef4444"}">{"● Habilitado" if s.is_healthy else "○ Desconectado"}</span></td><td>{len(s.models)}</td></tr>' for s in scans)}
      </tbody>
    </table>
  </div>

  <footer>
    &copy; 2026 Gravity AI Suite &bull; <a href="https://twitch.tv/darckrovert" target="_blank">Twitch Dev Stream</a> &bull; DarckRovert Systems
  </footer>
</div>
</body>
</html>"""
        body = html.encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionAbortedError: pass

    def _serve_health(self):
        scans = provider_manager.scan_all()
        body = json.dumps({"status": "ok", "backends": [{"name": s.name, "healthy": s.is_healthy, "models": len(s.models)} for s in scans]}).encode()
        try:
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        except: pass

    def _serve_models(self):
        scans = provider_manager.scan_all()
        all_models = [{"id": "gravity-bridge-auto", "object": "model", "owned_by": "Gravity AI"}]
        seen = {"gravity-bridge-auto"}
        for s in scans:
            if s.is_healthy:
                for m in s.models:
                    if m["name"] not in seen:
                        seen.add(m["name"]); all_models.append({"id": m["name"], "object": "model", "owned_by": s.name})
        resp = json.dumps({"object": "list", "data": all_models}).encode()
        try:
            self.send_response(200); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers(); self.wfile.write(resp)
        except: pass

    def _serve_status(self):
        best_p, best_m = provider_manager.get_best()
        scans = provider_manager.scan_all()
        status = {"version": "8.0", "bridge_online": True, "active_provider": best_p.name if best_p else None, "active_model": best_m,
            "backends": [{"name": s.name, "category": getattr(s,"category","local"), "healthy": s.is_healthy, "models": len(s.models)} for s in scans]}
        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers(); self.wfile.write(body)

    def _serve_audit(self):
        recent_logs = audit_logger.get_recent(100)
        body = json.dumps({"object": "list", "data": recent_logs}, indent=2).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers(); self.wfile.write(body)

    def _serve_metrics(self):
        data, content_type = get_metrics_data()
        self.send_response(200); self.send_header("Content-Type", content_type); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/v1/completions"):
            self.send_response(404); self.end_headers(); return

        ip = self.client_address[0]; auth_header = self.headers.get("Authorization", "")
        api_key = auth_header.split(" ")[-1] if " " in auth_header else auth_header
        allowed, reason = check_access(ip, api_key)
        if not allowed:
            self.send_response(429); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"error": reason}).encode()); record_error("rate_limit"); return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length); payload = json.loads(post_data.decode("utf-8"))
            messages = payload.get("messages", []); req_model = payload.get("model", "gravity-bridge-auto"); is_streaming = payload.get("stream", True)
            options = {k: payload[k] for k in ("temperature", "top_p", "max_tokens", "stop") if k in payload}

            target_prov = None; target_mod = req_model
            if req_model == "gravity-bridge-auto":
                bp, bm = provider_manager.get_best()
                if bp: target_prov, target_mod = bp.name, bm
            else:
                for r in provider_manager.scan_all():
                    if r.is_healthy and any(m["name"] == req_model for m in r.models):
                        target_prov = r.name; break
            
            if not target_prov:
                self.send_response(503); self.end_headers(); self.wfile.write(b'{"error":"No provider found."}'); record_error("no_provider"); return

            record_request(target_prov, target_mod)
            chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"; start_time = time.time()
            input_chars = sum(len(m.get("content","")) for m in messages); input_tokens = input_chars // 4
            record_tokens("input", target_prov, target_mod, input_tokens); stripper = ReasoningStripper()

            if is_streaming:
                self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self._send_cors(); self.end_headers()
                output_chars = 0
                for chunk_text in provider_manager.stream(messages, model=target_mod, provider=target_prov, options=options):
                    if not chunk_text: continue
                    clean_chunk = stripper.process_chunk(chunk_text)
                    if not clean_chunk: continue
                    output_chars += len(clean_chunk)
                    chunk = {"id": chat_id, "object": "chat.completion.chunk", "model": target_mod, "choices": [{"index": 0, "delta": {"content": clean_chunk}, "finish_reason": None}]}
                    try: self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8")); self.wfile.flush()
                    except: break
                
                final = {"id": chat_id, "object": "chat.completion.chunk", "model": target_mod, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
                try: self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8")); self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
                except: pass
                output_tokens = output_chars // 4; record_tokens("output", target_prov, target_mod, output_tokens)
            else:
                raw_text = provider_manager.complete(messages, model=target_mod, provider=target_prov, options=options)
                full_text = stripper.process_chunk(raw_text); output_chars = len(full_text); output_tokens = output_chars // 4
                record_tokens("output", target_prov, target_mod, output_tokens)
                resp = {"id": chat_id, "object": "chat.completion", "model": target_mod, "choices": [{"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens, "total_tokens": input_tokens + output_tokens}}
                body = json.dumps(resp).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self._send_cors(); self.end_headers(); self.wfile.write(body)

            elapsed = time.time() - start_time; record_latency(target_prov, target_mod, elapsed)
            from cost_tracker import CostTracker
            plugin = provider_manager.get_plugin(target_prov); usd = 0.0
            if plugin and getattr(plugin, "category", "") == "cloud":
                usd = CostTracker.estimate(target_prov, target_mod, input_chars, output_chars)
                CostTracker.record(target_prov, target_mod, input_tokens, output_tokens, usd)
            audit_logger.record(chat_id, target_prov, target_mod, input_tokens, output_tokens, usd, elapsed * 1000)

        except Exception as e:
            log.error(f"Error in POST: {str(e)}", exc_info=True); record_error("internal_error")
            self.send_response(500); self.end_headers(); self.wfile.write(f'{{"error":"{str(e)}"}}\n'.encode())

    def log_message(self, fmt, *args): log.debug(fmt % args)

def run_server():
    port = config.get("server.port", 7860); provider_manager.scan_all()
    threading.Thread(target=background_scanner, daemon=True).start()
    log.info(f"Gravity Bridge V8.0 \u2014 http://localhost:{port}/v1 | Metrics: /metrics")
    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

if __name__ == "__main__": run_server()
