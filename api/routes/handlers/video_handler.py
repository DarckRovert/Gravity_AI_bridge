import json
import os
import time
import uuid
import yaml
from core import video_pipeline


def handle_video_status(handler):
    try:
        data = video_pipeline.get_queue_status()
        try:
            import shutil

            BASE_DIR_v = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
            videos_dir = os.path.join(BASE_DIR_v, "_videos")
            disk = shutil.disk_usage(
                videos_dir if os.path.isdir(videos_dir) else BASE_DIR_v
            )
            data["disk_total_gb"] = round(disk.total / (1024**3), 1)
            data["disk_used_gb"] = round(disk.used / (1024**3), 1)
            data["disk_free_gb"] = round(disk.free / (1024**3), 1)
            data["disk_pct"] = round(disk.used / disk.total * 100, 1)
            total_size = (
                sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, dn, fns in os.walk(videos_dir)
                    for f in fns
                )
                if os.path.isdir(videos_dir)
                else 0
            )
            data["videos_size_gb"] = round(total_size / (1024**3), 3)
        except Exception:
            pass
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header(
            "Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"
        )
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_voices(handler):
    try:
        voices = video_pipeline.get_available_voices()
        styles = {k: v["label"] for k, v in video_pipeline.CINEMA_STYLES.items()}

        gemini_configured = False
        gemini_voices = {}
        try:
            import sys as _sys

            BASE_DIR_g = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
            _int_dir = os.path.join(BASE_DIR_g, "_integrations")
            if _int_dir not in _sys.path:
                _sys.path.insert(0, _int_dir)
            from gemini_tts import (
                list_voices as _gemini_voices,
                get_api_key_from_gravity,
            )

            gemini_key = get_api_key_from_gravity()
            if gemini_key:
                gemini_configured = True
                gemini_voices = _gemini_voices()
        except Exception:
            pass

        body = json.dumps(
            {
                "voices": voices,
                "count": len(voices),
                "styles": styles,
                "langs": {
                    "es": "Español",
                    "en": "English",
                    "pt": "Português",
                    "fr": "Français",
                    "de": "Deutsch",
                    "it": "Italiano",
                },
                "tts_engines": {
                    "sapi": {
                        "available": len(voices) > 0,
                        "label": "Windows SAPI (offline)",
                    },
                    "gemini": {
                        "available": gemini_configured,
                        "label": "Gemini TTS (online)",
                        "voices": gemini_voices,
                    },
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_engines(handler):
    try:
        import socket
        import concurrent.futures
        import urllib.request

        def _check_pollinations() -> bool:
            try:
                urllib.request.urlopen("https://image.pollinations.ai/", timeout=3)
                return True
            except Exception:
                return False

        def _check_comfyui() -> bool:
            try:
                sock = socket.create_connection(("127.0.0.1", 8188), timeout=1.5)
                sock.close()
                return True
            except Exception:
                return False

        def _check_fooocus() -> bool:
            try:
                import sys as _sys

                BASE_DIR_f = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                )
                tools_dir = os.path.join(BASE_DIR_f, "tools")
                if tools_dir not in _sys.path:
                    _sys.path.insert(0, tools_dir)
                from fooocus_client import health_check as _fhc

                return _fhc().get("online", False)
            except Exception:
                return False

        def _check_gemini() -> bool:
            try:
                import sys as _sys2

                BASE_DIR_gt = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                )
                _int_dir2 = os.path.join(BASE_DIR_gt, "_integrations")
                if _int_dir2 not in _sys2.path:
                    _sys2.path.insert(0, _int_dir2)
                from gemini_tts import get_api_key_from_gravity as _gak

                return bool(_gak())
            except Exception:
                return False

        def _check_nvidia() -> bool:
            try:
                from core.key_manager import KeyManager

                return KeyManager.has_key("nvidia")
            except Exception:
                return False

        def _get_sapi_count() -> int:
            try:
                return len(video_pipeline.get_available_voices())
            except Exception:
                return 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            f_poll = ex.submit(_check_pollinations)
            f_comfy = ex.submit(_check_comfyui)
            f_fooocus = ex.submit(_check_fooocus)
            f_gemini = ex.submit(_check_gemini)
            f_nvidia = ex.submit(_check_nvidia)
            f_sapi = ex.submit(_get_sapi_count)
            poll_ok = f_poll.result(timeout=4)
            comfy_ok = f_comfy.result(timeout=4)
            fooocus_ok = f_fooocus.result(timeout=4)
            gemini_ok = f_gemini.result(timeout=4)
            nvidia_ok = f_nvidia.result(timeout=4)
            sapi_n = f_sapi.result(timeout=4)

        engines = [
            {
                "id": "pollinations",
                "label": "Pollinations.ai",
                "type": "image",
                "tier": 1,
                "online": poll_ok,
                "description": "Generación de imágenes vía API remota",
            },
            {
                "id": "comfyui",
                "label": "ComfyUI / LTX-Video (MAI L2)",
                "type": "image_video",
                "tier": 2,
                "online": comfy_ok,
                "description": "Motor de animación I2V local (requiere ComfyUI en :8188)",
            },
            {
                "id": "fooocus",
                "label": "Fooocus",
                "type": "image",
                "tier": 3,
                "online": fooocus_ok,
                "description": "Generación de imágenes local vía Gradio (:7861)",
            },
            {
                "id": "sapi",
                "label": "Windows SAPI",
                "type": "tts",
                "tier": 1,
                "online": sapi_n > 0,
                "description": f"{sapi_n} voces instaladas (offline)",
            },
            {
                "id": "gemini_tts",
                "label": "Gemini TTS",
                "type": "tts",
                "tier": 3,
                "online": gemini_ok,
                "description": "Síntesis premium vía Google AI Studio (requiere API key)",
            },
            {
                "id": "nvidia_nim",
                "label": "Nvidia NIM",
                "type": "llm",
                "tier": 3,
                "online": nvidia_ok,
                "description": "Orquestación lógica avanzada vía Nvidia NIM (requiere API key)",
            },
            {
                "id": "mai_l0",
                "label": "MAI — FFmpeg Nativo (L0)",
                "type": "animation",
                "tier": 0,
                "online": True,
                "description": "Motor de Animación: efectos nativos FFmpeg, sin dependencias",
            },
            {
                "id": "mai_l1",
                "label": "MAI — Procedural Avanzado (L1)",
                "type": "animation",
                "tier": 1,
                "online": True,
                "description": "Motor de Animación: parallax, glitch, pulse, film burn, etc.",
            },
            {
                "id": "mai_l2",
                "label": "MAI — ComfyUI/IA (L2)",
                "type": "animation",
                "tier": 2,
                "online": comfy_ok,
                "description": "Motor de Animación: Image-to-Video vía ComfyUI (requiere GPU)",
            },
        ]

        body = json.dumps({"engines": engines, "count": len(engines)}, indent=2).encode(
            "utf-8"
        )
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_animations(handler):
    try:
        from core.animation_engine import ANIMATION_EFFECTS, ANIMATION_DEFAULTS

        body = json.dumps(
            {
                "effects": ANIMATION_EFFECTS,
                "defaults": ANIMATION_DEFAULTS,
                "levels": {
                    "0": "FFmpeg Nativo (máximo rendimiento, sin dependencias)",
                    "1": "Procedural Avanzado (efectos complejos via FFmpeg puro)",
                    "2": "ComfyUI / IA (máxima calidad visual, requiere ComfyUI online)",
                },
                "count": len(ANIMATION_EFFECTS),
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_list(handler):
    try:
        BASE_DIR_v = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        videos_dir = os.path.join(BASE_DIR_v, "_videos")
        videos = []
        if os.path.isdir(videos_dir):
            for fname in os.listdir(videos_dir):
                fpath = os.path.join(videos_dir, fname)
                if os.path.isfile(fpath) and fname.endswith(".mp4"):
                    size_mb = os.path.getsize(fpath) / (1024 * 1024)
                    mtime = time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(fpath))
                    )
                    videos.append(
                        {
                            "filename": fname,
                            "job_dir": "",
                            "path": fname,
                            "size_mb": round(size_mb, 2),
                            "date": mtime,
                            "download_url": f"/v1/video/download?file={fname}",
                            "stream_url": f"/v1/video/stream?path={fname}",
                        }
                    )
            for job_dir in sorted(os.listdir(videos_dir)):
                job_path = os.path.join(videos_dir, job_dir)
                if os.path.isdir(job_path):
                    for fname in os.listdir(job_path):
                        if fname.endswith(".mp4"):
                            fpath = os.path.join(job_path, fname)
                            size_mb = os.path.getsize(fpath) / (1024 * 1024)
                            mtime = time.strftime(
                                "%Y-%m-%d %H:%M",
                                time.localtime(os.path.getmtime(fpath)),
                            )
                            videos.append(
                                {
                                    "filename": fname,
                                    "job_dir": job_dir,
                                    "path": f"{job_dir}/{fname}",
                                    "size_mb": round(size_mb, 2),
                                    "date": mtime,
                                    "download_url": f"/v1/video/download?file={job_dir}/{fname}",
                                    "stream_url": f"/v1/video/stream?path={job_dir}/{fname}",
                                }
                            )
        body = json.dumps({"videos": videos, "count": len(videos)}, indent=2).encode(
            "utf-8"
        )
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_stream(handler):
    try:
        from urllib.parse import urlparse, parse_qs

        qs = parse_qs(urlparse(handler.path).query)
        rel_path = qs.get("path", [None])[0]
        if not rel_path or ".." in rel_path:
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(b'{"error":"path invalido"}')
            return
        BASE_DIR_v = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        videos_dir = os.path.join(BASE_DIR_v, "_videos")
        video_path = os.path.join(videos_dir, rel_path.replace("/", os.sep))
        if not os.path.isfile(video_path):
            basename = os.path.basename(rel_path)
            candidate = os.path.join(videos_dir, basename)
            if os.path.isfile(candidate):
                video_path = candidate
            else:
                import glob

                matches = glob.glob(
                    os.path.join(videos_dir, "**", basename), recursive=True
                )
                if matches:
                    video_path = matches[0]
                else:
                    handler.send_response(404)
                    handler.end_headers()
                    handler.wfile.write(b'{"error":"video no encontrado"}')
                    return
        size = os.path.getsize(video_path)
        range_header = handler.headers.get("Range", "")
        if range_header and range_header.startswith("bytes="):
            try:
                parts = range_header[6:].split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else size - 1
                end = min(end, size - 1)
                length = end - start + 1
                handler.send_response(206)
                handler.send_header("Content-Type", "video/mp4")
                handler.send_header("Content-Length", str(length))
                handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                handler.send_header("Accept-Ranges", "bytes")
                handler._send_cors()
                handler.end_headers()
                with open(video_path, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(65536, remaining))
                        if not chunk:
                            break
                        handler.wfile.write(chunk)
                        remaining -= len(chunk)
                return
            except Exception:
                pass
        handler.send_response(200)
        handler.send_header("Content-Type", "video/mp4")
        handler.send_header("Content-Length", str(size))
        handler.send_header("Accept-Ranges", "bytes")
        handler._send_cors()
        handler.end_headers()
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                handler.wfile.write(chunk)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_download(handler):
    try:
        from urllib.parse import urlparse, parse_qs, unquote

        qs = parse_qs(urlparse(handler.path).query)
        filename = qs.get("file", [None])[0]
        if not filename:
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(b'{"error":"Nombre de archivo requerido."}')
            return
        filename = unquote(filename)
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        videos_dir = os.path.join(BASE_DIR, "_videos")
        videos_dir_real = os.path.realpath(videos_dir)
        candidate = os.path.realpath(os.path.join(videos_dir, filename))
        if not candidate.startswith(videos_dir_real + os.sep):
            handler.send_response(403)
            handler.end_headers()
            handler.wfile.write(b'{"error":"Acceso denegado."}')
            return

        video_path = None
        if os.path.isfile(os.path.join(videos_dir_real, filename)):
            video_path = os.path.join(videos_dir_real, filename)
        else:
            for job_dir in os.listdir(videos_dir):
                if os.path.isdir(os.path.join(videos_dir, job_dir)):
                    potential = os.path.join(videos_dir, job_dir, filename)
                    if os.path.isfile(potential):
                        video_path = potential
                        break

        if not video_path:
            handler.send_response(404)
            handler.end_headers()
            handler.wfile.write(b'{"error":"Archivo no encontrado."}')
            return
        size = os.path.getsize(video_path)
        handler.send_response(200)
        handler.send_header("Content-Type", "video/mp4")
        handler.send_header("Content-Length", str(size))
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        handler._send_cors()
        handler.end_headers()
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                handler.wfile.write(chunk)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_thumbnail(handler):
    try:
        from urllib.parse import urlparse, parse_qs

        qs = parse_qs(urlparse(handler.path).query)
        raw_id = qs.get("job_id", ["0"])[0]
        try:
            job_id = int(raw_id)
        except (ValueError, TypeError):
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(b'{"error":"job_id must be a numeric value"}')
            return
        BASE_DIR_v = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        thumb_path = os.path.join(
            BASE_DIR_v, "_videos", "thumb_" + str(job_id) + ".jpg"
        )
        if not os.path.isfile(thumb_path):
            handler.send_response(404)
            handler.end_headers()
            handler.wfile.write(b"{}")
            return
        with open(thumb_path, "rb") as f:
            data = f.read()
        handler.send_response(200)
        handler.send_header("Content-Type", "image/jpeg")
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(data)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(('{"error":"' + str(e) + '"}').encode())


def handle_video_create(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        topic = data.get("topic", "").strip()
        if not topic:
            handler.send_response(400)
            handler.send_header("Content-Type", "application/json")
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(
                json.dumps({"error": "Campo 'topic' requerido."}).encode()
            )
            return
        n_scenes = int(data.get("n_scenes", 6))
        voice_speed = int(data.get("voice_speed", 150))
        voice_id = data.get("voice_id", "").strip()
        style = data.get("style", "documental").strip()
        narration_lang = data.get("narration_lang", "es").strip()
        transitions = bool(data.get("transitions", True))
        subtitles = bool(data.get("subtitles", True))
        resolution = data.get("resolution", "1024x1024").strip()
        title = data.get("title", "").strip()
        bgm_type = data.get("bgm_type", "ninguna").strip()
        quality = data.get("quality", "hd").strip()
        use_lore = bool(data.get("use_lore", True))
        fps = int(data.get("fps", 24))
        scene_duration = int(data.get("scene_duration", 8))
        duration_mode = data.get("duration_mode", "auto").strip()
        bgm_volume = float(data.get("bgm_volume", 0.1))
        codec = data.get("codec", "h264_amf").strip()
        ken_burns = bool(data.get("ken_burns", True))
        intro_card = bool(data.get("intro_card", False))
        color_grade = str(data.get("color_grade", "auto")).strip()
        animation_effect = str(data.get("animation_effect", "auto")).strip()
        _def_anim = 1
        try:
            _bdir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            with open(os.path.join(_bdir, "config.yaml"), "r", encoding="utf-8") as _fc:
                _cfg_c = yaml.safe_load(_fc) or {}
                _def_anim = int(_cfg_c.get("comfyui", {}).get("animation_level", 1))
        except Exception:
            pass
        animation_level = int(data.get("animation_level", _def_anim))

        job_type = data.get("job_type", "tts").strip()
        audio_track_path = data.get("audio_track_path", "").strip()
        lyrics_text = data.get("lyrics_text", "").strip()

        job_id = video_pipeline.add_job(
            topic=topic,
            n_scenes=n_scenes,
            voice_speed=voice_speed,
            voice_id=voice_id,
            style=style,
            narration_lang=narration_lang,
            transitions=transitions,
            resolution=resolution,
            subtitles=subtitles,
            title=title,
            bgm_type=bgm_type,
            quality=quality,
            use_lore=use_lore,
            fps=fps,
            scene_duration=scene_duration,
            duration_mode=duration_mode,
            bgm_volume=bgm_volume,
            codec=codec,
            ken_burns=ken_burns,
            intro_card=intro_card,
            color_grade=color_grade,
            animation_effect=animation_effect,
            animation_level=animation_level,
            job_type=job_type,
            audio_track_path=audio_track_path,
            lyrics_text=lyrics_text,
        )
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps(
                {
                    "ok": True,
                    "job_id": job_id,
                    "message": f"Video encolado (job #{job_id}). Estimado: ~{int(n_scenes * 4.5)} min.",
                    "n_scenes": n_scenes,
                    "style": style,
                    "voice_id": voice_id or "auto",
                    "fps": fps,
                    "codec": codec,
                    "ken_burns": ken_burns,
                    "intro_card": intro_card,
                }
            ).encode()
        )
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_course_generate(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        title = data.get("title", "").strip()
        n_videos = int(data.get("n_videos", 10))
        lang = data.get("lang", "es").strip()
        if not title:
            handler.send_response(400)
            handler.send_header("Content-Type", "application/json")
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(
                json.dumps({"error": "Campo 'title' requerido."}).encode()
            )
            return
        from core.workflow_engine import run_workflow

        job = run_workflow("course", {
            "topic": title,
            "n_videos": n_videos,
            "lang": lang
        }, blocking=False)
        
        ok = job is not None
        body = json.dumps(
            {
                "ok": ok,
                "job_id": job.job_id if ok else None,
                "message": (
                    "Curso encolado en el Motor de Workflows. Revisa los logs."
                    if ok
                    else "Error iniciando workflow del curso."
                ),
            }
        ).encode()
        handler.send_response(200 if ok else 500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_preview_voice(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        body_bytes = handler.rfile.read(length) if length else b"{}"
        data = json.loads(body_bytes.decode("utf-8"))
        voice_id = data.get("voice_id", "")
        text = data.get("text", "Prueba de voz para Gravity Studio.")[:200]
        import tempfile

        tmp = os.path.join(
            tempfile.gettempdir(), f"gravity_preview_{uuid.uuid4().hex}.wav"
        )
        ok = video_pipeline._generate_audio(text, tmp, rate=150, voice_id=voice_id)
        if ok and os.path.isfile(tmp):
            with open(tmp, "rb") as f:
                wav_data = f.read()
            handler.send_response(200)
            handler.send_header("Content-Type", "audio/wav")
            handler.send_header("Content-Length", str(len(wav_data)))
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(wav_data)
        else:
            handler.send_response(500)
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(b'{"error":"TTS fallido"}')

        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except:  # noqa: E722
            pass
    except Exception as e:
        try:
            if "tmp" in locals() and os.path.isfile(tmp):
                os.remove(tmp)
        except:  # noqa: E722
            pass
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(('{"error":"' + str(e) + '"}').encode())


def handle_video_cancel(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        raw_id = data.get("job_id", 0) or data.get("id", 0)
        try:
            job_id = int(raw_id)
        except (ValueError, TypeError):
            handler.send_response(400)
            handler.send_header("Content-Type", "application/json")
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(
                json.dumps(
                    {"error": f"job_id must be a numeric value, got: {raw_id!r}"}
                ).encode()
            )
            return
        ok = video_pipeline.cancel_job(job_id)
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": ok, "job_id": job_id}).encode())
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_video_delete(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        raw_id = data.get("id", 0) or data.get("job_id", 0)
        try:
            job_id = int(raw_id)
        except (ValueError, TypeError):
            handler.send_response(400)
            handler.send_header("Content-Type", "application/json")
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(
                json.dumps(
                    {"error": f"id must be a numeric value, got: {raw_id!r}"}
                ).encode()
            )
            return
        if not job_id:
            handler.send_response(400)
            handler.send_header("Content-Type", "application/json")
            handler._send_cors()
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": "id requerido"}).encode())
            return
        result = video_pipeline.delete_job(job_id)
        handler.send_response(200 if result.get("ok") else 404)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())
