import json, time, uuid, threading, os, sys, mimetypes, glob, traceback, yaml, urllib.parse, urllib.request, subprocess, psutil
from core import provider_manager, security_monitor, image_queue, video_pipeline, deploy_manager, game_server_manager, ai_process_manager, engine_watchdog
from core.audit_log import audit_logger
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data
from core.logger import log
from core.rate_limiter import check_access
from core.reasoning_stripper import ReasoningStripper

class PostRoutesMixin:
    def do_POST(self):
        print('DEBUG do_POST path:', repr(self.path))
        
        if not self._check_rate():
            return

        # /v1/youtube/analyzer/process — Analizar video de YouTube
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
                    return

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
            return


        # /v1/bounties/action — Marcar trabajo como aplicado o descartado
        if self.path == "/v1/bounties/action":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                url = data.get("url", "").strip()
                action = data.get("action", "").strip()
                
                if not url or not action:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "url y action son requeridos"}).encode())
                    return
                    
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                actions_path = os.path.join(BASE_DIR, "inputs", ".bounty_actions.json")
                os.makedirs(os.path.dirname(actions_path), exist_ok=True)
                
                actions = {}
                if os.path.exists(actions_path):
                    with open(actions_path, "r", encoding="utf-8") as f:
                        try: actions = json.load(f)
                        except: pass
                        
                actions[url] = action
                
                with open(actions_path, "w", encoding="utf-8") as f:
                    json.dump(actions, f)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "action": action}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/bounties/profile — Guardar el perfil del freelancer
        if self.path == "/v1/bounties/profile":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                profile = data.get("profile", "").strip()
                
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                settings_path = os.path.join(BASE_DIR, "_settings.json")
                
                settings = {}
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                        
                settings["bounty_profile"] = profile
                
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/infiltrator/start — Iniciar motor de infiltración (Playwright Stealth)
        if self.path == "/v1/infiltrator/start":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                target_url = data.get("url", "").strip()
                if not target_url: target_url = "https://www.google.com"
                
                from core import infiltrator
                ok, msg = infiltrator.start_job(target_url)
                
                self.send_response(200 if ok else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
            
        # /v1/infiltrator/stop — Detener motor de infiltración
        if self.path == "/v1/infiltrator/stop":
            try:
                from core import infiltrator
                ok, msg = infiltrator.stop_job()
                self.send_response(200 if ok else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/infiltrator/queue_bid — Encolar una oferta automática de Freelancer
        if self.path == "/v1/infiltrator/queue_bid":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                url = data.get("url", "")
                proposal = data.get("proposal", "")
                
                from core import infiltrator
                ok, msg = infiltrator.manager.queue_task({"type": "freelancer_bid", "url": url, "proposal": proposal})
                
                self.send_response(200 if ok else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        # /v1/factory/generate — Fábrica de Software
        if self.path == "/v1/factory/generate":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                
                if not prompt:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Prompt vacío"}).encode())
                    return
                    
                import re as _re, os as _os, zipfile as _zipfile, datetime as _datetime
                from core import provider_manager as _fpm, config_manager as _fcm
                
                system_prompt = (
                    "Eres un Ingeniero de Software Senior Autónomo.\n"
                    "El usuario te dará un requerimiento para un script, bot o aplicación.\n"
                    "Debes escribir el código necesario para que funcione.\n"
                    "REGLAS:\n"
                    "1. Por cada archivo que crees, debes incluir primero el nombre del archivo en negrita de esta forma exacta: **Archivo:** nombre_del_archivo.ext\n"
                    "2. Inmediatamente después, incluye el bloque de código Markdown correspondiente.\n"
                    "3. DEBES incluir siempre un **Archivo:** README.md con las instrucciones de uso para el cliente.\n"
                    "4. Si es necesario, incluye un **Archivo:** requirements.txt o package.json.\n"
                    "No des explicaciones fuera de los bloques de código o el README."
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                config = _fcm.load_config()
                provider_name = config.get("model.default_provider", "LM Studio")
                plugin = _fpm.get_plugin(provider_name)
                if not plugin:
                    raise Exception(f"No hay proveedor de IA disponible ({provider_name}).")
                    
                chunks = list(plugin.chat_stream(messages, "auto", {}))
                response_text = "".join(chunks)
                
                response_text = _re.sub(r'<think>.*?</think>', '', response_text, flags=_re.DOTALL).strip()
                if '<think>' in response_text:
                    response_text = _re.sub(r'<think>.*', '', response_text, flags=_re.DOTALL).strip()
                    
                prefixes_to_strip = [
                    "Aquí tienes", "Aquí está", "Claro, aquí", "Entendido.", "¡Por supuesto!"
                ]
                for prefix in prefixes_to_strip:
                    if response_text.lower().startswith(prefix.lower()):
                        lines = response_text.split('\n')
                        while lines and (lines[0].lower().startswith(prefix.lower()) or lines[0].strip() == ""):
                            lines.pop(0)
                        response_text = '\n'.join(lines).strip()
                
                _BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
                entregables_dir = _os.path.join(_BASE_DIR, "_entregables")
                _os.makedirs(entregables_dir, exist_ok=True)
                
                # Encontrar bloques: **Archivo:** nombre \n ```lang \n codigo \n ```
                pattern = r'\*\*Archivo:\*\*\s*([^\n`]+).*?```\w*\n(.*?)```'
                matches = list(_re.finditer(pattern, response_text, _re.DOTALL))
                
                folder_name = "entregable_" + _datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                project_path = _os.path.join(entregables_dir, folder_name)
                _os.makedirs(project_path, exist_ok=True)
                
                files_created = 0
                for match in matches:
                    filename = match.group(1).strip()
                    code = match.group(2)
                    filename = _os.path.basename(filename) # Evitar path traversal
                    file_path = _os.path.join(project_path, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    files_created += 1
                    
                with open(_os.path.join(project_path, "RAW_RESPONSE.md"), "w", encoding="utf-8") as f:
                    f.write(response_text)
                    
                zip_filename = folder_name + ".zip"
                zip_path = _os.path.join(entregables_dir, zip_filename)
                with _zipfile.ZipFile(zip_path, 'w', _zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in _os.walk(project_path):
                        for file in files:
                            abs_path = _os.path.join(root, file)
                            rel_path = _os.path.relpath(abs_path, project_path)
                            zipf.write(abs_path, rel_path)
                            
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": True, 
                    "filename": zip_filename,
                    "files_created": files_created
                }).encode())
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/scheduler/trigger — Encolar un video ahora (override manual del scheduler)
        if self.path == "/v1/scheduler/trigger":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                from core import content_scheduler
                result = content_scheduler.queue_now(
                    niche_id = data.get("niche_id"),
                    topic    = data.get("topic"),
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
            return

        # /v1/scheduler/topic/add — Agregar un topic nuevo a un niche
        if self.path == "/v1/scheduler/topic/add":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                data     = json.loads(self.rfile.read(length)) if length else {}
                niche_id = data.get("niche_id", "").strip()
                topic    = data.get("topic", "").strip()
                if not niche_id or not topic:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "niche_id y topic son requeridos"}).encode())
                    return
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
            return

        # /v1/youtube/auth/exchange — Intercambiar código OAuth por refresh_token
        if self.path == "/v1/youtube/auth/exchange":
            from api.routes.handlers.revenue_handler import handle_youtube_auth_exchange
            handle_youtube_auth_exchange(self)
            return

        # /v1/youtube/upload — Upload manual de un job completado a YouTube
        if self.path == "/v1/youtube/upload":
            from api.routes.handlers.revenue_handler import handle_youtube_upload
            handle_youtube_upload(self)
            return

        # /v1/v2v/start — Arrancar motor VTuber V2V
        if self.path == "/v1/v2v/start":
            from api.routes.handlers.v2v_handler import handle_v2v_start
            handle_v2v_start(self)
            return

        # /v1/v2v/stop — Detener motor VTuber V2V
        if self.path == "/v1/v2v/stop":
            from api.routes.handlers.v2v_handler import handle_v2v_stop
            handle_v2v_stop(self)
            return


        # /v1/keys — Guardar API key cifrada en keystore
        if self.path == "/v1/keys":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                data     = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "").strip().lower()
                api_key  = data.get("api_key", "").strip()
                if not provider or not api_key:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "provider y api_key son requeridos"}).encode())
                    return
                from core.key_manager import KeyManager
                KeyManager.set_key(provider, api_key)
                body = json.dumps({"ok": True, "provider": provider, "masked": KeyManager.mask(provider)}).encode()
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

        # /v1/cost/limit — Actualizar límite diario de gasto
        if self.path == "/v1/cost/limit":
            from api.routes.handlers.revenue_handler import handle_cost_limit
            handle_cost_limit(self)
            return


        # /v1/rag/ingest — Ingestión de archivos PDF/TXT al índice RAG
        if self.path == "/v1/rag/ingest":
            try:
                import cgi, io
                content_type = self.headers.get("Content-Type", "")
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                # Parse multipart/form-data
                environ = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(length)}
                form = cgi.FieldStorage(fp=io.BytesIO(body), environ=environ, keep_blank_values=True)
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sources_dir = os.path.join(BASE_DIR, "_rag_sources")
                os.makedirs(sources_dir, exist_ok=True)
                indexed = 0
                for field_name in form.keys():
                    items = form[field_name]
                    if not isinstance(items, list): items = [items]
                    for item in items:
                        if item.filename:
                            safe_name = os.path.basename(item.filename)
                            dest = os.path.join(sources_dir, safe_name)
                            with open(dest, "wb") as f:
                                f.write(item.file.read())
                            indexed += 1
                # Trigger background re-indexing if rag_engine is available
                try:
                    from core.rag_engine import ingest_directory
                    import threading
                    t = threading.Thread(target=ingest_directory, args=(sources_dir,), daemon=True)
                    t.start()
                except Exception:
                    pass
                body_resp = json.dumps({"ok": True, "indexed": indexed, "message": f"{indexed} archivo(s) guardados. Re-indexación iniciada."}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body_resp)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
            return

        # /v1/rag/toggle — Activar o desactivar RAG en _settings.json
        if self.path == "/v1/rag/toggle":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                settings_path = os.path.join(BASE_DIR, "_settings.json")
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                # Si viene valor explícito lo usa; si no, hace toggle
                if "enabled" in data:
                    settings["rag_enabled"] = bool(data["enabled"])
                else:
                    settings["rag_enabled"] = not settings.get("rag_enabled", True)
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                body = json.dumps({"ok": True, "rag_enabled": settings["rag_enabled"]}).encode()
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

        # /v1/model/lock — Bloquear un modelo y proveedor específico en _settings.json
        if self.path == "/v1/model/lock":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "").strip()
                model    = data.get("model", "").strip()
                lock     = bool(data.get("lock", True))

                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                settings_path = os.path.join(BASE_DIR, "_settings.json")
                
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                if not lock:
                    settings["model_locked"] = False
                    settings.pop("locked_provider", None)
                    settings.pop("locked_model", None)
                else:
                    if not provider or not model:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self._send_cors()
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "provider y model son requeridos para bloquear"}).encode())
                        return
                    settings["model_locked"] = True
                    settings["locked_provider"] = provider
                    settings["locked_model"] = model

                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                
                body = json.dumps({
                    "ok": True, 
                    "model_locked": settings["model_locked"],
                    "locked_provider": settings.get("locked_provider"),
                    "locked_model": settings.get("locked_model")
                }).encode()
                
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
            return

        # /v1/universal/config — Guardar configuración del proveedor Universal AI
        if self.path == "/v1/universal/config":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                data     = json.loads(self.rfile.read(length)) if length else {}
                base_url = data.get("universal_base_url", "").strip()
                model    = data.get("universal_model", "").strip()
                
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            return

        # /v1/audit/rotate — Archivar el audit log actual y empezar uno limpio
        if self.path == "/v1/audit/rotate":
            try:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
                    body = json.dumps({"ok": True, "archived_to": archive_path, "size_kb": size_kb}).encode()
                else:
                    body = json.dumps({"ok": True, "note": "No habia audit log que rotar"}).encode()
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

        # /v1/security/scan — Disparar escaneo activo del monitor de seguridad
        if self.path == "/v1/security/scan":
            try:
                # Ejecutar escaneo completo forzado de manera sincrona para que
                # el frontend reciba y vea los resultados inmediatos.
                if hasattr(security_monitor, "force_scan"):
                    state = security_monitor.force_scan()
                else:
                    state = security_monitor.get_state() if hasattr(security_monitor, "get_state") else {}
                
                body = json.dumps({"ok": True, "message": "Escaneo de seguridad completado", "state": state}).encode()
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


        if self.path == "/v1/agent/compare":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                data     = json.loads(self.rfile.read(length)) if length else {}
                messages = data.get("messages", [{"role": "user", "content": data.get("prompt", "")}])
                n_models = int(data.get("n_models", 3))
                mode     = data.get("mode", "parallel")
                from core import multi_agent
                if mode in ("vote", "consensus"):
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
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                project_path = data.get("project_path")
                
                # Dispara el pipeline (deploy_manager.start_deploy ya maneja el hilo interno)
                result = deploy_manager.start_deploy(project_path)
                
                self.send_response(200 if result.get("started") else 400)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"ok": result.get("started", False), "message": result.get("reason", "Deploy hacia FabricaWeb iniciado"), "job_id": "fabricaweb_deploy"}).encode())
            except Exception as e:
                self.send_response(500)
                self._send_cors()
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
                            result["error"] = result.get("error", "Error generando con Fooocus")
                            result["success"] = False
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                else:
                    from tools.pollinations_generator import generate as poll_gen
                    try:
                        result = poll_gen(prompt=prompt, output_path=output_path,
                                          width=width, height=height, model=model,
                                          seed=seed, enhance=enhance, negative_prompt=negative_prompt)
                    except Exception as e:
                        log.error(f"[ImageLab] Error en poll_gen: {traceback.format_exc()}")
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
            from api.routes.handlers.gameserver_handler import handle_gameserver_start
            handle_gameserver_start(self)
            return

        # /v1/gameserver/stop
        if self.path == "/v1/gameserver/stop":
            from api.routes.handlers.gameserver_handler import handle_gameserver_stop
            handle_gameserver_stop(self)
            return

        # /v1/gameserver/restart
        if self.path == "/v1/gameserver/restart":
            from api.routes.handlers.gameserver_handler import handle_gameserver_restart
            handle_gameserver_restart(self)
            return

        # /v1/gameserver/command
        if self.path == "/v1/gameserver/command":
            from api.routes.handlers.gameserver_handler import handle_gameserver_command
            handle_gameserver_command(self)
            return

        if self.path == "/v1/gameserver/register":
            from api.routes.handlers.gameserver_handler import handle_gameserver_register
            handle_gameserver_register(self)
            return

        if self.path == "/v1/gameserver/expose":
            from api.routes.handlers.gameserver_handler import handle_gameserver_expose
            handle_gameserver_expose(self)
            return

        # ── Journalist Autonomous OSINT ─────────────────────────────────────────────
        if self.path == "/v1/journalist/start":
            from api.routes.handlers.journalist_handler import handle_journalist_start
            handle_journalist_start(self)
            return

        if self.path == "/v1/journalist/stop":
            from api.routes.handlers.journalist_handler import handle_journalist_stop
            handle_journalist_stop(self)
            return

        if self.path == "/v1/journalist/portal/start":
            from api.routes.handlers.journalist_handler import handle_journalist_portal_start
            handle_journalist_portal_start(self)
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



        # /v1/queue/add — Añadir trabajo a la cola de imágenes
        if self.path == "/v1/queue/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                prompt = data.get("prompt", "").strip()
                if not prompt:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
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
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/queue/cancel — Cancela un job de imagen por ID
        if self.path.startswith("/v1/queue/cancel"):
            try:
                from urllib.parse import parse_qs, urlparse
                qs     = parse_qs(urlparse(self.path).query)
                job_id = qs.get("id", [None])[0]
                if not job_id:
                    length = int(self.headers.get("Content-Length", 0))
                    data   = json.loads(self.rfile.read(length)) if length else {}
                    job_id = data.get("id") or data.get("job_id")
                if not job_id:
                    self.send_response(400); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                    self.wfile.write(b'{"error":"id requerido"}'); return
                ok = image_queue.cancel_job(job_id) if hasattr(image_queue, "cancel_job") else False
                body = json.dumps({"ok": ok, "job_id": job_id, "message": "Cancelado" if ok else "Job no encontrado o ya completado"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/queue/delete — Elimina un job por ID
        if self.path.startswith("/v1/queue/delete"):
            try:
                from urllib.parse import parse_qs, urlparse
                qs     = parse_qs(urlparse(self.path).query)
                job_id = qs.get("id", [None])[0]
                if not job_id:
                    length = int(self.headers.get("Content-Length", 0))
                    data   = json.loads(self.rfile.read(length)) if length else {}
                    job_id = data.get("id") or data.get("job_id")
                if not job_id:
                    self.send_response(400); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                    self.wfile.write(b'{"error":"id requerido"}'); return
                from core.image_queue import _get_conn, _notify_update
                with _get_conn() as conn:
                    cur = conn.execute("DELETE FROM image_jobs WHERE id=?", (job_id,))
                    ok = cur.rowcount > 0
                _notify_update()
                body = json.dumps({"ok": ok, "job_id": job_id, "message": "Eliminado" if ok else "Job no encontrado"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/queue/clear_history — Limpia todo el historial
        if self.path == "/v1/queue/clear_history":
            try:
                from core.image_queue import _get_conn, _notify_update
                with _get_conn() as conn:
                    cur = conn.execute("DELETE FROM image_jobs WHERE status IN ('done', 'failed', 'cancelled')")
                    ok = cur.rowcount > 0
                _notify_update()
                body = json.dumps({"ok": True, "message": "Historial limpiado"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

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




        # /v1/video/create — Encola un nuevo trabajo de generación de video
        if self.path == "/v1/video/create":
            from api.routes.handlers.video_handler import handle_video_create
            handle_video_create(self)
            return

        # /v1/course/generate — Generar un temario (Playlist) de N videos e insertarlo en el scheduler
        if self.path == "/v1/course/generate":
            from api.routes.handlers.video_handler import handle_course_generate
            handle_course_generate(self)
            return

        # /v1/video/preview_voice — TTS preview de voz seleccionada
        if self.path == '/v1/video/preview_voice':
            from api.routes.handlers.video_handler import handle_video_preview_voice
            handle_video_preview_voice(self)
            return

        # /v1/video/cancel — Cancela un trabajo de video pendiente
        if self.path == "/v1/video/cancel":
            from api.routes.handlers.video_handler import handle_video_cancel
            handle_video_cancel(self)
            return

        # /v1/video/delete — Elimina un job y sus archivos físicos
        if self.path == "/v1/video/delete":
            from api.routes.handlers.video_handler import handle_video_delete
            handle_video_delete(self)
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
                    self.send_header("Content-Type", "application/json")
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
                    # psutil ya importado
                    p = psutil.Process(pid)
                    pname = p.name()
                    p.terminate()
                    body = json.dumps({"ok": True, "message": f"Proceso {pname} (PID {pid}) terminado.", "pid": pid}).encode()
                except ImportError:
                    # subprocess ya importado
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
            from api.routes.handlers.gameserver_handler import handle_gameserver_backup
            handle_gameserver_backup(self)
            return


        # /v1/sessions/spawn — Crea un nuevo subproceso ask_deepseek.py --session <id>
        if self.path == "/v1/sessions/spawn":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                s_id   = data.get("session_id", "").strip()
                s_role = data.get("role", "").strip() or None
                
                from core.session_runner import SessionSpawner
                # Spawn session as subprocess
                spawner = SessionSpawner()
                spawner.spawn(session_id=s_id, work_data={}, role=s_role)
                
                body = json.dumps({"ok": True, "session_id": s_id, "message": f"Worker para sesión {s_id} levantado."}).encode("utf-8")
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

        # /v1/sessions/kill — Termina un subproceso de sesión
        if self.path == "/v1/sessions/kill":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                s_id   = data.get("session_id", "").strip()
                
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
            return

        # /v1/hitl/approve — Aprobar una acción pendiente
        if self.path == "/v1/hitl/approve":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                aid    = (data.get("approval_id") or data.get("request_id") or "").strip()
                from core.hitl_manager import approve
                ok = approve(aid)
                body = json.dumps({"ok": ok, "approval_id": aid,
                                   "message": "Aprobado" if ok else "ID no encontrado"}).encode()
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

        # /v1/hitl/reject — Rechazar una acción pendiente
        if self.path == "/v1/hitl/reject":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                aid    = (data.get("approval_id") or data.get("request_id") or "").strip()
                reason = data.get("reason", "").strip()
                from core.hitl_manager import reject
                ok = reject(aid, reason)
                body = json.dumps({"ok": ok, "approval_id": aid,
                                   "message": "Rechazado" if ok else "ID no encontrado"}).encode()
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

        # /v1/tools/scrape — Firecrawl / Fallback HTML scraper
        if self.path == "/v1/tools/scrape":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                url    = data.get("url", "").strip()
                if not url:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "url requerida"}).encode())
                    return
                # Leer api_key desde config.yaml
                api_key = ""
                try:
                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    # BASE_DIR ya calculado
                    with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    api_key = cfg.get("firecrawl_api_key", "") or ""
                except Exception:
                    pass
                from core.firecrawl_scraper import scrape_url
                result = scrape_url(url, api_key)
                body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
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
            return

        # ── /v1/gravity/chat — Chat con conciencia sistémica completa ─────────
        if self.path == "/v1/gravity/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                messages_in = data.get("messages", [])
                stream_mode = data.get("stream", True)

                user_msg = ""
                user_msg_idx = -1
                for i in range(len(messages_in)-1, -1, -1):
                    if messages_in[i].get("role") == "user":
                        user_msg = messages_in[i].get("content", "")
                        user_msg_idx = i
                        break

                # Inyección de scraping web en tiempo real para el Chat
                if user_msg_idx != -1:
                    import re
                    urls = re.findall(r'(https?://[^\s)\]]+)', user_msg)
                    if urls:
                        try:
                            from core.firecrawl_scraper import scrape_url
                            _base_dir_scrape = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                            api_key = ""
                            try:
                                with open(os.path.join(_base_dir_scrape, "config.yaml"), "r", encoding="utf-8") as f:
                                    api_key = yaml.safe_load(f).get("firecrawl_api_key", "")
                            except: pass
                            
                            for url in urls[:1]:
                                scrape_res = scrape_url(url, api_key=api_key)
                                if scrape_res.get("ok"):
                                    scraped_text = scrape_res.get("content", "")[:6000]
                                    messages_in[user_msg_idx]["content"] = user_msg.replace(
                                        url, f"[{url} - CONTENIDO WEB EXTRAÍDO:\n{scraped_text}\n]"
                                    )
                                    user_msg = messages_in[user_msg_idx]["content"]
                        except Exception as e:
                            pass

                # Detectar comandos del sistema
                from core.gravity_brain import parse_chat_commands, execute_system_command, build_gravity_system_prompt
                from core import data_guardian

                cmd_info = parse_chat_commands(user_msg)
                if cmd_info:
                    # Ejecutar el comando del sistema
                    cmd_result = execute_system_command(cmd_info)
                    feedback = cmd_info.get("user_feedback", "")
                    result_text = cmd_result.get("result_text", "Sin resultado")
                    ok = cmd_result.get("ok", False)
                    icon = "✓" if ok else "✗"

                    # Construir respuesta con resultado del comando
                    response_content = (
                        f"**{icon} {feedback}**\n\n"
                        f"Acción ejecutada: `{cmd_info.get('api_action', cmd_info.get('command'))}`\n\n"
                        f"```\n{result_text}\n```"
                    )

                    if stream_mode:
                        chat_id = f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}"
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self._send_cors()
                        self.end_headers()
                        chunk = {
                            "id": chat_id, "object": "chat.completion.chunk", "model": "gravity-brain-v16",
                            "choices": [{"index": 0, "delta": {"content": response_content}, "finish_reason": None}]
                        }
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                        final = {
                            "id": chat_id, "object": "chat.completion.chunk", "model": "gravity-brain-v16",
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                        }
                        self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8"))
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    else:
                        body = json.dumps({
                            "id": f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}",
                            "object": "chat.completion",
                            "model": "gravity-brain-v16",
                            "choices": [{"index": 0, "message": {"role": "assistant", "content": response_content}, "finish_reason": "stop"}],
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                        }).encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self._send_cors()
                        self.end_headers()
                        self.wfile.write(body)
                    return

                # No es un comando — chat normal con conciencia sistémica inyectada
                _base_dir_brain = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                kb_data_brain = {}
                try:
                    kb_data_brain, _ = data_guardian.load_knowledge(
                        os.path.join(_base_dir_brain, "_knowledge.json")
                    )
                except Exception:
                    pass

                extra_rules = kb_data_brain.get("persistent_rules", [])
                system_prompt = build_gravity_system_prompt(extra_rules=extra_rules if extra_rules else None)

                # Insertar system prompt con conciencia sistémica
                messages_out = [m for m in messages_in if m.get("role") != "system"]
                messages_out.insert(0, {"role": "system", "content": system_prompt})

                # Inyección RAG si está activa
                try:
                    settings_brain = {}
                    sp = os.path.join(_base_dir_brain, "_settings.json")
                    with open(sp, "r", encoding="utf-8") as _sf:
                        settings_brain = json.load(_sf)
                    if settings_brain.get("rag_enabled", False) and user_msg:
                        from rag.retriever import RAGRetriever
                        rag_ctx = RAGRetriever.retrieve_as_context(user_msg[:500], top_k=3)
                        if rag_ctx:
                            if messages_out and messages_out[0].get("role") == "system":
                                messages_out[0]["content"] += f"\n\n[CONTEXTO RAG/CONOCIMIENTO EXTRA]:\n{rag_ctx}"
                            else:
                                messages_out.insert(0, {"role": "system", "content": rag_ctx})
                            log.info("[GravityChat] RAG inyectado")
                except Exception:
                    pass

                # Obtener proveedor activo
                from core import provider_manager as _pm
                best_p, best_m = _pm.get_best()
                if not best_p:
                    error_body = json.dumps({"error": "No hay proveedor de IA disponible. Inicia un motor local o configura una API key."}).encode()
                    self.send_response(503)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(error_body)
                    return

                options = {k: data[k] for k in ("temperature", "top_p", "max_tokens") if k in data}
                stripper = ReasoningStripper()
                chat_id = f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}"

                if stream_mode:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self._send_cors()
                    self.end_headers()
                    for chunk_text in _pm.stream(messages_out, model=best_m, provider=best_p.name, options=options):
                        if not chunk_text:
                            continue
                        clean = stripper.process_chunk(chunk_text)
                        if not clean:
                            continue
                        chunk = {
                            "id": chat_id, "object": "chat.completion.chunk", "model": best_m,
                            "choices": [{"index": 0, "delta": {"content": clean}, "finish_reason": None}]
                        }
                        try:
                            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                            self.wfile.flush()
                        except Exception:
                            break
                    final = {
                        "id": chat_id, "object": "chat.completion.chunk", "model": best_m,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    try:
                        self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8"))
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    except Exception:
                        pass
                else:
                    raw = _pm.complete(messages_out, model=best_m, provider=best_p.name, options=options)
                    full = stripper.process_chunk(raw)
                    body = json.dumps({
                        "id": chat_id, "object": "chat.completion", "model": best_m,
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": full}, "finish_reason": "stop"}],
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
            except Exception as e:
                log.error(f"[GravityChat] Error: {e}", exc_info=True)
                try:
                    body = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    pass
            return


        # Rate limiting
        if self.path == "/v1/chat/completions":
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
                            "Eres Gravity AI V16.0 PRO, Auditor Senior. "
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
                                if messages and messages[0].get("role") == "system":
                                    messages[0]["content"] += f"\n\n[CONTEXTO RAG/CONOCIMIENTO EXTRA]:\n{_rag_context}"
                                else:
                                    messages.insert(0, {"role": "system", "content": _rag_context})
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
                log.error(f"Error in POST /v1/chat/completions: {e}", exc_info=True)
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
            return

        # ── V13.0 Monetization Hub — POST handlers ────────────────────────────

        # /v1/language/clone — Clonar un job a otros idiomas
        if self.path == "/v1/language/clone":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                job_id = data.get("job_id")
                langs  = data.get("languages", None)
                if not job_id:
                    self.send_response(400); self._send_cors(); self.end_headers()
                    self.wfile.write(json.dumps({"error": "job_id requerido"}).encode()); return
                from core.language_cloner import clone_job_async
                clone_job_async(int(job_id), langs)
                body = json.dumps({"ok": True, "job_id": job_id, "message": "Clonación iniciada en background.", "languages": langs}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/affiliates/program/add — Agregar programa de afiliado a un niche
        if self.path == "/v1/affiliates/program/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                niche  = data.get("niche_id", "")
                prog   = data.get("program", {})
                if not niche or not prog:
                    self.send_response(400); self._send_cors(); self.end_headers()
                    self.wfile.write(json.dumps({"error": "niche_id y program requeridos"}).encode()); return
                from core.affiliate_manager import add_program
                result = add_program(niche, prog)
                body   = json.dumps(result).encode()
                self.send_response(200 if result["ok"] else 400)
                self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/social/distribute — Distribuir un Short a redes sociales manualmente
        if self.path == "/v1/social/distribute":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data   = json.loads(self.rfile.read(length)) if length else {}
                job_id = data.get("job_id")
                if not job_id:
                    self.send_response(400); self._send_cors(); self.end_headers()
                    self.wfile.write(json.dumps({"error": "job_id requerido"}).encode()); return
                import sqlite3 as _sq3
                BASE_D  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_p    = os.path.join(BASE_D, "_video_queue.sqlite")
                conn    = _sq3.connect(db_p, timeout=10)
                conn.row_factory = _sq3.Row
                row     = conn.execute("SELECT shorts_path, title, topic FROM video_jobs WHERE id=?", (int(job_id),)).fetchone()
                conn.close()
                if not row or not row["shorts_path"]:
                    self.send_response(404); self._send_cors(); self.end_headers()
                    self.wfile.write(json.dumps({"error": "Job sin shorts_path. Asegúrate de que el video fue procesado."}).encode()); return
                from core.tiktok_uploader import distribute_short_async
                distribute_short_async(
                    job_id      = int(job_id),
                    shorts_path = row["shorts_path"],
                    title       = row["title"] or row["topic"] or f"Video #{job_id}",
                )
                body = json.dumps({"ok": True, "job_id": job_id, "message": "Distribución iniciada en background."}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self._send_cors(); self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500); self._send_cors(); self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # /v1/revenue/views/update — Actualizar vistas de un job (llamado desde integración externa)
        if self.path == "/v1/revenue/views/update":
            from api.routes.handlers.revenue_handler import handle_revenue_views_update
            handle_revenue_views_update(self)
            return


        # ── OBS Control: /v1/obs/* ──────────────────────────────────────────────

        # POST /v1/obs/connect
        if self.path == "/v1/obs/connect":
            from api.routes.handlers.obs_handler import handle_obs_connect
            handle_obs_connect(self)
            return

        # POST /v1/obs/scene/switch
        if self.path == "/v1/obs/scene/switch":
            from api.routes.handlers.obs_handler import handle_obs_scene_switch
            handle_obs_scene_switch(self)
            return

        # POST /v1/obs/source/toggle
        if self.path == "/v1/obs/source/toggle":
            from api.routes.handlers.obs_handler import handle_obs_source_toggle
            handle_obs_source_toggle(self)
            return

        # POST /v1/obs/source/visible
        if self.path == "/v1/obs/source/visible":
            from api.routes.handlers.obs_handler import handle_obs_source_visible
            handle_obs_source_visible(self)
            return

        # POST /v1/obs/stream/start
        if self.path == "/v1/obs/stream/start":
            from api.routes.handlers.obs_handler import handle_obs_stream_start
            handle_obs_stream_start(self)
            return

        # POST /v1/obs/stream/stop
        if self.path == "/v1/obs/stream/stop":
            from api.routes.handlers.obs_handler import handle_obs_stream_stop
            handle_obs_stream_stop(self)
            return

        # POST /v1/obs/stream/toggle
        if self.path == "/v1/obs/stream/toggle":
            from api.routes.handlers.obs_handler import handle_obs_stream_toggle
            handle_obs_stream_toggle(self)
            return

        # POST /v1/obs/record/start
        if self.path == "/v1/obs/record/start":
            from api.routes.handlers.obs_handler import handle_obs_record_start
            handle_obs_record_start(self)
            return

        # POST /v1/obs/record/stop
        if self.path == "/v1/obs/record/stop":
            from api.routes.handlers.obs_handler import handle_obs_record_stop
            handle_obs_record_stop(self)
            return

        # POST /v1/obs/record/toggle
        if self.path == "/v1/obs/record/toggle":
            from api.routes.handlers.obs_handler import handle_obs_record_toggle
            handle_obs_record_toggle(self)
            return

        # POST /v1/obs/audio/mute
        if self.path == "/v1/obs/audio/mute":
            from api.routes.handlers.obs_handler import handle_obs_audio_mute
            handle_obs_audio_mute(self)
            return

        # POST /v1/obs/audio/volume
        if self.path == "/v1/obs/audio/volume":
            from api.routes.handlers.obs_handler import handle_obs_audio_volume
            handle_obs_audio_volume(self)
            return

        # POST /v1/obs/spark/generate
        if self.path == "/v1/obs/spark/generate":
            from api.routes.handlers.obs_handler import handle_obs_spark_generate
            handle_obs_spark_generate(self)
            return

        # POST /v1/obs/spark/edit
        if self.path == "/v1/obs/spark/edit":
            from api.routes.handlers.obs_handler import handle_obs_spark_edit
            handle_obs_spark_edit(self)
            return

        # POST /v1/obs/spark/remove
        if self.path == "/v1/obs/spark/remove":
            from api.routes.handlers.obs_handler import handle_obs_spark_remove
            handle_obs_spark_remove(self)
            return

        # ── V16.0 PRO Autonomous Edition POST handlers ───────────────────────────

        # POST /v1/autonomy/trigger — Forzar un ciclo OODA inmediato
        if self.path == "/v1/autonomy/trigger":
            try:
                from core.autonomy_engine import trigger_cycle
                result = trigger_cycle()
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
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

        # POST /v1/reflection/trigger — Forzar un ciclo de reflexión inmediato
        if self.path == "/v1/reflection/trigger":
            try:
                import threading
                from core.self_reflection import run_reflection_cycle
                t = threading.Thread(target=run_reflection_cycle, daemon=True, name="ReflectionTrigger")
                t.start()
                body = json.dumps({"ok": True, "message": "Ciclo de auto-reflexión iniciado en background."}).encode()
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

        # POST /v1/reflection/patches/<patch_id>/approve
        if self.path.startswith("/v1/reflection/patches/") and self.path.endswith("/approve"):
            try:
                patch_id = self.path.split("/v1/reflection/patches/")[1].replace("/approve", "").strip()
                from core.self_reflection import approve_patch
                result = approve_patch(patch_id)
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
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
            return

        # POST /v1/reflection/patches/<patch_id>/reject
        if self.path.startswith("/v1/reflection/patches/") and self.path.endswith("/reject"):
            try:
                patch_id = self.path.split("/v1/reflection/patches/")[1].replace("/reject", "").strip()
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                reason = data.get("reason", "")
                from core.self_reflection import reject_patch
                result = reject_patch(patch_id, reason)
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
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
            return

        # Fallback 404 para cualquier otra ruta POST
        self.send_response(404)
        self._send_cors()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "POST path not found"}).encode())

