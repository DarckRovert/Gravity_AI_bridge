import json, time, uuid, threading, os, sys, mimetypes, glob, traceback, yaml, urllib.parse, urllib.request, subprocess, psutil
from core import provider_manager, security_monitor, image_queue, video_pipeline, deploy_manager, game_server_manager, ai_process_manager, engine_watchdog
from core.audit_log import audit_logger
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data
from core.logger import log
from core.rate_limiter import check_access
from core.reasoning_stripper import ReasoningStripper



class PostAgentMixin:
    def _handle_post_agent(self):
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
                    return True
                    
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
            return True

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
            return True

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
            return True
            
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
            return True

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
            return True
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
                    return True
                    
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
            return True

        # /v1/scheduler/trigger — Encolar un video ahora (override manual del scheduler)
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
            return True

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
            return True

        # /v1/model/lock — Bloquear un modelo y proveedor específico en _settings.json
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
            return True

        # /v1/fabricaweb/deploy
        if self.path == "/v1/journalist/start":
            from api.routes.handlers.journalist_handler import handle_journalist_start
            handle_journalist_start(self)
            return True

        if self.path == "/v1/journalist/stop":
            from api.routes.handlers.journalist_handler import handle_journalist_stop
            handle_journalist_stop(self)
            return True

        if self.path == "/v1/journalist/portal/start":
            from api.routes.handlers.journalist_handler import handle_journalist_portal_start
            handle_journalist_portal_start(self)
            return True

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
                    return True
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
            return True

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
                    return True
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
            return True

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
            return True

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
                    return True
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sys.path.insert(0, os.path.join(BASE, "tools"))
                from grep_tool import GrepTool
                import concurrent.futures as _cf
                grepper = GrepTool()
                # Fix real: No usar 'with' porque fuerza shutdown(wait=True) al salir del bloque
                _ex = _cf.ThreadPoolExecutor(max_workers=1)
                _fut = _ex.submit(grepper.execute, pattern=pattern, path=path_g or BASE)
                try:
                    r = _fut.result(timeout=15)
                    _ex.shutdown(wait=False)
                except _cf.TimeoutError:
                    _ex.shutdown(wait=False)
                    body = json.dumps({"ok": False, "matches": [], "count": 0,
                                       "raw": "Timeout: búsqueda excedió 15s. Usa el parámetro 'path' para limitar el scope."}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                    return True
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
            return True

        # /v1/security/kill — Kill suspicious process
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
            return True

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
            return True

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
                    return True
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
            return True

        # ── /v1/gravity/chat — Chat con conciencia sistémica completa ─────────
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
            return True

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
            return True

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
            return True

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
            return True

        return False
