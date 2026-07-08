"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - BRIDGE SERVER V16.14 PRO [Omniscient-Tier Edition]      ║
║            Enrutador Universal OpenAI-Compatible + Multi-Session             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import os
import sys

# ── Windows UTF-8 Safety ──────────────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
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
from core.logger import log
from core.config_manager import config
from api.state import check_rate_limit, register_ip_hit, RATE_LIMIT_WINDOW
from core import service_loader
from core.db_migrator import run_pending as _run_db_migrations

# ── V16.14 PRO Multi-Session Bridge ────────────────────────────────────────────────
from core.session_runner import SessionSpawner, start_orphan_reaper

ACTIVE_SESSIONS = {}
MAX_SESSIONS = 32


def bridge_poll_loop():
    """Loop continuo de polling asíncrono para orquestar sub-sesiones en paralelo."""
    log.info("[V16.14 PRO] Multi-Session Poll Loop activado. Capacidad máxima: 32.")
    SessionSpawner(sys.executable, os.path.join(_BASE, "ask_deepseek.py"))

    while True:
        # Simular poll checking. La capacidad se controla con BoundedSemaphore internamente en SessionSpawner.
        time.sleep(1.0)


class Console_Safe:
    def print(self, *args, **kwargs):
        try:
            print(*args)
        except Exception:
            pass


console = Console_Safe()


# ── Background provider scanner ───────────────────────────────────────────────
def background_scanner():
    while True:
        try:
            provider_manager.scan_all()
        except Exception:
            pass
        time.sleep(30)


# ── HTTP Handler ──────────────────────────────────────────────────────────────
from api.routes.mixin_get import GetRoutesMixin  # noqa: E402
from api.routes.mixin_post import PostRoutesMixin  # noqa: E402
from api.routes.mixin_workflow import WorkflowMixin  # noqa: E402


class GravityBridgeHandler(BaseHTTPRequestHandler, GetRoutesMixin, PostRoutesMixin, WorkflowMixin):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # Cliente desconectado abruptamente

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _check_rate(self) -> bool:
        """Verifica el rate limit para la IP del cliente. Retorna False y envía 429 si bloqueada."""
        ip = self.client_address[0] if self.client_address else "unknown"
        if ip != "unknown":
            register_ip_hit(ip)
        if not check_rate_limit(ip):
            body = json.dumps(
                {"error": "Too Many Requests", "retry_after": RATE_LIMIT_WINDOW}
            ).encode()
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", str(RATE_LIMIT_WINDOW))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
            return False
        return True

    def do_OPTIONS(self):
        if not self._check_rate():
            return
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        if not self._check_rate():
            return
        routes = {
            "/": self._serve_dashboard,
            "/dashboard": self._serve_dashboard,
            "/health": self._serve_health,
            "/v1/models": self._serve_models,
            "/v1/status": self._serve_status,
            "/v1/audit": self._serve_audit,
            "/v1/fooocus/status": self._serve_fooocus_status,
            "/v1/images": self._serve_images,
            "/metrics": self._serve_metrics,
            "/v1/security": self._serve_security,
            "/v1/security/geoip": self._serve_security_geoip,
            "/v1/queue": self._serve_queue,
            "/v1/deploy/status": self._serve_deploy_status,
            "/v1/gameserver/status": self._serve_gameserver_status,
            "/v1/gameserver/log": self._serve_gameserver_log,
            "/v1/gameserver/players": self._serve_gameserver_players,
            "/registro": self._serve_registro,
            # ── V16.14 PRO Endpoints ────────────────────────────────────────
            "/v1/hardware": self._serve_hardware,
            "/v1/hardware/stats": self._serve_hardware,
            "/v1/cost": self._serve_cost,
            "/v1/watchdog": self._serve_watchdog,
            "/v1/sessions": self._serve_sessions,
            "/v1/rag/status": self._serve_rag_status,
            "/v1/rag/search": self._serve_rag_search,
            # ── V16.14 PRO New Endpoints ─────────────────────────────────────────────
            "/v1/queue/stream": self._serve_queue_stream,
            "/v1/fabricaweb/status": self._serve_fabricaweb_status,
            # ── V16.14 PRO Video Studio ──────────────────────────────────────────────
            "/v1/video/status": self._serve_video_status,
            "/v1/video/download": self._serve_video_download,
            "/v1/video/voices": self._serve_video_voices,
            "/v1/video/engines": self._serve_video_engines,
            "/v1/video/stream": self._serve_video_stream,
            "/v1/video/thumbnail": self._serve_video_thumbnail,
            "/v1/video/list": self._serve_video_list,
            # ── V16.14 PRO Image Lab (Pollinations) ────────────────────────────────────────
            "/v1/image/health": self._serve_pollinations_health,
            "/v1/image/lab/history": self._serve_image_lab_list,
            # ── V16.14 PRO Diamond Tier ───────────────────────────────────────────────
            "/v1/sessions/active": self._serve_active_sessions,
            "/v1/mcp/status": self._serve_mcp_status,
            "/v1/mcp/resource": self._serve_mcp_resource,
            "/v1/hitl/pending": self._serve_hitl_pending,
            "/v1/tools/firecrawl/health": self._serve_firecrawl_health,
            # ── V16.14 PRO Gravity Brain ──────────────────────────────────────────────
            "/v1/gravity/context": self._serve_gravity_context,
            # ── V16.14 PRO MAI Animations ────────────────────────────────────────────
            "/v1/video/animations": self._serve_video_animations,
            "/v1/processes": self._serve_processes,
            # ── V16.14 PRO Monetización ─────────────────────────────────────────────
            "/v1/scheduler/status": self._serve_scheduler_status,
            "/v1/scheduler/niches": self._serve_scheduler_niches,
            "/v1/youtube/status": self._serve_youtube_status,
            "/v1/youtube/auth/url": self._serve_youtube_auth_url,
            "/v1/video/upload-status": self._serve_video_upload_status,
            # ── V16.0 Monetization Hub ────────────────────────────────────────
            "/v1/revenue/summary": self._serve_revenue_summary,
            "/v1/revenue/timeline": self._serve_revenue_timeline,
            "/v1/revenue/top": self._serve_revenue_top_jobs,
            "/v1/youtube/quota": self._serve_youtube_quota,
            "/v1/social/status": self._serve_social_status,
            "/v1/affiliates/status": self._serve_affiliates_status,
            "/v1/affiliates/programs": self._serve_affiliates_programs,
            "/v1/language/status": self._serve_language_status,
            "/v1/v2v/status": self._serve_v2v_status,
            # ── Gravity OBS Control + Gravity Spark ───────────────────────────────
            "/v1/obs/status": self._serve_obs_status,
            "/v1/obs/scenes": self._serve_obs_scenes,
            "/v1/obs/scene/items": self._serve_obs_scene_items,
            "/v1/obs/inputs": self._serve_obs_inputs,
            "/v1/obs/stream/status": self._serve_obs_stream_status,
            "/v1/obs/overlays": self._serve_obs_overlays,
            "/v1/bounties": self._serve_bounties,
            "/v1/factory/list": self._serve_factory_list,
            "/v1/infiltrator/status": self._serve_infiltrator_status,
            # ── La Tinka Engine ────────────────────────────────────────────────────
            "/v1/tinka/status": self._serve_tinka_status,
            "/v1/tinka/analyze": self._serve_tinka_analyze,
            "/v1/tinka/predict": self._serve_tinka_predict,
            "/v1/tinka/update": self._serve_tinka_update,
            # ── V16.14 PRO Autonomous Edition ───────────────────────────────────────
            "/v1/autonomy/status": self._serve_autonomy_status,
            "/v1/autonomy/decisions": self._serve_autonomy_decisions,
            "/v1/autonomy/rules": self._serve_autonomy_rules,
            "/v1/reflection/report": self._serve_reflection_report,
            "/v1/reflection/patches": self._serve_reflection_patches,
            # ── Periodista Autónomo (OSINT) ────────────────────────────────────────
            "/v1/journalist/status": self._serve_journalist_status,
            "/v1/journalist/log": self._serve_journalist_log,
            "/v1/journalist/news": self._serve_journalist_news,
            # ── J.A.R.V.I.S y Radar HF ────────────────────────────────────────────
            "/v1/jarvis/status": self._serve_jarvis_status,
            "/v1/radar/status": self._serve_radar_status,
            # ── NPU AMD XDNA (FastFlowLM) ─────────────────────────────────────────
            "/v1/npu/status": self._serve_npu_status,
            # ── Gravity Workflow Engine ────────────────────────────────────────
            "/v1/workflow/list": self._serve_workflow_list,
            "/v1/workflow/nodes": self._serve_workflow_nodes,
            "/v1/workflow/jobs": self._serve_workflow_jobs,
        }

        # Rutas con query string (?server=&lines=)
        path_clean = self.path.split("?")[0]
        if path_clean in routes:
            routes[path_clean]()
        elif self.path.startswith("/v1/workflow/status/"):
            self._serve_workflow_status()
        elif self.path.startswith("/static/output/"):
            self._serve_static_output()
        elif self.path.startswith("/static/imagelab/"):
            self._serve_static_image_lab()
        elif self.path.startswith("/obs-overlay/"):
            self._serve_obs_overlay_html()
        elif self.path.startswith("/v1/factory/download/"):
            self._serve_factory_download()
        elif self.path.startswith("/images/"):
            self._serve_journalist_images()
        else:
            # Intentar servir desde el frontend/dist (JS, CSS, Assets)
            self._serve_frontend_static()

    # Rutas manejadas de forma nativa por los modulos Mixins incorporados

    def log_message(self, fmt, *args):
        log.debug(fmt % args)


# ── Entry point ───────────────────────────────────────────────────────────────
def run_server():
    port = config.get("server.port", 7860)

    # ── Pre-flight Checks ─────────────────────────────────────────────────────
    _BASE = os.path.dirname(os.path.abspath(__file__))
    portal_dir = os.path.join(os.path.dirname(_BASE), "gravity-news-portal")
    if not os.path.isdir(portal_dir):
        log.warning(
            f"[Pre-Flight] Directorio externo faltante: {portal_dir}. La publicación de noticias fallará silenciamente."
        )

    # ── Migraciones de base de datos ──────────────────────────────────────────
    try:
        migration_results = _run_db_migrations()
        total_applied = sum(v for v in migration_results.values() if v > 0)
        if total_applied > 0:
            log.info(
                f"[DBMigrator] {total_applied} migración(es) aplicadas al arrancar."
            )
        else:
            log.info("[DBMigrator] Todas las bases de datos están al día.")
    except Exception as _mig_e:
        log.error(f"[DBMigrator] Error en migraciones de arranque: {_mig_e}")

    provider_manager.scan_all()
    threading.Thread(
        target=background_scanner, daemon=True, name="GravityBGScanner"
    ).start()

    # Arrancar módulos background V16.14 PRO de manera tolerante a fallos
    service_loader.start_service("core.security_monitor")
    service_loader.start_service("core.image_queue")
    service_loader.start_service("core.video_pipeline")
    service_loader.start_service("core.engine_watchdog", verbose=True)
    # Los siguientes servicios pesados han sido desactivados del auto-arranque.
    # El usuario los controlará/lanzará manualmente desde el Dashboard.
    # service_loader.start_service("core.bounty_hunter")
    # service_loader.start_service("core.infiltrator")

    # ai_process_manager no tiene start() por defecto, pero se le invoca discover_apps()
    ai_process_manager_module = service_loader.load_module("core.ai_process_manager")
    if ai_process_manager_module:
        try:
            ai_process_manager_module.discover_apps()
        except Exception as e:
            log.error(f"Failed to discover apps in ai_process_manager: {e}")

    # service_loader.start_service("core.content_scheduler")

    # ── V16.14 PRO Autonomous Edition — Autogovernance Daemons ─────────────────
    # service_loader.start_service("core.self_reflection")
    # service_loader.start_service("core.autonomy_engine")
    log.info("[V16.14 PRO] Motores autónomos desactivados del auto-arranque a petición del usuario.")
    
    # ── J.A.R.V.I.S Sensory Bus (V16.14 PRO Sentinel-Tier) ──
    try:
        from core.sensory_bus import SensoryBus
        bus = SensoryBus(host="0.0.0.0", port=9999)
        # Desactivado auto-arranque del micrófono continuo por solicitud del usuario
        # bus.start_server_thread()
        log.info("[V16.14 PRO] J.A.R.V.I.S Sensory Bus preparado (iniciado en manual).")
        
        # ── Fase 5: Cognitive Loop (Voice-to-LLM Engine) ──
        def _cognitive_ws_thread():
            import websocket
            import json
            import time
            import threading
            from core import provider_manager, data_guardian
            from core.reasoning_stripper import ReasoningStripper
            from core.gravity_brain import build_gravity_system_prompt, parse_chat_commands, execute_system_command
            import os
            
            _base_dir_brain = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Memoria conversacional de voz persistente durante la sesión
            voice_history = []
            voice_history_lock = threading.Lock()

            import queue
            voice_queue = queue.Queue()

            def _safe_ws_send(text_msg):
                import json
                import asyncio
                payload = json.dumps({"type": "voice_output", "text": text_msg})
                if bus and bus.loop:
                    try:
                        asyncio.run_coroutine_threadsafe(bus.broadcast(payload), bus.loop)
                    except Exception as e:
                        log.error(f"[COGNITIVE-LOOP] Error en _safe_ws_send: {e}")

            def _process_voice_task(ws, user_text):
                try:
                    # 1. Cargar contexto real de Gravity
                    kb_data_brain = {}
                    try:
                        kb_data_brain, _ = data_guardian.load_knowledge(
                            os.path.join(_base_dir_brain, "_knowledge.json")
                        )
                    except Exception:
                        pass
                    
                    extra_rules = kb_data_brain.get("persistent_rules", [])
                    base_system_prompt = build_gravity_system_prompt(
                        extra_rules=extra_rules if extra_rules else None
                    )
                    
                    # Añadir directiva de voz
                    voice_directive = (
                        "\n\nDIRECTIVA DE VOZ (JARVIS): El usuario se está comunicando por micrófono. "
                        "Responde de forma natural, conversacional y corta. "
                        "ATENCIÓN: Tienes capacidades ejecutivas. Si el usuario te pide crear un video, generar una imagen, "
                        "ver el estado del sistema u otra acción de sistema, PUEDES y DEBES responder ÚNICAMENTE con el comando barra (/) correspondiente (e.g. '/video crear <tema>', '/status', '/imagen <prompt>'). "
                        "El sistema interceptará tu comando, lo ejecutará y le informará al usuario."
                    )
                    system_prompt = base_system_prompt + voice_directive
                    
                    messages = [{"role": "system", "content": system_prompt}]
                    with voice_history_lock:
                        messages.extend(list(voice_history))
                    messages.append({"role": "user", "content": user_text})
                    
                    bp, bm = provider_manager.get_best()
                    if not bp:
                        _safe_ws_send("Error. Sistemas cognitivos desconectados.")
                        return
                        
                    raw_text = provider_manager.complete(messages, model=bm, provider=bp.name, options={"temperature": 0.5})
                    clean_text = ReasoningStripper().process_chunk(raw_text).strip()
                    
                    # 2. Interceptar comandos si el LLM emitió uno (Robusto a ruido)
                    cmd_info = None
                    if "/" in clean_text:
                        cmd_candidate = clean_text[clean_text.find("/"):]
                        cmd_info = parse_chat_commands(cmd_candidate)
                    else:
                        cmd_info = parse_chat_commands(clean_text)
                        
                    if cmd_info:
                        log.info(f"[COGNITIVE-LOOP] Ejecutando comando por voz: {cmd_info}")
                        cmd_result = execute_system_command(cmd_info)
                        feedback = cmd_info.get("user_feedback", "Ejecutando orden.")
                        ok = cmd_result.get("ok", False)
                        res = cmd_result.get('result_text', '')
                        if ok:
                            clean_text = f"{feedback} Acción completada exitosamente."
                        else:
                            clean_text = f"Hubo un problema al ejecutar la orden. {res}"
                    
                    log.info(f"[COGNITIVE-LOOP] Respuesta generada: {clean_text}")
                    _safe_ws_send(clean_text)
                    
                    # 3. Guardar en historial (máx 10 intercambios para no saturar tokens)
                    with voice_history_lock:
                        voice_history.append({"role": "user", "content": user_text})
                        voice_history.append({"role": "assistant", "content": clean_text})
                        if len(voice_history) > 20:
                            del voice_history[:-20]  # Operación in-place segura gracias al Lock
                        
                except Exception as e:
                    log.error(f"[COGNITIVE-LOOP] Error en procesamiento LLM: {e}")
                    try:
                        _safe_ws_send("Señor, he sufrido un error crítico en mi red neuronal central.")
                    except Exception:
                        pass

            def _voice_worker():
                """Procesa la cola de voz secuencialmente para evitar saturar el modelo local."""
                while True:
                    user_text = voice_queue.get()
                    if user_text is None:
                        break
                    try:
                        _process_voice_task(None, user_text)
                    finally:
                        voice_queue.task_done()

            # Iniciar el worker secuencial de voz
            threading.Thread(target=_voice_worker, daemon=True, name="JarvisVoiceWorker").start()

            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get("type") == "voice_input":
                        user_text = data.get("text", "").strip()
                        if not user_text:
                            return
                        
                        log.info(f"[COGNITIVE-LOOP] Encolando comando de voz: {user_text}")
                        # Usar cola en lugar de hilos paralelos masivos para evitar crash del intérprete
                        voice_queue.put(user_text)
                        
                except Exception as e:
                    log.error(f"[COGNITIVE-LOOP] Error: {e}")

            def on_error(ws, error):
                log.error(f"[COGNITIVE-LOOP] WS Error: {error}")
                
            def on_close(ws, close_status_code, close_msg):
                log.warning(f"[COGNITIVE-LOOP] WS Cerrado: {close_status_code} {close_msg}")
                
            def on_open(ws):
                log.info("[COGNITIVE-LOOP] Conectado exitosamente al Sensory Bus (ws://127.0.0.1:9999)")
                
            # Loop de reconexión seguro sin recursión
            while True:
                try:
                    time.sleep(2)
                    ws = websocket.WebSocketApp("ws://127.0.0.1:9999", on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
                    ws.run_forever()
                except Exception:
                    pass
                time.sleep(3)


        # Desactivado el Cognitive Loop continuo al inicio para no saturar memoria.
        # threading.Thread(target=_cognitive_ws_thread, daemon=True, name="JarvisCognitiveLoop").start()
        # log.info("[V16.14 PRO] Cognitive Loop enlazado al Sensory Bus. Comandos de voz habilitados.")

        
    except Exception as e:
        log.error(f"Error iniciando Sensory Bus: {e}")

    # ── Registrar daemons críticos en el watchdog para auto-restart ───────────
    try:
        from core.engine_watchdog import register_daemon
        import threading as _th

        # Mapa: daemon_id → (nombre_exacto_del_thread, restart_fn)
        # Los nombres son los definidos con name= en threading.Thread() de cada módulo
        _daemon_map = {
            "autonomy_engine": (
                "GravityAutonomyEngine",
                lambda: service_loader.start_service("core.autonomy_engine"),
            ),
            "self_reflection": (
                "GravitySelfReflection",
                lambda: service_loader.start_service("core.self_reflection"),
            ),
            "content_scheduler": (
                "GravityContentScheduler",
                lambda: service_loader.start_service("core.content_scheduler"),
            ),
            "security_monitor": (
                "GravitySecurityMonitor",
                lambda: service_loader.start_service("core.security_monitor"),
            ),
        }
        for daemon_id, (thread_name, restart_fn) in _daemon_map.items():
            # Búsqueda exacta por nombre de thread
            t = next((th for th in _th.enumerate() if th.name == thread_name), None)
            if t:
                register_daemon(daemon_id, t, restart_fn)
                log.debug(f"[Watchdog] Daemon registrado: {daemon_id} ({thread_name})")
            else:
                log.debug(
                    f"[Watchdog] Thread '{thread_name}' no iniciado (daemon '{daemon_id}' en modo manual)"
                )
    except Exception as _wd_e:
        log.warning(f"[Watchdog] No se pudo registrar daemons para monitoreo: {_wd_e}")

    # ── Gravity OBS Control — Auto-conexion con OBS Studio ────────────────────
    log.info("[DEBUG] Iniciando OBS Auto-connect...")
    obs_module = service_loader.load_module("core.obs_client")
    if obs_module:
        try:
            obs_module.auto_connect_if_configured()
        except Exception as _obs_e:
            log.warning(f"[OBS] Auto-connect no disponible: {_obs_e}")
    log.info("[DEBUG] OBS Auto-connect finalizado.")

    # ── WAL Checkpoint: truncar el Write-Ahead Log de SQLite antes de arrancar ──
    # Evita que _cache.sqlite-wal crezca indefinidamente entre sesiones.
    try:
        import sqlite3 as _sqlite3

        from core.cache_engine import CACHE_DB as _wal_path
        if os.path.exists(_wal_path):
            log.info(f"[DEBUG] Conectando a {_wal_path} para WAL...")
            _wal_conn = _sqlite3.connect(_wal_path)
            log.info("[DEBUG] Ejecutando PRAGMA wal_checkpoint...")
            _wal_conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            _wal_conn.close()
            log.info("[V16.14 PRO] WAL checkpoint completado en cache DB.")
    except Exception as _e:
        log.debug(f"[V16.14 PRO] WAL checkpoint salteado: {_e}")

    log.info(
        "[V16.14 PRO] Security Monitor, Image Queue, Video Pipeline, Engine Watchdog, AI Process Manager activos."
    )

    # Iniciar Multi-Session Poll Loop (V16.14 PRO)
    threading.Thread(
        target=bridge_poll_loop, daemon=True, name="BridgePollLoop"
    ).start()

    # Iniciar daemon de limpieza de sesiones huérfanas (V16.14 PRO)
    start_orphan_reaper()
    log.info("[V16.14 PRO] OrphanReaper daemon activado.")

    log.info(
        f"Gravity Bridge V16.14 PRO — http://localhost:{port} | Dashboard: / | API: /v1"
    )
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
