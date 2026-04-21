"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - BRIDGE SERVER V10.3 [Diamond-Tier Edition]             ║
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

# ── PyInstaller frozen-path fix ───────────────────────────────────────────────
# En modo frozen (exe compilado):
#   - sys.executable = D:\Gravity AI Bridge\GravityBridge.exe
#   - sys._MEIPASS   = C:\Users\xxx\AppData\Local\Temp\_MEIxxx\ (módulos Python)
#   - Los datos (web/, config.yaml, etc.) están en el directorio del exe (copiados por Inno Setup)
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(os.path.abspath(sys.executable))
    _MEIPASS = getattr(sys, "_MEIPASS", _BASE)
    # _MEIPASS: donde PyInstaller descomprime los módulos Python (.pyc)
    if _MEIPASS not in sys.path:
        sys.path.insert(0, _MEIPASS)
    # Directorio del exe: donde están los datos (config.yaml, web/, _knowledge.json)
    if _BASE not in sys.path:
        sys.path.insert(0, _BASE)
    os.chdir(_BASE)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

from core import provider_manager
from core.logger      import log
from core.audit_log   import audit_logger
from core.config_manager import config
from api.state import check_rate_limit, register_ip_hit, geoip_cache, recent_ips, geoip_lock, RATE_LIMIT_WINDOW
from core.rate_limiter   import check_access
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data
from core import security_monitor
from core import image_queue
from core import deploy_manager
from core import game_server_manager
from core import ai_process_manager
from core import engine_watchdog
from core import video_pipeline


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
        import time as _t; _t.sleep(30)


# ── HTTP Handler ──────────────────────────────────────────────────────────────
from api.routes.mixin_get import GetRoutesMixin
from api.routes.mixin_post import PostRoutesMixin

class GravityBridgeHandler(BaseHTTPRequestHandler, GetRoutesMixin, PostRoutesMixin):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass # Cliente desconectado abruptamente


    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _check_rate(self) -> bool:
        """Verifica el rate limit para la IP del cliente. Retorna False y envía 429 si bloqueada."""
        ip = self.client_address[0] if self.client_address else "unknown"
        if ip != "unknown":
            register_ip_hit(ip)
        if not check_rate_limit(ip):
            body = json.dumps({"error": "Too Many Requests", "retry_after": RATE_LIMIT_WINDOW}).encode()
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", str(RATE_LIMIT_WINDOW))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        routes = {
            "/":                    self._serve_dashboard,
            "/dashboard":           self._serve_dashboard,
            "/health":              self._serve_health,
            "/v1/models":           self._serve_models,
            "/v1/status":           self._serve_status,
            "/v1/audit":            self._serve_audit,
            "/v1/fooocus/status":   self._serve_fooocus_status,
            "/v1/images":           self._serve_images,
            "/metrics":             self._serve_metrics,
            "/v1/security":         self._serve_security,
            "/v1/security/geoip":   self._serve_security_geoip,
            "/v1/queue":            self._serve_queue,
            "/v1/deploy/status":    self._serve_deploy_status,
            "/v1/gameserver/status":self._serve_gameserver_status,
            "/v1/gameserver/log":   self._serve_gameserver_log,
            "/v1/gameserver/players":self._serve_gameserver_players,
            "/registro":            self._serve_registro,
            # ── V10.1 Endpoints ────────────────────────────────────────
            "/v1/hardware":         self._serve_hardware,
            "/v1/cost":             self._serve_cost,
            "/v1/watchdog":         self._serve_watchdog,
            "/v1/sessions":         self._serve_sessions,
            "/v1/rag/status":       self._serve_rag_status,
            # ── V10.1 New Endpoints ─────────────────────────────────────────────
            "/v1/queue/stream":     self._serve_queue_stream,
            "/v1/fabricaweb/status":self._serve_fabricaweb_status,
            # ── V10.3 Video Studio ──────────────────────────────────────────────
            "/v1/video/status":     self._serve_video_status,
            "/v1/video/download":   self._serve_video_download,
            "/v1/video/voices":     self._serve_video_voices,
            # ── V10.3 Image Lab (Pollinations) ────────────────────────────────────────
            "/v1/image/health":     self._serve_pollinations_health,
            "/v1/image/lab/history":self._serve_image_lab_list,
        }

        # Rutas con query string (?server=&lines=)
        path_clean = self.path.split("?")[0]
        if path_clean in routes:
            routes[path_clean]()
        elif self.path.startswith("/static/output/"):
            self._serve_static_output()
        elif self.path.startswith("/static/imagelab/"):
            self._serve_static_image_lab()
        else:
            self.send_response(404)
            self.end_headers()

    # Rutas manejadas de forma nativa por los modulos Mixins incorporados

    def log_message(self, fmt, *args):
        log.debug(fmt % args)


# ── Entry point ───────────────────────────────────────────────────────────────
def run_server():
    port = config.get("server.port", 7860)
    provider_manager.scan_all()
    threading.Thread(target=background_scanner, daemon=True).start()

    # Arrancar módulos background V10.1 + V10.3
    security_monitor.start()
    image_queue.start()
    video_pipeline.start()
    engine_watchdog.start(verbose=True)
    ai_process_manager.discover_apps()

    # ── WAL Checkpoint: truncar el Write-Ahead Log de SQLite antes de arrancar ──
    # Evita que _cache.sqlite-wal crezca indefinidamente entre sesiones.
    try:
        import sqlite3 as _sqlite3
        _wal_path = os.path.join(_BASE, "_cache.sqlite")
        if os.path.exists(_wal_path):
            _wal_conn = _sqlite3.connect(_wal_path)
            _wal_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            _wal_conn.close()
            log.info("[V10.3] WAL checkpoint completado en _cache.sqlite.")
    except Exception as _e:
        log.debug(f"[V10.3] WAL checkpoint salteado: {_e}")

    log.info("[V10.3] Security Monitor, Image Queue, Video Pipeline, Engine Watchdog, AI Process Manager activos.")

    log.info(f"Gravity Bridge V10.3 — http://localhost:{port} | Dashboard: / | API: /v1")
    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


def main():
    """Entry point para gravity_launcher.pyw en modo frozen (PyInstaller)."""
    run_server()


if __name__ == "__main__":
    run_server()
