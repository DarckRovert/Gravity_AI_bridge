import json, time, uuid, threading, os, sys, mimetypes, glob, traceback, urllib.parse, urllib.request
from core import provider_manager, security_monitor, image_queue, video_pipeline, deploy_manager, game_server_manager, ai_process_manager, engine_watchdog
from core.audit_log import audit_logger
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data
from core.logger import log
from core.rate_limiter import check_access
from core.reasoning_stripper import ReasoningStripper

class PostRoutesMixin:
    def do_POST(self):

        # /v1/agent/compare — Multi-Agent Orchestrator
        if self.path == "/v1/agent/compare":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                data     = json.loads(self.rfile.read(length)) if length else {}
                messages = data.get("messages", [{"role": "user", "content": data.get("prompt", "")}])
                n_models = int(data.get("n_models", 3))
                mode     = data.get("mode", "parallel")
                from core import multi_agent
                if mode == "vote":
                    result = multi_agent.vote(messages, n_models=n_models)
                    results = [result]
                else:
                    results = multi_agent.compare(messages, n_models=n_models)
                body = json.dumps({"ok": True, "mode": mode, "results": results}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/fabricaweb/deploy
        if self.path == "/v1/fabricaweb/deploy":
            try:
                # Dispara el pipeline sin bloquear al cliente
                threading.Thread(target=deploy_manager.run_deploy_pipeline, daemon=True).start()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "message": "Deploy hacia FabricaWeb iniciado", "job_id": "fabricaweb_deploy"}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/image/generate — Image Lab independiente via Pollinations.ai
        if self.path == "/v1/image/generate":
            try:
                import uuid as _uuid, base64
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                if not prompt:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "prompt requerido"}).encode())
                    return

                width  = int(data.get("width",  1024))
                height = int(data.get("height", 1024))
                model  = data.get("model", "flux")
                negative_prompt = data.get("negative_prompt", "").strip()
                enhance_str = str(data.get("enhance", "true")).lower()
                enhance = enhance_str == "true"
                seed_val = data.get("seed", "")
                seed = None
                if seed_val and str(seed_val).isdigit():
                    seed = int(seed_val)

                BASE    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                lab_dir = os.path.join(BASE, "_integrations", "ImageLab")
                os.makedirs(lab_dir, exist_ok=True)

                filename    = f"lab_{_uuid.uuid4().hex[:12]}.png"
                output_path = os.path.join(lab_dir, filename)

                from tools.pollinations_generator import generate as poll_gen
                try:
                    result = poll_gen(prompt=prompt, output_path=output_path,
                                      width=width, height=height, model=model,
                                      seed=seed, enhance=enhance, negative_prompt=negative_prompt)
                except Exception as e:
                    import traceback
                    print(f"Error calling poll_gen: {traceback.format_exc()}", file=sys.stderr)
                    raise e

                if result.get("success") and os.path.isfile(output_path):
                    with open(output_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    body = json.dumps({
                        "ok":       True,
                        "url":      f"/static/imagelab/{filename}",
                        "filename": filename,
                        "b64":      b64,
                        "width":    width,
                        "height":   height,
                        "model":    model,
                    }).encode("utf-8")
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
            return

        # /v1/watchdog/unlock

        if self.path == "/v1/watchdog/unlock":
            try:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
                self.wfile.write(json.dumps({"ok": True, "message": "Modelo desbloqueado. Auto-switch reactivo."}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/gameserver/start
        if self.path == "/v1/gameserver/start":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                result    = game_server_manager.start(server_id)
                body      = json.dumps(result).encode()
                code      = 200 if result.get("ok", False) else 400
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/gameserver/stop
        if self.path == "/v1/gameserver/stop":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                result    = game_server_manager.stop(server_id)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/gameserver/restart
        if self.path == "/v1/gameserver/restart":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                threading.Thread(target=game_server_manager.restart, args=(server_id,), daemon=True).start()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "note": "Reinicio en proceso...", "server": server_id}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/gameserver/command
        if self.path == "/v1/gameserver/command":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                command   = data.get("command", "")
                result    = game_server_manager.send_command(server_id, command)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        if self.path == "/v1/gameserver/register":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                usr       = data.get("username", "")
                pwd       = data.get("password", "")
                result    = game_server_manager.register_account(server_id, usr, pwd)
                self.send_response(200 if result.get("ok") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/v1/gameserver/expose":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                server_id = data.get("server", "wow_vanilla")
                public_ip = data.get("public_address", "")
                result    = game_server_manager.expose_wan(server_id, public_ip)
                self.send_response(200 if result.get("ok") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/v1/ai/start":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                provider  = data.get("provider", "")
                result    = ai_process_manager.start_engine(provider)
                body      = json.dumps(result).encode("utf-8")
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
            return

        if self.path == "/v1/ai/stop":
            try:
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                provider  = data.get("provider", "")
                result    = ai_process_manager.stop_engine(provider)
                body      = json.dumps(result).encode("utf-8")
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
            return

        # /v1/security/scan — Fuerza un escaneo de seguridad inmediato
        if self.path == "/v1/security/scan":
            try:
                state = security_monitor.force_scan()
                body  = json.dumps(state, indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/queue/add — Añadir trabajo a la cola de imágenes
        if self.path == "/v1/queue/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                if not prompt:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error":"prompt requerido"}')
                    return
                job_id = image_queue.add_job(
                    prompt      = prompt,
                    performance = data.get("performance", "Speed"),
                    width       = int(data.get("width", 1024)),
                    height      = int(data.get("height", 1024)),
                )
                body = json.dumps({"ok": True, "job_id": job_id}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/deploy — Inicia el pipeline build + netlify
        if self.path == "/v1/deploy":
            try:
                length       = int(self.headers.get("Content-Length", 0))
                data         = json.loads(self.rfile.read(length)) if length else {}
                project_path = data.get("project_path")
                result       = deploy_manager.start_deploy(project_path)
                body         = json.dumps(result).encode()
                code         = 200 if result.get("started") else 400
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/generate — Generar imagen via Fooocus desde API REST
        if self.path == "/v1/generate":
            try:
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


        # /v1/video/create — Encola un nuevo trabajo de generación de video
        if self.path == "/v1/video/create":
            try:
                length     = int(self.headers.get("Content-Length", 0))
                data       = json.loads(self.rfile.read(length)) if length else {}
                topic      = data.get("topic", "").strip()
                if not topic:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Campo 'topic' requerido."}).encode())
                    return
                n_scenes      = int(data.get("n_scenes", 6))
                voice_speed   = int(data.get("voice_speed", 150))
                voice_id      = data.get("voice_id", "").strip()
                style         = data.get("style", "documental").strip()
                narration_lang= data.get("narration_lang", "es").strip()
                transitions   = bool(data.get("transitions", True))
                job_id        = video_pipeline.add_job(
                    topic          = topic,
                    n_scenes       = n_scenes,
                    voice_speed    = voice_speed,
                    voice_id       = voice_id,
                    style          = style,
                    narration_lang = narration_lang,
                    transitions    = transitions,
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok":       True,
                    "job_id":   job_id,
                    "message":  f"Video encolado (job #{job_id}). El proceso toma ~{n_scenes * 5} min en CPU.",
                    "n_scenes": n_scenes,
                    "style":    style,
                    "voice_id": voice_id or "auto",
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return


        # /v1/video/cancel — Cancela un trabajo de video pendiente
        if self.path == "/v1/video/cancel":
            try:
                length  = int(self.headers.get("Content-Length", 0))
                data    = json.loads(self.rfile.read(length)) if length else {}
                job_id  = int(data.get("job_id", 0))
                ok      = video_pipeline.cancel_job(job_id)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/audit/rotate — Fuerza rotación inmediata del audit log activo
        if self.path == "/v1/audit/rotate":
            try:
                _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                import time as _time, os as _os
                bak = audit_logger.log_path.replace(".jsonl", f".bak.{int(_time.time())}.jsonl")
                if _os.path.isfile(audit_logger.log_path):
                    _os.rename(audit_logger.log_path, bak)
                    audit_logger._line_count = 0
                    # Mantener max 3 backups
                    _base_log_dir  = _os.path.dirname(audit_logger.log_path)
                    _base_log_name = _os.path.basename(audit_logger.log_path).replace(".jsonl", "")
                    _baks = sorted([f for f in _os.listdir(_base_log_dir) if f.startswith(_base_log_name + ".bak.")])
                    while len(_baks) > 3:
                        _os.remove(_os.path.join(_base_log_dir, _baks.pop(0)))
                    msg = f"Log rotado → {_os.path.basename(bak)}"
                else:
                    msg = "No hay log activo para rotar."
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "message": msg}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/rag/toggle — Activa o desactiva la inyección RAG en el flujo de chat
        if self.path == "/v1/rag/toggle":
            try:
                length  = int(self.headers.get("Content-Length", 0))
                data    = json.loads(self.rfile.read(length)) if length else {}
                enabled = data.get("enabled", None)
                _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                settings_path = os.path.join(_base_dir, "_settings.json")
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                except Exception:
                    settings = {}
                if enabled is None:
                    # Toggle: invierte el estado actual
                    enabled = not settings.get("rag_enabled", False)
                settings["rag_enabled"] = bool(enabled)
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True,
                    "rag_enabled": settings["rag_enabled"],
                    "message": f"RAG {'activado' if settings['rag_enabled'] else 'desactivado'} en flujo de chat."
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return


        # /v1/tools/run — Code Runner (Python/Bash)
        if self.path == "/v1/tools/run":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                code   = data.get("code", "").strip()
                lang   = data.get("lang", "python").lower()
                if not code:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "code requerido"}).encode())
                    return
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sys.path.insert(0, os.path.join(BASE, "tools"))
                from code_runner import CodeRunner
                runner = CodeRunner()
                result = runner.execute(code=code, language=lang, timeout=15)
                body = json.dumps({"ok": True, "stdout": result.stdout or "", "stderr": result.stderr or "", "exit_code": result.exit_code or 0}).encode("utf-8")
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
            return

        # /v1/tools/search — Web Search DuckDuckGo
        if self.path == "/v1/tools/search":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                query  = data.get("query", "").strip()
                if not query:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "query requerido"}).encode())
                    return
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sys.path.insert(0, os.path.join(BASE, "tools"))
                from web_search import WebSearch
                searcher = WebSearch()
                r = searcher.execute(query=query)
                # Parse structured results from stdout
                import re as _re
                lines = (r.stdout or "").split("\n")
                results = []
                cur = {}
                for line in lines:
                    if line and line[0].isdigit() and ". **" in line:
                        if cur: results.append(cur)
                        cur = {"title": _re.sub(r"^\d+\.\s*\*\*(.+)\*\*", r"\1", line).strip()}
                    elif "URL:" in line and cur:
                        cur["url"] = line.replace("URL:", "").strip()
                    elif line.strip() and cur and "title" in cur and "url" in cur:
                        cur.setdefault("snippet", line.strip())
                if cur: results.append(cur)
                if not results:
                    results = [{"title": "Resultado", "url": "", "snippet": r.stdout or "Sin resultados"}]
                body = json.dumps({"ok": r.success, "results": results, "query": query}).encode("utf-8")
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
            return

        # /v1/tools/git — Git Tool operations
        if self.path == "/v1/tools/git":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                cmd    = data.get("cmd", "status").strip()
                cwd    = data.get("cwd", "").strip() or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sys.path.insert(0, os.path.join(BASE, "tools"))
                from git_tool import GitTool
                import subprocess as _sp
                git_cmds = {"status": ["git","status","--short"], "log": ["git","log","--oneline","-15"], "diff": ["git","diff","HEAD"], "branch": ["git","branch","-a"]}
                git_cmd = git_cmds.get(cmd, None)
                if git_cmd:
                    _r = _sp.run(git_cmd, capture_output=True, text=True, timeout=10, cwd=cwd)
                    output = _r.stdout[:5000] + (_r.stderr[:1000] if _r.stderr else "")
                else:
                    output = f"Comando '{cmd}' no soportado. Opciones: status, log, diff, branch"
                body = json.dumps({"ok": True, "output": output, "error": "", "cmd": cmd}).encode("utf-8")
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
            return

        # /v1/tools/grep — Grep pattern search
        if self.path == "/v1/tools/grep":
            try:
                length  = int(self.headers.get("Content-Length", 0))
                data    = json.loads(self.rfile.read(length)) if length else {}
                pattern = data.get("pattern", "").strip()
                path_g  = data.get("path", "").strip()
                if not pattern:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "pattern requerido"}).encode())
                    return
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sys.path.insert(0, os.path.join(BASE, "tools"))
                from grep_tool import GrepTool
                grepper = GrepTool()
                r = grepper.execute(pattern=pattern, path=path_g or BASE)
                lines = (r.stdout or "").split("\n") if r.success else []
                results = [{"line": l} for l in lines if l.strip()]
                body = json.dumps({"ok": r.success, "matches": results, "count": len(results), "raw": r.stdout or r.stderr or ""}).encode("utf-8")
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
            return

        # /v1/security/kill — Kill suspicious process
        if self.path == "/v1/security/kill":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                pid    = int(data.get("pid", 0))
                if not pid:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "pid requerido"}).encode())
                    return
                import signal as _signal
                try:
                    import psutil
                    p = psutil.Process(pid)
                    pname = p.name()
                    p.terminate()
                    body = json.dumps({"ok": True, "message": f"Proceso {pname} (PID {pid}) terminado.", "pid": pid}).encode()
                except ImportError:
                    import subprocess, sys
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                    body = json.dumps({"ok": True, "message": f"Kill enviado a PID {pid}.", "pid": pid}).encode()
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
            return

        # /v1/gameserver/backup — Backup server DB
        if self.path == "/v1/gameserver/backup":
            try:
                import shutil, time as t
                length    = int(self.headers.get("Content-Length", 0))
                data      = json.loads(self.rfile.read(length)) if length else {}
                BASE      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                backup_dir = os.path.join(BASE, "_archivo", "server_backups")
                os.makedirs(backup_dir, exist_ok=True)
                ts = int(t.time())
                # Backup del SQLite del servidor si existe
                gs_db = os.path.join(BASE, "_image_queue.sqlite")
                if os.path.isfile(gs_db):
                    dst = os.path.join(backup_dir, f"server_backup_{ts}.zip")
                    shutil.copy2(gs_db, os.path.join(backup_dir, f"backup_{ts}.sqlite"))
                    msg = f"Backup creado: backup_{ts}.sqlite en _archivo/server_backups/"
                else:
                    msg = f"Backup dir listo: {backup_dir} (no hay DB de servidor local para copiar)"
                body = json.dumps({"ok": True, "message": msg, "timestamp": ts}).encode()
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
                    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    kb_data, _ = data_guardian.load_knowledge(os.path.join(_base_dir, "_knowledge.json"))
                    _sys_prompt = (
                        "Eres Gravity AI V10.1, Auditor Senior. "
                        "PROTOCOLO: Lógica interna en inglés. Salida final en español estrictamente. "
                        "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa."
                    )
                    if kb_data and "persistent_rules" in kb_data and kb_data["persistent_rules"]:
                        _sys_prompt += "\n\nCONOCIMIENTO CRÍTICO:\n" + "\n".join(kb_data["persistent_rules"])
                    messages.insert(0, {"role": "system", "content": _sys_prompt})
                except Exception as e:
                    log.error(f"Error cargando personalidad para el bridge: {e}")

            # ── Inyección RAG (si está activada en _settings.json) ──
            try:
                _base_dir_rag = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                _settings_path = os.path.join(_base_dir_rag, "_settings.json")
                with open(_settings_path, "r", encoding="utf-8") as _sf:
                    _rag_enabled = json.load(_sf).get("rag_enabled", False)
                if _rag_enabled:
                    # Extraer la última query del usuario para la búsqueda
                    _user_msgs = [m for m in messages if m.get("role") == "user"]
                    if _user_msgs:
                        _query = _user_msgs[-1].get("content", "")[:500]
                        from rag.retriever import RAGRetriever
                        _rag_context = RAGRetriever.retrieve_as_context(_query, top_k=4)
                        if _rag_context:
                            # Añadir como mensaje system adicional (no sobreescribe el de personalidad)
                            messages.append({"role": "system", "content": _rag_context})
                            log.info(f"[RAG] Contexto inyectado ({len(_rag_context)} chars) para query: {_query[:60]}...")
            except Exception as _rag_err:
                log.debug(f"[RAG] Skip — {_rag_err}")  # Silencioso si RAG no está disponible

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
                    except Exception as write_err:
                        log.debug(f"[Streaming] Socket cerrado durante escritura: {write_err}")
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
            try:
                body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass
