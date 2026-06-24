import json
import time
import os
import sys
import subprocess
import psutil
from core import security_monitor, image_queue, deploy_manager, ai_process_manager


class PostSystemMixin:
    def _handle_post_system(self):
        if self.path == "/v1/scheduler/trigger":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                from core import content_scheduler

                result = content_scheduler.queue_now(
                    niche_id=data.get("niche_id"),
                    topic=data.get("topic"),
                )
                body = json.dumps(result).encode("utf-8")
                self.send_response(200 if result.get("ok") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/scheduler/topic/add — Agregar un topic nuevo a un niche
        if self.path == "/v1/scheduler/topic/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                niche_id = data.get("niche_id", "").strip()
                topic = data.get("topic", "").strip()
                if not niche_id or not topic:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {"error": "niche_id y topic son requeridos"}
                        ).encode()
                    )
                    return True
                from core import content_scheduler

                result = content_scheduler.add_topic(niche_id, topic)
                body = json.dumps(result).encode("utf-8")
                self.send_response(200 if result.get("ok") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/youtube/auth/exchange — Intercambiar código OAuth por refresh_token
        if self.path == "/v1/cost/limit":
            from api.routes.handlers.revenue_handler import handle_cost_limit

            handle_cost_limit(self)
            return True

        # /v1/rag/ingest — Ingestión de archivos PDF/TXT al índice RAG
        if self.path == "/v1/universal/config":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                base_url = data.get("universal_base_url", "").strip()
                model = data.get("universal_model", "").strip()

                BASE_DIR = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                settings_path = os.path.join(BASE_DIR, "_settings.json")

                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                if base_url:
                    settings["universal_base_url"] = base_url
                if model:
                    settings["universal_model"] = model

                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)

                body = json.dumps({"ok": True}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/audit/rotate — Archivar el audit log actual y empezar uno limpio
        if self.path == "/v1/audit/rotate":
            try:
                BASE_DIR = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                audit_path = os.path.join(BASE_DIR, "_audit_log.jsonl")
                archive_dir = os.path.join(BASE_DIR, "_archivo")
                os.makedirs(archive_dir, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                archive_path = os.path.join(archive_dir, f"audit_{ts}.jsonl")
                if os.path.exists(audit_path):
                    import shutil

                    shutil.copy2(audit_path, archive_path)
                    with open(audit_path, "w", encoding="utf-8") as f:
                        f.write("")  # truncar
                    size_kb = round(os.path.getsize(archive_path) / 1024, 1)
                    body = json.dumps(
                        {"ok": True, "archived_to": archive_path, "size_kb": size_kb}
                    ).encode()
                else:
                    body = json.dumps(
                        {"ok": True, "note": "No habia audit log que rotar"}
                    ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/security/scan — Disparar escaneo activo del monitor de seguridad
        if self.path == "/v1/security/scan":
            try:
                # Ejecutar escaneo completo forzado de manera sincrona para que
                # el frontend reciba y vea los resultados inmediatos.
                if hasattr(security_monitor, "force_scan"):
                    state = security_monitor.force_scan()
                else:
                    state = (
                        security_monitor.get_state()
                        if hasattr(security_monitor, "get_state")
                        else {}
                    )

                body = json.dumps(
                    {
                        "ok": True,
                        "message": "Escaneo de seguridad completado",
                        "state": state,
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        if self.path == "/v1/fabricaweb/deploy":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                project_path = data.get("project_path")

                # Dispara el pipeline (deploy_manager.start_deploy ya maneja el hilo interno)
                result = deploy_manager.start_deploy(project_path)

                self.send_response(200 if result.get("started") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "ok": result.get("started", False),
                            "message": result.get(
                                "reason", "Deploy hacia FabricaWeb iniciado"
                            ),
                            "job_id": "fabricaweb_deploy",
                        }
                    ).encode()
                )
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/image/generate — Image Lab independiente via Pollinations.ai
        if self.path == "/v1/watchdog/unlock":
            try:
                BASE_DIR = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                settings_path = os.path.join(BASE_DIR, "_settings.json")
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                settings["model_locked"] = False
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "ok": True,
                            "message": "Modelo desbloqueado. Auto-switch reactivo.",
                        }
                    ).encode()
                )
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/gameserver/start
        if self.path == "/v1/ai/start":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "")
                result = ai_process_manager.start_engine(provider)
                body = json.dumps(result).encode("utf-8")
                self.send_response(200 if result.get("success") else 400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return True

        if self.path == "/v1/ai/stop":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "")
                result = ai_process_manager.stop_engine(provider)
                body = json.dumps(result).encode("utf-8")
                self.send_response(200 if result.get("success") else 400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return True

        # /v1/queue/add — Añadir trabajo a la cola de imágenes
        if self.path == "/v1/queue/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                if not prompt:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(b'{"error":"prompt requerido"}')
                    return True
                job_id = image_queue.add_job(
                    prompt=prompt,
                    performance=data.get("performance", "Speed"),
                    width=int(data.get("width", 1024)),
                    height=int(data.get("height", 1024)),
                )
                body = json.dumps({"ok": True, "job_id": job_id}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/queue/cancel — Cancela un job de imagen por ID
        if self.path.startswith("/v1/queue/cancel"):
            try:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(self.path).query)
                job_id = qs.get("id", [None])[0]
                if not job_id:
                    length = int(self.headers.get("Content-Length", 0))
                    data = json.loads(self.rfile.read(length)) if length else {}
                    job_id = data.get("id") or data.get("job_id")
                if not job_id:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(b'{"error":"id requerido"}')
                    return
                ok = (
                    image_queue.cancel_job(job_id)
                    if hasattr(image_queue, "cancel_job")
                    else False
                )
                body = json.dumps(
                    {
                        "ok": ok,
                        "job_id": job_id,
                        "message": (
                            "Cancelado" if ok else "Job no encontrado o ya completado"
                        ),
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/queue/delete — Elimina un job por ID
        if self.path.startswith("/v1/queue/delete"):
            try:
                from urllib.parse import parse_qs, urlparse

                qs = parse_qs(urlparse(self.path).query)
                job_id = qs.get("id", [None])[0]
                if not job_id:
                    length = int(self.headers.get("Content-Length", 0))
                    data = json.loads(self.rfile.read(length)) if length else {}
                    job_id = data.get("id") or data.get("job_id")
                if not job_id:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(b'{"error":"id requerido"}')
                    return
                from core.image_queue import _get_conn, _notify_update

                with _get_conn() as conn:
                    cur = conn.execute("DELETE FROM image_jobs WHERE id=?", (job_id,))
                    ok = cur.rowcount > 0
                _notify_update()
                body = json.dumps(
                    {
                        "ok": ok,
                        "job_id": job_id,
                        "message": "Eliminado" if ok else "Job no encontrado",
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/queue/clear_history — Limpia todo el historial
        if self.path == "/v1/queue/clear_history":
            try:
                from core.image_queue import _get_conn, _notify_update

                with _get_conn() as conn:
                    cur = conn.execute(
                        "DELETE FROM image_jobs WHERE status IN ('done', 'failed', 'cancelled')"
                    )
                    ok = cur.rowcount > 0
                _notify_update()
                body = json.dumps(
                    {"ok": True, "message": "Historial limpiado"}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        if self.path == "/v1/deploy":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                project_path = data.get("project_path")
                result = deploy_manager.start_deploy(project_path)
                body = json.dumps(result).encode()
                code = 200 if result.get("started") else 400
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/generate — Generar imagen via Fooocus desde API REST
        if self.path == "/v1/generate":
            try:
                BASE = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                tools_dir = os.path.join(BASE, "tools")
                if tools_dir not in sys.path:
                    sys.path.insert(0, tools_dir)
                from fooocus_client import generate_image, ImageGenRequest

                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                req: ImageGenRequest = {
                    "prompt": data.get("prompt", "a beautiful landscape"),
                    "negative_prompt": data.get("negative_prompt", ""),
                    "width": int(data.get("width", 1024)),
                    "height": int(data.get("height", 1024)),
                    "num_images": int(data.get("num_images", 1)),
                    "performance": data.get("performance", "Speed"),
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
                self.wfile.write(
                    json.dumps({"success": False, "error": str(e)}).encode()
                )
            return True

        # /v1/video/create — Encola un nuevo trabajo de generación de video
        if self.path == "/v1/course/generate":
            from api.routes.handlers.video_handler import handle_course_generate

            handle_course_generate(self)
            return True

        # /v1/video/preview_voice — TTS preview de voz seleccionada
        if self.path == "/v1/security/kill":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                pid = int(data.get("pid", 0))
                if not pid:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "pid requerido"}).encode())
                    return True
                try:
                    # psutil ya importado
                    p = psutil.Process(pid)
                    pname = p.name()
                    p.terminate()
                    body = json.dumps(
                        {
                            "ok": True,
                            "message": f"Proceso {pname} (PID {pid}) terminado.",
                            "pid": pid,
                        }
                    ).encode()
                except ImportError:
                    # subprocess ya importado
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/F"], capture_output=True
                        )
                    body = json.dumps(
                        {
                            "ok": True,
                            "message": f"Kill enviado a PID {pid}.",
                            "pid": pid,
                        }
                    ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/gameserver/backup — Backup server DB
        if self.path == "/v1/sessions/spawn":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                s_id = data.get("session_id", "").strip()
                s_role = data.get("role", "").strip() or None

                from core.session_runner import SessionSpawner

                # Spawn session as subprocess
                spawner = SessionSpawner()
                spawner.spawn(session_id=s_id, work_data={}, role=s_role)

                body = json.dumps(
                    {
                        "ok": True,
                        "session_id": s_id,
                        "message": f"Worker para sesión {s_id} levantado.",
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/sessions/kill — Termina un subproceso de sesión
        if self.path == "/v1/sessions/kill":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                s_id = data.get("session_id", "").strip()

                from core.session_runner import active_sessions

                if s_id in active_sessions:
                    handle = active_sessions[s_id]
                    if handle.process.poll() is None:
                        handle.process.terminate()
                    del active_sessions[s_id]
                    msg = f"Worker {s_id} terminado con éxito."
                else:
                    msg = f"Worker {s_id} no encontrado o ya inactivo."

                body = json.dumps({"ok": True, "message": msg}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/hitl/approve — Aprobar una acción pendiente
        return False
