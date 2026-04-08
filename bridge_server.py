"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — BRIDGE SERVER V8.0 PRO                      ║
║     Enrutador Universal OpenAI-Compatible                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import time
import uuid
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import sys

# ── Windows UTF-8 Safety ──────────────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import provider_manager
from core.logger      import log
from core.audit_log   import audit_logger
from core.config_manager import config
from core.rate_limiter   import check_access
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data


class Console_Safe:
    def print(self, *args, **kwargs):
        try: print(*args)
        except Exception: pass

console = Console_Safe()

# ── Background provider scanner ───────────────────────────────────────────────
def background_scanner():
    while True:
        try: provider_manager.scan_all()
        except Exception: pass
        time.sleep(30)

# ── Reasoning Stripper ────────────────────────────────────────────────────────
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
        routes = {
            "/":             self._serve_dashboard,
            "/dashboard":    self._serve_dashboard,
            "/health":       self._serve_health,
            "/v1/models":    self._serve_models,
            "/v1/status":    self._serve_status,
            "/v1/audit":     self._serve_audit,
            "/metrics":      self._serve_metrics,
        }
        if self.path in routes:
            routes[self.path]()
        else:
            self.send_response(404)
            self.end_headers()

    # ── Dashboard SPA ─────────────────────────────────────────────────────────
    def _serve_dashboard(self):
        try:
            from dashboard import DASHBOARD_HTML
            body = DASHBOARD_HTML.encode("utf-8")
        except Exception:
            body = b"<h1>Gravity AI Bridge V8.0</h1><p>Ejecuta: python dashboard.py</p>"
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionAbortedError:
            pass

    # ── API endpoints GET ─────────────────────────────────────────────────────
    def _serve_health(self):
        scans = provider_manager.scan_all()
        body  = json.dumps({
            "status": "ok",
            "backends": [{"name": s.name, "healthy": s.is_healthy, "models": len(s.models)} for s in scans]
        }).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _serve_models(self):
        scans      = provider_manager.scan_all()
        all_models = [{"id": "gravity-bridge-auto", "object": "model", "owned_by": "Gravity AI"}]
        seen       = {"gravity-bridge-auto"}
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
            self._send_cors()
            self.end_headers()
            self.wfile.write(resp)
        except Exception:
            pass

    def _serve_status(self):
        best_p, best_m = provider_manager.get_best()
        scans  = provider_manager.scan_all()
        status = {
            "version":         "8.0",
            "bridge_online":   True,
            "active_provider": best_p.name if best_p else None,
            "active_model":    best_m,
            "backends": [
                {
                    "name":       s.name,
                    "category":   getattr(s, "category", "local"),
                    "healthy":    s.is_healthy,
                    "models":     len(s.models),
                    "latency_ms": getattr(s, "response_ms", 0),
                }
                for s in scans
            ],
        }
        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_audit(self):
        recent_logs = audit_logger.get_recent(100)
        body = json.dumps({"object": "list", "data": recent_logs}, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_metrics(self):
        data, content_type = get_metrics_data()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):

        # /v1/keys — guardar API key desde el Dashboard web
        if self.path == "/v1/keys":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length))
                prov   = data.get("provider", "").strip().lower()
                key    = data.get("key", "").strip()
                if prov and key:
                    from key_manager import KeyManager
                    KeyManager.set_key(prov, key)
                    body = json.dumps({"ok": True, "provider": prov}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(400)
                    self.end_headers()
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return

        if self.path not in ("/v1/chat/completions", "/v1/completions"):
            self.send_response(404)
            self.end_headers()
            return

        # Rate limiting
        ip         = self.client_address[0]
        auth_hdr   = self.headers.get("Authorization", "")
        api_key    = auth_hdr.split(" ")[-1] if " " in auth_hdr else auth_hdr
        allowed, reason = check_access(ip, api_key)
        if not allowed:
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": reason}).encode())
            record_error("rate_limit")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data      = self.rfile.read(content_length)
            payload        = json.loads(post_data.decode("utf-8"))
            messages       = payload.get("messages", [])
            req_model      = payload.get("model", "gravity-bridge-auto")
            is_streaming   = payload.get("stream", True)
            options        = {k: payload[k] for k in ("temperature", "top_p", "max_tokens", "stop") if k in payload}

            target_prov = None
            target_mod  = req_model
            if req_model == "gravity-bridge-auto":
                bp, bm = provider_manager.get_best()
                if bp:
                    target_prov, target_mod = bp.name, bm
            else:
                for r in provider_manager.scan_all():
                    if r.is_healthy and any(m["name"] == req_model for m in r.models):
                        target_prov = r.name
                        break

            if not target_prov:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"error":"No provider available."}')
                record_error("no_provider")
                return

            record_request(target_prov, target_mod)
            chat_id     = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            start_time  = time.time()
            input_chars = sum(len(m.get("content", "")) for m in messages)
            input_tokens = input_chars // 4
            record_tokens("input", target_prov, target_mod, input_tokens)
            stripper = ReasoningStripper()

            if is_streaming:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self._send_cors()
                self.end_headers()
                output_chars = 0
                for chunk_text in provider_manager.stream(messages, model=target_mod, provider=target_prov, options=options):
                    if not chunk_text:
                        continue
                    clean = stripper.process_chunk(chunk_text)
                    if not clean:
                        continue
                    output_chars += len(clean)
                    chunk = {
                        "id": chat_id, "object": "chat.completion.chunk", "model": target_mod,
                        "choices": [{"index": 0, "delta": {"content": clean}, "finish_reason": None}]
                    }
                    try:
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        break
                # Final [DONE]
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
                output_tokens = output_chars // 4
                record_tokens("output", target_prov, target_mod, output_tokens)
            else:
                raw_text     = provider_manager.complete(messages, model=target_mod, provider=target_prov, options=options)
                full_text    = stripper.process_chunk(raw_text)
                output_chars = len(full_text)
                output_tokens = output_chars // 4
                record_tokens("output", target_prov, target_mod, output_tokens)
                resp = {
                    "id": chat_id, "object": "chat.completion", "model": target_mod,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": full_text}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens, "total_tokens": input_tokens + output_tokens}
                }
                body = json.dumps(resp).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)

            elapsed = time.time() - start_time
            record_latency(target_prov, target_mod, elapsed)
            from cost_tracker import CostTracker
            plugin = provider_manager.get_plugin(target_prov)
            usd    = 0.0
            if plugin and getattr(plugin, "category", "") == "cloud":
                usd = CostTracker.estimate(target_prov, target_mod, input_chars, output_chars)
                CostTracker.record(target_prov, target_mod, input_tokens, output_tokens, usd)
            audit_logger.record(chat_id, target_prov, target_mod, input_tokens, output_tokens, usd, elapsed * 1000)

        except Exception as e:
            import traceback
            log.error(f"Error in POST: {e}", exc_info=True)
            record_error("internal_error")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error":"{str(e)}"}}\n'.encode())

    def log_message(self, fmt, *args):
        log.debug(fmt % args)


# ── Entry point ───────────────────────────────────────────────────────────────
def run_server():
    port = config.get("server.port", 7860)
    provider_manager.scan_all()
    threading.Thread(target=background_scanner, daemon=True).start()
    log.info(f"Gravity Bridge V8.0 — http://localhost:{port} | Dashboard: / | API: /v1")
    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run_server()
