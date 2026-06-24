import json
import os
import traceback
from core.logger import log


class PostMediaMixin:
    def _handle_post_media(self):
        if self.path == "/v1/youtube/analyzer/process":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                url = data.get("url", "").strip()

                if not url:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "url es requerida"}).encode())
                    return True

                from tools.youtube_analyzer import YouTubeAnalyzer

                analyzer = YouTubeAnalyzer()
                result = analyzer.process_url(url)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/bounties/action — Marcar trabajo como aplicado o descartado
        if self.path == "/v1/youtube/auth/exchange":
            from api.routes.handlers.revenue_handler import handle_youtube_auth_exchange

            handle_youtube_auth_exchange(self)
            return True

        # /v1/youtube/upload — Upload manual de un job completado a YouTube
        if self.path == "/v1/youtube/upload":
            from api.routes.handlers.revenue_handler import handle_youtube_upload

            handle_youtube_upload(self)
            return True

        # /v1/v2v/start — Arrancar motor VTuber V2V
        if self.path == "/v1/v2v/start":
            from api.routes.handlers.v2v_handler import handle_v2v_start

            handle_v2v_start(self)
            return True

        # /v1/v2v/stop — Detener motor VTuber V2V
        if self.path == "/v1/v2v/stop":
            from api.routes.handlers.v2v_handler import handle_v2v_stop

            handle_v2v_stop(self)
            return True

        # /v1/keys — Guardar API key cifrada en keystore
        if self.path == "/v1/image/generate":
            try:
                import uuid as _uuid
                import base64

                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                if not prompt:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "prompt requerido"}).encode())
                    return True

                width = int(data.get("width", 1024))
                height = int(data.get("height", 1024))
                model = data.get("model", "flux")
                negative_prompt = data.get("negative_prompt", "").strip()
                enhance_str = str(data.get("enhance", "true")).lower()
                enhance = enhance_str == "true"
                seed_val = data.get("seed", "")
                seed = None
                if seed_val and str(seed_val).isdigit():
                    seed = int(seed_val)

                BASE = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                lab_dir = os.path.join(BASE, "_integrations", "ImageLab")
                os.makedirs(lab_dir, exist_ok=True)

                filename = f"lab_{_uuid.uuid4().hex[:12]}.png"
                output_path = os.path.join(lab_dir, filename)

                provider = data.get("provider", "Pollinations.ai")

                if provider.lower() == "fooocus":
                    from tools.fooocus_client import generate_image
                    import shutil

                    try:
                        f_req = {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "width": width,
                            "height": height,
                            "num_images": 1,
                            "performance": "Speed",
                        }
                        result = generate_image(f_req)
                        if result.get("success") and result.get("images"):
                            img_path = result["images"][0]
                            shutil.copy2(img_path, output_path)
                            result["success"] = True
                        else:
                            result["error"] = result.get(
                                "error", "Error generando con Fooocus"
                            )
                            result["success"] = False
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                else:
                    from tools.pollinations_generator import generate as poll_gen

                    try:
                        result = poll_gen(
                            prompt=prompt,
                            output_path=output_path,
                            width=width,
                            height=height,
                            model=model,
                            seed=seed,
                            enhance=enhance,
                            negative_prompt=negative_prompt,
                        )
                    except Exception as e:
                        log.error(
                            f"[ImageLab] Error en poll_gen: {traceback.format_exc()}"
                        )
                        raise e

                if result.get("success") and os.path.isfile(output_path):
                    with open(output_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    body = json.dumps(
                        {
                            "ok": True,
                            "url": f"/static/imagelab/{filename}",
                            "filename": filename,
                            "b64": b64,
                            "width": width,
                            "height": height,
                            "model": model,
                        }
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    err = result.get("error", "Pollinations sin respuesta")
                    self.send_response(502)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": err}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/watchdog/unlock

        if self.path == "/v1/video/create":
            from api.routes.handlers.video_handler import handle_video_create

            handle_video_create(self)
            return True

        # /v1/course/generate — Generar un temario (Playlist) de N videos e insertarlo en el scheduler
        if self.path == "/v1/video/preview_voice":
            from api.routes.handlers.video_handler import handle_video_preview_voice

            handle_video_preview_voice(self)
            return True

        # /v1/video/cancel — Cancela un trabajo de video pendiente
        if self.path == "/v1/video/cancel":
            from api.routes.handlers.video_handler import handle_video_cancel

            handle_video_cancel(self)
            return True

        # /v1/video/delete — Elimina un job y sus archivos físicos
        if self.path == "/v1/video/delete":
            from api.routes.handlers.video_handler import handle_video_delete

            handle_video_delete(self)
            return True

        # /v1/tools/run — Code Runner (Python/Bash)
        if self.path == "/v1/affiliates/program/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                niche = data.get("niche_id", "")
                prog = data.get("program", {})
                if not niche or not prog:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "niche_id y program requeridos"}).encode()
                    )
                    return
                from core.affiliate_manager import add_program

                result = add_program(niche, prog)
                body = json.dumps(result).encode()
                self.send_response(200 if result["ok"] else 400)
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

        # /v1/social/distribute — Distribuir un Short a redes sociales manualmente
        if self.path == "/v1/social/distribute":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                job_id = data.get("job_id")
                if not job_id:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "job_id requerido"}).encode())
                    return
                import sqlite3 as _sq3

                BASE_D = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                db_p = os.path.join(BASE_D, "_video_queue.sqlite")
                conn = _sq3.connect(db_p, timeout=10)
                conn.row_factory = _sq3.Row
                row = conn.execute(
                    "SELECT shorts_path, title, topic FROM video_jobs WHERE id=?",
                    (int(job_id),),
                ).fetchone()
                conn.close()
                if not row or not row["shorts_path"]:
                    self.send_response(404)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "error": "Job sin shorts_path. Asegúrate de que el video fue procesado."
                            }
                        ).encode()
                    )
                    return
                from core.tiktok_uploader import distribute_short_async

                distribute_short_async(
                    job_id=int(job_id),
                    shorts_path=row["shorts_path"],
                    title=row["title"] or row["topic"] or f"Video #{job_id}",
                )
                body = json.dumps(
                    {
                        "ok": True,
                        "job_id": job_id,
                        "message": "Distribución iniciada en background.",
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

        # /v1/revenue/views/update — Actualizar vistas de un job (llamado desde integración externa)
        if self.path == "/v1/revenue/views/update":
            from api.routes.handlers.revenue_handler import handle_revenue_views_update

            handle_revenue_views_update(self)
            return True

        # ── OBS Control: /v1/obs/* ──────────────────────────────────────────────

        # POST /v1/obs/connect
        if self.path == "/v1/obs/connect":
            from api.routes.handlers.obs_handler import handle_obs_connect

            handle_obs_connect(self)
            return True

        # POST /v1/obs/scene/switch
        if self.path == "/v1/obs/scene/switch":
            from api.routes.handlers.obs_handler import handle_obs_scene_switch

            handle_obs_scene_switch(self)
            return True

        # POST /v1/obs/source/toggle
        if self.path == "/v1/obs/source/toggle":
            from api.routes.handlers.obs_handler import handle_obs_source_toggle

            handle_obs_source_toggle(self)
            return True

        # POST /v1/obs/source/visible
        if self.path == "/v1/obs/source/visible":
            from api.routes.handlers.obs_handler import handle_obs_source_visible

            handle_obs_source_visible(self)
            return True

        # POST /v1/obs/stream/start
        if self.path == "/v1/obs/stream/start":
            from api.routes.handlers.obs_handler import handle_obs_stream_start

            handle_obs_stream_start(self)
            return True

        # POST /v1/obs/stream/stop
        if self.path == "/v1/obs/stream/stop":
            from api.routes.handlers.obs_handler import handle_obs_stream_stop

            handle_obs_stream_stop(self)
            return True

        # POST /v1/obs/stream/toggle
        if self.path == "/v1/obs/stream/toggle":
            from api.routes.handlers.obs_handler import handle_obs_stream_toggle

            handle_obs_stream_toggle(self)
            return True

        # POST /v1/obs/record/start
        if self.path == "/v1/obs/record/start":
            from api.routes.handlers.obs_handler import handle_obs_record_start

            handle_obs_record_start(self)
            return True

        # POST /v1/obs/record/stop
        if self.path == "/v1/obs/record/stop":
            from api.routes.handlers.obs_handler import handle_obs_record_stop

            handle_obs_record_stop(self)
            return True

        # POST /v1/obs/record/toggle
        if self.path == "/v1/obs/record/toggle":
            from api.routes.handlers.obs_handler import handle_obs_record_toggle

            handle_obs_record_toggle(self)
            return True

        # POST /v1/obs/audio/mute
        if self.path == "/v1/obs/audio/mute":
            from api.routes.handlers.obs_handler import handle_obs_audio_mute

            handle_obs_audio_mute(self)
            return True

        # POST /v1/obs/audio/volume
        if self.path == "/v1/obs/audio/volume":
            from api.routes.handlers.obs_handler import handle_obs_audio_volume

            handle_obs_audio_volume(self)
            return True

        # POST /v1/obs/spark/generate
        if self.path == "/v1/obs/spark/generate":
            from api.routes.handlers.obs_handler import handle_obs_spark_generate

            handle_obs_spark_generate(self)
            return True

        # POST /v1/obs/spark/edit
        if self.path == "/v1/obs/spark/edit":
            from api.routes.handlers.obs_handler import handle_obs_spark_edit

            handle_obs_spark_edit(self)
            return True

        # POST /v1/obs/spark/remove
        if self.path == "/v1/obs/spark/remove":
            from api.routes.handlers.obs_handler import handle_obs_spark_remove

            handle_obs_spark_remove(self)
            return True

        # ── V16.0 PRO Autonomous Edition POST handlers ───────────────────────────

        # POST /v1/autonomy/trigger — Forzar un ciclo OODA inmediato
        return False
