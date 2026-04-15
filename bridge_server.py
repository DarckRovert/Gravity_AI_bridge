"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - BRIDGE SERVER V9.3.1 PRO [Diamond-Tier Edition]          ║
║                    Enrutador Universal OpenAI-Compatible                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import uuid
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import sys
import mimetypes
import glob

# ── Windows UTF-8 Safety ──────────────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from core import provider_manager
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
            "/v1/fooocus/status": self._serve_fooocus_status,
            "/v1/images":    self._serve_images,
            "/metrics":      self._serve_metrics,
        }
        if self.path in routes:
            routes[self.path]()
        elif self.path.startswith("/static/output/"):
            self._serve_static_output()
        else:
            self.send_response(404)
            self.end_headers()

    # ── Dashboard SPA ─────────────────────────────────────────────────────────
    def _serve_dashboard(self):
        # DASHBOARD_HTML ahora es bytes constante en dashboard.py — import directo
        try:
            from dashboard import DASHBOARD_HTML
            body = DASHBOARD_HTML
        except Exception:
            body = b"<h1>Gravity AI Bridge V9.3.1 PRO</h1><p>No se encontro web/dashboard.html. Restaura la carpeta web/.</p>"
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionAbortedError:
            pass

    def _serve_static_output(self):
        # Permite subdirectorios de fecha: /static/output/2026-04-13/filename.png
        raw = self.path[len("/static/output/"):]
        if not raw or ".." in raw:
            self.send_response(403)
            self.end_headers()
            return

        BASE = os.path.dirname(os.path.abspath(__file__))
        fooocus_out = os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs")

        filepath = None
        # 1. Intento ruta completa (con subcarpeta incluida en raw)
        candidate = os.path.join(fooocus_out, raw.replace("/", os.sep))
        if os.path.isfile(candidate):
            filepath = candidate
        else:
            # 2. Busqueda recursiva por basename (compatibilidad con URLs sin subcarpeta)
            basename = os.path.basename(raw)
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                matches = glob.glob(os.path.join(fooocus_out, "**", basename), recursive=True)
                if matches:
                    filepath = matches[0]
                    break

        if not filepath:
            self.send_response(404)
            self.end_headers()
            return

        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(500)
            self.end_headers()

    def _serve_images(self):
        """Sirve lista de imagenes generadas por Fooocus con URLs correctas incluyendo subcarpeta de fecha."""
        try:
            BASE = os.path.dirname(os.path.abspath(__file__))
            fooocus_out = os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs")
            files = []
            if os.path.isdir(fooocus_out):
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    files.extend(glob.glob(os.path.join(fooocus_out, "**", ext), recursive=True))

            # Ordenar por fecha de modificacion (mas nuevas primero)
            files.sort(key=os.path.getmtime, reverse=True)

            # Construir URLs con subcarpeta de fecha incluida para que _serve_static_output las encuentre
            img_urls = []
            for f in files[:50]:
                rel = os.path.relpath(f, fooocus_out).replace(os.sep, "/")
                img_urls.append(f"/static/output/{rel}")

            resp = {"images": img_urls, "count": len(img_urls)}
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            log.error(f"Error sirviendo imagenes: {e}")
            self.send_response(500)
            self.end_headers()

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
            "version":         "9.3.1 PRO",
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

    # ── Fooocus Motor Status ───────────────────────────────────────────────────
    def _serve_fooocus_status(self):
        """Health check real del motor Fooocus en puerto 7861."""
        import sys, os
        BASE = os.path.dirname(os.path.abspath(__file__))
        tools_dir = os.path.join(BASE, "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        try:
            from fooocus_client import health_check, OUTPUT_DIR
            status = health_check()
            # Contar imagenes generadas
            import glob
            imgs = []
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                imgs.extend(glob.glob(os.path.join(OUTPUT_DIR, "**", ext), recursive=True))
            status["images_generated"] = len(imgs)
            status["output_dir"] = OUTPUT_DIR
            status["port"] = 7861
        except Exception as e:
            status = {"online": False, "message": str(e), "port": 7861}
        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):

        # /v1/generate — Generar imagen via Fooocus desde API REST
        if self.path == "/v1/generate":
            try:
                BASE = os.path.dirname(os.path.abspath(__file__))
                tools_dir = os.path.join(BASE, "tools")
                if tools_dir not in sys.path:
                    sys.path.insert(0, tools_dir)
                from fooocus_client import generate_image, ImageGenRequest
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                req: ImageGenRequest = {
                    "prompt":          data.get("prompt", "a beautiful landscape"),
                    "negative_prompt": data.get("negative_prompt", ""),
                    "width":           int(data.get("width", 1024)),
                    "height":          int(data.get("height", 1024)),
                    "num_images":      int(data.get("num_images", 1)),
                    "performance":     data.get("performance", "Speed"),
                    "style_selections": data.get("style_selections", ["Fooocus V2"]),
                }
                result = generate_image(req)
                body = json.dumps(result).encode("utf-8")
                code = 200 if result.get("success") else 500
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
            return


        # /v1/keys — guardar API key desde el Dashboard web
        if self.path == "/v1/keys":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length))
                prov   = data.get("provider", "").strip().lower()
                key    = data.get("key", "").strip()
                if prov and key:
                    from core.key_manager import KeyManager
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

            # ── Auto-inyección de Personalidad (Knowledge Base) ──
            if not any(m.get("role") == "system" for m in messages):
                try:
                    from core import data_guardian
                    _base_dir = os.path.dirname(__file__)
                    kb_data, _ = data_guardian.load_knowledge(os.path.join(_base_dir, "_knowledge.json"))
                    _sys_prompt = (
                        "Eres Gravity AI V9.3.1 PRO, Auditor Senior. "
                        "PROTOCOLO: Lógica interna en inglés. Salida final en español estrictamente. "
                        "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa."
                    )
                    if kb_data and "persistent_rules" in kb_data and kb_data["persistent_rules"]:
                        _sys_prompt += "\n\nCONOCIMIENTO CRÍTICO:\n" + "\n".join(kb_data["persistent_rules"])
                    messages.insert(0, {"role": "system", "content": _sys_prompt})
                except Exception as e:
                    log.error(f"Error cargando personalidad para el bridge: {e}")

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
            from core.cost_tracker import CostTracker
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
    log.info(f"Gravity Bridge V9.3.1 PRO [Diamond-Tier Edition] — http://localhost:{port} | Dashboard: / | API: /v1")
    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run_server()
