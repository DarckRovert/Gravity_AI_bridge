"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - BRIDGE SERVER V12.2 PRO [Omniscient-Tier Edition]          ║
║            Enrutador Universal OpenAI-Compatible + Multi-Session             ║
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
from core import content_scheduler

# ── V12.2 PRO Multi-Session Bridge ────────────────────────────────────────────────
from core.session_runner import SessionSpawner, start_orphan_reaper

ACTIVE_SESSIONS = {}
MAX_SESSIONS = 32

def bridge_poll_loop():
    """Loop continuo de polling asíncrono para orquestar sub-sesiones en paralelo."""
    log.info("[V12.2 PRO] Multi-Session Poll Loop activado. Capacidad máxima: 32.")
    spawner = SessionSpawner(sys.executable, os.path.join(_BASE, "ask_deepseek.py"))
    
    while True:
        # Simular poll checking. La capacidad se controla con BoundedSemaphore internamente en SessionSpawner.
        time.sleep(1.0)



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
            # ── V12.2 PRO Endpoints ────────────────────────────────────────
            "/v1/hardware":         self._serve_hardware,
            "/v1/hardware/stats":   self._serve_hardware,
            "/v1/cost":             self._serve_cost,
            "/v1/watchdog":         self._serve_watchdog,
            "/v1/sessions":         self._serve_sessions,
            "/v1/rag/status":       self._serve_rag_status,
            "/v1/rag/search":       self._serve_rag_search,
            # ── V12.2 PRO New Endpoints ─────────────────────────────────────────────
            "/v1/queue/stream":     self._serve_queue_stream,
            "/v1/fabricaweb/status":self._serve_fabricaweb_status,
            # ── V12.2 PRO Video Studio ──────────────────────────────────────────────
            "/v1/video/status":     self._serve_video_status,
            "/v1/video/download":   self._serve_video_download,
            "/v1/video/voices":     self._serve_video_voices,
            "/v1/video/engines":    self._serve_video_engines,
            "/v1/video/stream":     self._serve_video_stream,
            "/v1/video/thumbnail":  self._serve_video_thumbnail,
            "/v1/video/list":       self._serve_video_list,
            # ── V12.2 PRO Image Lab (Pollinations) ────────────────────────────────────────
            "/v1/image/health":     self._serve_pollinations_health,
            "/v1/image/lab/history":self._serve_image_lab_list,
            # ── V12.2 PRO Diamond Tier ───────────────────────────────────────────────
            "/v1/sessions/active":       self._serve_active_sessions,
            "/v1/mcp/status":            self._serve_mcp_status,
            "/v1/mcp/resource":          self._serve_mcp_resource,
            "/v1/hitl/pending":          self._serve_hitl_pending,
            "/v1/tools/firecrawl/health":self._serve_firecrawl_health,
            # ── V12.2 PRO Gravity Brain ──────────────────────────────────────────────
            "/v1/gravity/context":       self._serve_gravity_context,
            # ── V12.2 PRO MAI Animations ────────────────────────────────────────────
            "/v1/video/animations":      self._serve_video_animations,
            "/v1/processes":             self._serve_processes,
            # ── V12.2 PRO Monetización ─────────────────────────────────────────────
            "/v1/scheduler/status":       self._serve_scheduler_status,
            "/v1/scheduler/niches":       self._serve_scheduler_niches,
            "/v1/youtube/status":         self._serve_youtube_status,
            "/v1/youtube/auth/url":       self._serve_youtube_auth_url,
            "/v1/video/upload-status":    self._serve_video_upload_status,
            # ── V12.2 Monetization Hub ────────────────────────────────────────
            "/v1/revenue/summary":        self._serve_revenue_summary,
            "/v1/revenue/timeline":       self._serve_revenue_timeline,
            "/v1/revenue/top":            self._serve_revenue_top_jobs,
            "/v1/youtube/quota":          self._serve_youtube_quota,
            "/v1/social/status":          self._serve_social_status,
            "/v1/affiliates/status":      self._serve_affiliates_status,
            "/v1/affiliates/programs":    self._serve_affiliates_programs,
            "/v1/language/status":        self._serve_language_status,
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
            # Intentar servir desde el frontend/dist (JS, CSS, Assets)
            self._serve_frontend_static()


    # Rutas manejadas de forma nativa por los modulos Mixins incorporados

    def log_message(self, fmt, *args):
        log.debug(fmt % args)


# ── Entry point ───────────────────────────────────────────────────────────────
def run_server():
    port = config.get("server.port", 7860)
    provider_manager.scan_all()
    threading.Thread(target=background_scanner, daemon=True, name="GravityBGScanner").start()

    # Arrancar módulos background V12.2 PRO + V12.2 PRO
    security_monitor.start()
    image_queue.start()
    video_pipeline.start()
    engine_watchdog.start(verbose=True)
    ai_process_manager.discover_apps()
    content_scheduler.start()

    # ── WAL Checkpoint: truncar el Write-Ahead Log de SQLite antes de arrancar ──
    # Evita que _cache.sqlite-wal crezca indefinidamente entre sesiones.
    try:
        import sqlite3 as _sqlite3
        _wal_path = os.path.join(_BASE, "_cache.sqlite")
        if os.path.exists(_wal_path):
            _wal_conn = _sqlite3.connect(_wal_path)
            _wal_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            _wal_conn.close()
            log.info("[V12.2 PRO] WAL checkpoint completado en _cache.sqlite.")
    except Exception as _e:
        log.debug(f"[V12.2 PRO] WAL checkpoint salteado: {_e}")

    log.info("[V12.2 PRO] Security Monitor, Image Queue, Video Pipeline, Engine Watchdog, AI Process Manager activos.")

    # Iniciar Multi-Session Poll Loop (V12.2 PRO)
    threading.Thread(target=bridge_poll_loop, daemon=True, name="BridgePollLoop").start()

    # Iniciar daemon de limpieza de sesiones huérfanas (V12.2 PRO)
    start_orphan_reaper()
    log.info("[V12.2 PRO] OrphanReaper daemon activado.")

    log.info(f"Gravity Bridge V12.2 PRO — http://localhost:{port} | Dashboard: / | API: /v1")
    server = ThreadingHTTPServer(("0.0.0.0", port), GravityBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("[Gravity] Shutdown solicitado. Terminando sesiones activas...")
        try:
            from core.session_runner import shutdown as _sessions_shutdown
            _sessions_shutdown()
        except Exception:
            pass
        server.server_close()
        log.info("[Gravity] Server cerrado limpiamente.")


def main():
    """Entry point para gravity_launcher.pyw en modo frozen (PyInstaller)."""
    run_server()


if __name__ == "__main__":
    run_server()
