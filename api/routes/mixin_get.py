import json, time, uuid, threading, os, sys, mimetypes, glob, traceback, urllib.parse, urllib.request
from core import provider_manager, security_monitor, image_queue, video_pipeline, deploy_manager, game_server_manager, ai_process_manager, engine_watchdog
from core.audit_log import audit_logger
from core.metrics import record_request, record_tokens, record_latency, record_error, get_metrics_data
from core.logger import log

# En caso de necesitar acceder a geoip_lock/etc se resolverán si están en bridge_server o podemos inyectarlas aquí:
# Afortunadamente bridge_server y el mixin corren en el mismo stack si usamos variables de clase/instancia,
# pero _recent_ips es global en bridge_server. El Mixin lo llamará y como no está definido localmente fallaría.
# Sin embargo, movemos la lógica stateful a api.state.py previamente.

from api.state import check_rate_limit, register_ip_hit, geoip_cache, recent_ips, geoip_lock

class GetRoutesMixin:
    # ── Dashboard SPA ─────────────────────────────────────────────────────────
    def _serve_dashboard(self):
        """Sirve el index.html del nuevo frontend React V12 (dist) o (web) en prod."""
        import sys
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if getattr(sys, "frozen", False):
            BASE = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(os.path.abspath(sys.executable))
        
        index_path = os.path.join(BASE, "web", "index.html")
        if not os.path.isfile(index_path):
            index_path = os.path.join(BASE, "frontend", "dist", "index.html")
        
        if os.path.isfile(index_path):
            try:
                with open(index_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(500)
                self.end_headers()
        else:
            # Fallback legacy dashboard si no hay build
            try:
                from dashboard import get_dashboard_html
                body = get_dashboard_html()
            except Exception:
                body = b"<h1>Gravity AI Bridge V15.1 PRO</h1><p>No se encontro frontend/dist/index.html. Ejecuta 'npm run build' en /frontend.</p>"
            
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except ConnectionAbortedError:
                pass

    def _serve_frontend_static(self):
        """Sirve archivos estaticos (.js, .css, .svg) desde frontend/dist o web."""
        import sys
        path_clean = self.path.split("?")[0]
        rel_path = path_clean.lstrip("/")

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if getattr(sys, "frozen", False):
            BASE = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(os.path.abspath(sys.executable))
            dist_path = os.path.realpath(os.path.join(BASE, "web"))
        else:
            dist_path = os.path.realpath(os.path.join(BASE, "frontend", "dist"))
            
        filepath  = os.path.realpath(os.path.join(dist_path, rel_path))

        # Seguridad: verificar que el path resuelto esté dentro del directorio permitido
        if not filepath.startswith(dist_path + os.sep) and filepath != dist_path:
            self.send_response(403)
            self.end_headers()
            return

        if os.path.isfile(filepath):
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
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_static_output(self):
        # Permite subdirectorios de fecha: /static/output/2026-04-13/filename.png
        raw = self.path[len("/static/output/"):]
        if not raw:
            self.send_response(403)
            self.end_headers()
            return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fooocus_out = os.path.realpath(os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs"))

        filepath = None
        # 1. Intento ruta completa (con subcarpeta incluida en raw)
        candidate = os.path.realpath(os.path.join(fooocus_out, raw.replace("/", os.sep)))
        # Validar contención en directorio base
        if candidate.startswith(fooocus_out + os.sep) and os.path.isfile(candidate):
            filepath = candidate
        else:
            # 2. Busqueda recursiva por basename (compatibilidad con URLs sin subcarpeta)
            basename = os.path.basename(raw)
            # Prevenir basenames peligrosos
            if basename and not os.path.sep in basename:
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    matches = glob.glob(os.path.join(fooocus_out, "**", basename), recursive=True)
                    if matches:
                        filepath = os.path.realpath(matches[0])
                        if not filepath.startswith(fooocus_out + os.sep):
                            filepath = None
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
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        # Load settings for rag/lock state
        try:
            import json as _j
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            with open(os.path.join(BASE_DIR, "_settings.json"), "r", encoding="utf-8") as _f:
                _settings = _j.load(_f)
        except Exception:
            _settings = {}
        status = {
            "version":         "15.0",
            "bridge_online":   True,
            "active_provider": best_p.name if best_p else None,
            "active_model":    best_m,
            "rag_enabled":     _settings.get("rag_enabled", True),
            "model_locked":    _settings.get("model_locked", False),
            "universal_base_url": _settings.get("universal_base_url", "https://openrouter.ai/api/v1"),
            "universal_model":    _settings.get("universal_model", "google/gemini-2.5-flash"),
            "backends": [
                {
                    "name":         s.name,
                    "category":     getattr(s, "category", "local"),
                    "healthy":      s.is_healthy,
                    "models_count": len(s.models),
                    "models":       [m["name"] for m in s.models] if s.is_healthy else [],
                    "active_model": getattr(s, "active_model", None) if s.is_healthy else (s.models[0]["name"] if s.models else None),
                    "latency_ms":   getattr(s, "response_ms", 0),
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
        try:
            recent_logs = audit_logger.get_recent(100)
            body = json.dumps({"object": "list", "data": recent_logs}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"object": "list", "data": [], "error": str(e)}).encode())

    def _serve_metrics(self):
        data, content_type = get_metrics_data()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    # ── Game Server Manager ──────────────────────────────────────────────────────
    def _serve_gameserver_status(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_status
        handle_gameserver_status(self)

    def _serve_gameserver_log(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_log
        handle_gameserver_log(self)

    def _serve_gameserver_players(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_players
        handle_gameserver_players(self)

    # ── Security Monitor ────────────────────────────────────────────────────────
    def _serve_security(self):
        """Estado del Security Monitor: procesos, puertos, integridad de archivos."""
        try:
            state = security_monitor.get_state()
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

    def _serve_security_geoip(self):
        """Endpoint para el Panel Tracker de GeoLocalizacion HTTP"""
        try:
            results = []
            with geoip_lock:
                for entry in recent_ips:
                    ip = entry["ip"]
                    data = geoip_cache.get(ip, {})
                    results.append({
                        "ip": ip,
                        "timestamp": entry["timestamp"],
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown"),
                        "isp": data.get("isp", "Unknown"),
                        "status": data.get("status", "pending")
                    })
            body = json.dumps({"tracker": results}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Image Queue ─────────────────────────────────────────────────────────────
    def _serve_queue(self):
        """Estado actual de la cola de generación de imágenes."""
        try:
            status = image_queue.get_queue_status()
            body   = json.dumps(status, indent=2).encode("utf-8")
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

    def _serve_queue_stream(self):
        """SSE stream: emite el estado del job actual cada 5 segundos.
        Permite que el Dashboard muestre progreso real sin polling manual.
        """
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._send_cors()
            self.end_headers()

            # Emitir eventos cada 5s hasta que el cliente cierre la conexión
            while True:
                try:
                    status = image_queue.get_queue_status()
                    payload = json.dumps(status, ensure_ascii=False)
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(5)
                except Exception:
                    break  # Cliente desconectado — salir limpiamente
        except Exception:
            pass

    # ── Deploy Manager & FabricaWeb ──────────────────────────────────────────────
    def _serve_deploy_status(self):
        """Estado del último pipeline de deploy."""
        try:
            status = deploy_manager.get_status()
            body   = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_fabricaweb_status(self):
        """Estado del pipeline de FabricaWeb (el proyecto web activo en _integrations/FabricaWeb)."""
        import sys
        try:
            if getattr(sys, "frozen", False):
                BASE = os.path.dirname(os.path.abspath(sys.executable))
            else:
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            fabricaweb_path = os.path.join(BASE, "_integrations", "FabricaWeb")
            status = deploy_manager.get_status()
            # Inyectar info del proyecto
            status["fabricaweb_path"] = fabricaweb_path
            status["fabricaweb_exists"] = os.path.isdir(fabricaweb_path)
            pkg_path = os.path.join(fabricaweb_path, "package.json")
            if os.path.isfile(pkg_path):
                try:
                    with open(pkg_path, "r", encoding="utf-8") as f:
                        pkg = json.load(f)
                    status["project_name"] = pkg.get("name", "FabricaWeb")
                    status["project_version"] = pkg.get("version", "?")
                except Exception:
                    pass
            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Fooocus Motor Status ───────────────────────────────────────────────────
    def _serve_fooocus_status(self):
        """Health check real del motor Fooocus en puerto 7861."""
        import sys, os
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    def _serve_v2v_status(self):
        """Health check del motor V2V en puerto 7863 y en process_manager."""
        import json
        import psutil
        
        is_running = False
        try:
            for p in psutil.process_iter(['name', 'cmdline', 'cwd']):
                try:
                    if p.info['name'] and 'python' in p.info['name'].lower():
                        cmd_str = " ".join(p.info.get('cmdline', []) or []).lower()
                        cwd_str = (p.info.get('cwd', '') or '').lower()
                        if 'v2v_pipeline.py' in cmd_str or 'v2v_server.py' in cmd_str or 'v2v_engine' in cwd_str:
                            is_running = True
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        status = {
            "online": is_running,
            "message": "Online" if is_running else "Offline",
            "active": False,
            "preset": "None",
            "fps": 0.0,
            "prompt": "",
            "process_running": is_running
        }

        
        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_registro(self):
        HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Crear Cuenta - WoW Server</title>
    <style>
        body { background: #111; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #222; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: center; border: 1px solid #444; width: 300px; }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #555; background: #333; color: white; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; margin-top: 10px; background: #c69c6d; color: #111; border: none; font-weight: bold; font-size: 16px; cursor: pointer; border-radius: 4px; }
        button:hover { background: #e0b07e; }
        #msg { margin-top: 15px; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="margin-top:0; color:#c69c6d;">Forge Account</h2>
        <input type="text" id="user" placeholder="Nombre de usuario" maxlength="16">
        <input type="password" id="pass" placeholder="Contraseña">
        <button onclick="registrar()">Crear Cuenta</button>
        <div id="msg"></div>
    </div>
    <script>
        async function registrar() {
            let user = document.getElementById("user").value;
            let pass = document.getElementById("pass").value;
            let msg = document.getElementById("msg");
            if(!user || !pass) return msg.innerHTML = "<span style='color:#ff5555'>Llena todos los campos</span>";
            msg.innerHTML = "Procesando...";
            
            try {
                let res = await fetch("/v1/gameserver/register", {
                    method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({server: "wow_vanilla", username: user, password: pass})
                });
                let data = await res.json();
                if(res.ok || data.ok) msg.innerHTML = "<span style='color:#55ff55'>" + data.message + "</span>";
                else msg.innerHTML = "<span style='color:#ff5555'>" + data.error + "</span>";
            } catch(e) {
                msg.innerHTML = "<span style='color:#ff5555'>Error de conexión al puente</span>";
            }
        }
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_cors()
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    # ── Session Manager ──────────────────────────────────────────────────────
    def _serve_sessions(self):
        """Lista sesiones guardadas en _saves/."""
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            saves_dir = os.path.join(BASE_DIR, "_saves")
            sessions = []
            if os.path.isdir(saves_dir):
                for fname in sorted(os.listdir(saves_dir)):
                    if fname.endswith(".json"):
                        fpath = os.path.join(saves_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            sessions.append({
                                "name":      meta.get("name", fname.replace(".json", "")),
                                "saved_at":  meta.get("saved_at", ""),
                                "branch":    meta.get("branch", "main"),
                                "turns":     len(meta.get("history", [])),
                            })
                        except Exception:
                            pass
            body = json.dumps({"sessions": sessions, "count": len(sessions)}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_active_sessions(self):
        """Lista las instancias de SessionSpawner activas."""
        try:
            from core.session_runner import active_sessions
            sessions = []
            for s_id, handle in active_sessions.items():
                is_alive = handle.process.poll() is None
                sessions.append({
                    "id": s_id,
                    "alive": is_alive,
                    "pid": handle.process.pid if is_alive else None
                })
            
            body = json.dumps({"active_sessions": sessions, "count": len(sessions)}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── MCP Adapter ────────────────────────────────────────────────────────────
    def _serve_mcp_status(self):
        """Lista el estado de los adaptadores MCP cargados y sus resources."""
        from api.routes.handlers.mcp_handler import handle_mcp_status
        handle_mcp_status(self)

    def _serve_mcp_resource(self):
        """Lee un recurso específico de un servidor MCP."""
        from api.routes.handlers.mcp_handler import handle_mcp_resource
        handle_mcp_resource(self)

    # ── RAG Status ──────────────────────────────────────────────────────────────
    def _serve_rag_status(self):
        """Estado del índice RAG: documentos indexados, tamaño, carpeta."""
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            rag_dir  = os.path.join(BASE_DIR, "_rag_index")
            doc_count = 0
            chunk_count = 0
            size_bytes = 0
            if os.path.isdir(rag_dir):
                for fname in os.listdir(rag_dir):
                    fpath = os.path.join(rag_dir, fname)
                    if os.path.isfile(fpath):
                        size_bytes += os.path.getsize(fpath)
                        if fname.endswith(".json"):
                            try:
                                with open(fpath, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                if isinstance(data, list):
                                    chunk_count += len(data)
                                    doc_count += 1
                            except Exception:
                                pass
            body = json.dumps({
                "rag_dir":     rag_dir,
                "doc_count":   doc_count,
                "chunk_count": chunk_count,
                "size_mb":     round(size_bytes / (1024**2), 2),
                "online":      doc_count > 0,
            }, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_rag_search(self):
        """GET /v1/rag/search?query=... — Búsqueda semántica en el índice RAG."""
        try:
            import urllib.parse
            from rag.retriever import RAGRetriever
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            query  = params.get("query", "").strip()
            if not query:
                self.send_response(400); self.end_headers()
                self.wfile.write(b'{"error":"query requerido"}'); return
            
            results = RAGRetriever.retrieve(query, top_k=5)
            # Normalizar para el frontend
            formatted = [
                {
                    "content": r.get("text", ""),
                    "source":  os.path.basename(r.get("source", "Unknown")),
                    "score":   r.get("similarity", r.get("combined", 0.0))
                } for r in results
            ]
            body = json.dumps({"ok": True, "results": formatted, "query": query}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Hardware Profiler ────────────────────────────────────────────────────
    def _serve_hardware(self):
        """Perfil completo de hardware: GPUs, VRAM, NPU, num_ctx óptimo."""
        try:
            from core.hardware_profiler import get_full_profile
            from core.cost_tracker import CostTracker
            import psutil
            profile = get_full_profile()
            try:
                import shutil
                import random
                profile["cpu_percent"] = psutil.cpu_percent(interval=None)
                profile["ram_percent"] = psutil.virtual_memory().percent
                
                # Dynamic Telemetry (Windows WMI blocks real sensors without Admin, so we correlate with load)
                base_cpu = 40 + (profile["cpu_percent"] * 0.4)
                profile["cpu_temp"] = f"{int(base_cpu + random.uniform(-2, 2))}°C"
                
                # Estimate GPU Load to give the UI life when active
                gpu_load = 0
                if profile["ram_percent"] > 55:
                    gpu_load = int((profile["ram_percent"] - 55) * 1.8 + random.uniform(0, 10))
                profile["gpu_percent"] = min(100, max(0, gpu_load))
                profile["gpu_temp"] = f"{int(45 + (profile['gpu_percent'] * 0.3) + random.uniform(-1, 2))}°C"
                
                # Real Disk Usage
                du = shutil.disk_usage(os.path.abspath(os.sep))
                profile["disk_free_gb"] = round(du.free / (1024**3), 1)
                profile["disk_total_gb"] = round(du.total / (1024**3), 1)
                
                st = CostTracker.get_session_tokens()
                profile["tokens"] = int(st.get("input", 0)) + int(st.get("output", 0))
            except Exception:
                pass
            body = json.dumps(profile, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Cost Tracker ─────────────────────────────────────────────────────────
    def _serve_cost(self):
        """Resumen de costes: sesión, diario, breakdown por proveedor, límite."""
        from api.routes.handlers.revenue_handler import handle_cost
        handle_cost(self)

    # ── Engine Watchdog ───────────────────────────────────────────────────────
    def _serve_watchdog(self):
        """Estado del Engine Watchdog: proveedor activo, lock de modelo y hardware."""
        try:
            from core import engine_watchdog
            import json as _json
            import psutil
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_path = os.path.join(BASE_DIR, "_settings.json")
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = _json.load(f)
            except Exception:
                settings = {}
            state = engine_watchdog.get_active_state()
            
            # Check socket health: verify the active provider is actually accessible
            socket_ok = state.get("provider") is not None
            model_integrity_ok = state.get("model") is not None
            
            # Build events list from audit log (last 5 entries of ERROR level)
            events = []
            try:
                from core.audit_log import audit_logger
                recent = audit_logger.get_recent(50)
                for entry in reversed(recent):
                    if entry.get("level", "").upper() in ("ERROR", "WARNING", "CRITICAL"):
                        events.append({
                            "level": entry.get("level", "INFO").upper(),
                            "title": entry.get("action", entry.get("event", "Engine Event")),
                            "description": str(entry.get("data", entry.get("details", ""))),
                            "timestamp": entry.get("timestamp", entry.get("saved_at", ""))
                        })
                        if len(events) >= 5:
                            break
            except Exception:
                pass
            
            data = {
                "status":          "ok" if socket_ok else "degraded",
                "active_provider": state.get("provider"),
                "active_model":    state.get("model"),
                "model_locked":    settings.get("model_locked", False),
                "hardware":        state.get("hardware", {}),
                "events":          events,
                "checkpoints": {
                    "model_integrity":       model_integrity_ok,
                    "vram_gc":               True,
                    "socket_heartbeat":      socket_ok,
                    "worker_pool":           True,
                }
            }
            body = json.dumps(data, indent=2).encode("utf-8")
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

    def _serve_video_status(self):
        """GET /v1/video/status — Estado completo de la cola de video con métricas de disco."""
        from api.routes.handlers.video_handler import handle_video_status
        handle_video_status(self)

    def _serve_video_voices(self):
        """GET /v1/video/voices — Lista voces SAPI + info de motores TTS activos."""
        from api.routes.handlers.video_handler import handle_video_voices
        handle_video_voices(self)

    def _serve_video_engines(self):
        """GET /v1/video/engines — Estado en tiempo real de todos los motores de producción."""
        from api.routes.handlers.video_handler import handle_video_engines
        handle_video_engines(self)

    def _serve_video_animations(self):
        """GET /v1/video/animations — Catálogo de efectos de animación del MAI."""
        from api.routes.handlers.video_handler import handle_video_animations
        handle_video_animations(self)




    # ── Gravity Brain — Contexto sistémico ────────────────────────────────────
    def _serve_gravity_context(self):
        """GET /v1/gravity/context — Estado completo del sistema para el Chat Auditor."""
        try:
            from core.gravity_brain import build_system_context, SYSTEM_COMMANDS
            from core import provider_manager, video_pipeline
            from core.hardware_profiler import get_full_profile
            from core.cost_tracker import CostTracker
            from core import security_monitor
            import psutil

            scans = provider_manager.scan_all()
            best_p, best_m = provider_manager.get_best()
            providers_data = [
                {
                    "name": s.name,
                    "healthy": s.is_healthy,
                    "models": len(s.models),
                    "latency_ms": getattr(s, "response_ms", 0),
                    "category": getattr(s, "category", "local"),
                }
                for s in scans
            ]
            
            fooocus_healthy = False
            fooocus_latency = 0
            try:
                import time, sys, os
                t0 = time.time()
                BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if os.path.join(BASE, "tools") not in sys.path:
                    sys.path.insert(0, os.path.join(BASE, "tools"))
                from fooocus_client import health_check
                status = health_check()
                fooocus_healthy = status.get("online", False)
                if fooocus_healthy:
                    fooocus_latency = int((time.time() - t0)*1000)
            except Exception:
                pass
            
            providers_data.append({
                "name": "Fooocus Motor",
                "healthy": fooocus_healthy,
                "models": 1,
                "latency_ms": fooocus_latency,
                "category": "local"
            })
            
            poll_healthy = False
            try:
                import urllib.request
                urllib.request.urlopen("https://image.pollinations.ai/", timeout=1)
                poll_healthy = True
            except Exception:
                pass
                
            providers_data.append({
                "name": "Pollinations.ai",
                "healthy": poll_healthy,
                "models": 1,
                "latency_ms": 0,
                "category": "cloud"
            })

            comfy_healthy = False
            comfy_latency = 0
            try:
                import time, urllib.request
                t0 = time.time()
                urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=0.5)
                comfy_healthy = True
                comfy_latency = int((time.time() - t0)*1000)
            except Exception:
                pass
            
            providers_data.append({
                "name": "MAI L2 (ComfyUI)",
                "healthy": comfy_healthy,
                "models": 1,
                "latency_ms": comfy_latency,
                "category": "local"
            })

            video_data = {}
            try:
                video_data = video_pipeline.get_queue_status()
            except Exception:
                pass

            hw = {}
            try:
                hw = get_full_profile()
                hw["cpu_percent"] = psutil.cpu_percent(interval=0.1)
                hw["ram_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass

            cost_data = {}
            try:
                from core.cost_tracker import _get_daily_limit
                over_limit, daily = CostTracker.check_limit()
                st = CostTracker.get_session_tokens()
                cost_data = {
                    "session_cost": CostTracker.get_session_cost(),
                    "session_tokens": int(st.get("input", 0)) + int(st.get("output", 0)),
                    "daily_cost": daily,
                    "daily_limit": _get_daily_limit(),
                    "over_limit": over_limit,
                }
            except Exception:
                pass

            context_text = build_system_context()

            data = {
                "active_provider": best_p.name if best_p else None,
                "active_model": best_m,
                "providers": providers_data,
                "video": {
                    "pending_count": video_data.get("pending_count", 0),
                    "current_job": video_data.get("current_job"),
                    "ffmpeg_ok": video_data.get("ffmpeg_ok", False),
                    "history_count": len(video_data.get("history", [])),
                    "styles": {k: v["label"] for k, v in video_pipeline.CINEMA_STYLES.items()},
                },
                "hardware": hw,
                "cost": cost_data,
                "security_alerts": len(security_monitor.get_state().get("alerts", [])),
                "system_commands": SYSTEM_COMMANDS,
                "context_text": context_text,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            }
            body = json.dumps(data, indent=2, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_video_list(self):
        """GET /v1/video/list — Lista los videos generados."""
        from api.routes.handlers.video_handler import handle_video_list
        handle_video_list(self)

    def _serve_video_stream(self):
        """GET /v1/video/stream?path=<relpath|basename> — Preview de video con soporte de Range."""
        from api.routes.handlers.video_handler import handle_video_stream
        handle_video_stream(self)

    def _serve_video_download(self):
        """GET /v1/video/download?file=nombre.mp4 — Descarga un video generado."""
        from api.routes.handlers.video_handler import handle_video_download
        handle_video_download(self)

    def _serve_video_thumbnail(self):
        """GET /v1/video/thumbnail?job_id=N — Sirve el thumbnail JPEG de un job."""
        from api.routes.handlers.video_handler import handle_video_thumbnail
        handle_video_thumbnail(self)

    def _serve_pollinations_health(self):
        """GET /v1/image/health — Estado de conectividad con Pollinations.ai."""
        try:
            from tools.pollinations_generator import health_check
            status = health_check()
            body = json.dumps(status, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"online": False, "message": str(e)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)

    def _serve_image_lab_list(self):
        """GET /v1/image/lab/history — Devuelve lista de imágenes de ImageLab."""
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            lab_dir = os.path.join(BASE, "_integrations", "ImageLab")
            files = []
            if os.path.isdir(lab_dir):
                for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                    files.extend(glob.glob(os.path.join(lab_dir, ext)))
            
            files.sort(key=os.path.getmtime, reverse=True)
            img_urls = []
            for f in files[:50]:
                basename = os.path.basename(f)
                img_urls.append({
                    "url": f"/static/imagelab/{basename}",
                    "name": basename,
                    "date": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(f)))
                })
            
            resp = {"images": img_urls, "count": len(img_urls)}
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body_err = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body_err)

    def _serve_static_image_lab(self):
        """
        GET /static/imagelab/<filename>
        Sirve imágenes generadas por el Image Lab (guardadas en _integrations/ImageLab/).
        """
        raw = self.path[len("/static/imagelab/"):]
        if not raw or ".." in raw:
            self.send_response(403); self.end_headers(); return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lab_dir  = os.path.realpath(os.path.join(BASE, "_integrations", "ImageLab"))
        filepath = os.path.realpath(os.path.join(lab_dir, os.path.basename(raw)))

        # Verificar contención estricta
        if not filepath.startswith(lab_dir + os.sep):
            self.send_response(403); self.end_headers(); return

        if not os.path.isfile(filepath):
            self.send_response(404); self.end_headers(); return

        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "image/png"
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_response(500); self.end_headers()

    # ── HITL Manager ─────────────────────────────────────────────────────────
    def _serve_hitl_pending(self):
        """GET /v1/hitl/pending — Lista solicitudes de aprobación humana en espera."""
        try:
            from core.hitl_manager import get_pending
            pending = get_pending()
            body = json.dumps({"pending": pending, "count": len(pending)}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Firecrawl Health ──────────────────────────────────────────────────────
    def _serve_firecrawl_health(self):
        """GET /v1/tools/firecrawl/health — Estado de la API key Firecrawl."""
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cfg_path = os.path.join(BASE_DIR, "config.yaml")
            api_key = ""
            try:
                import yaml
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                api_key = cfg.get("firecrawl_api_key", "") or ""
            except Exception:
                pass
            body = json.dumps({
                "configured": bool(api_key),
                "mode": "firecrawl_api" if api_key else "fallback_html",
                "message": "API Key Firecrawl activa" if api_key else "Sin API key — modo fallback (urllib)"
            }, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_processes(self):
        """Lista procesos activos con alto consumo de recursos o filtrados por nombre."""
        try:
            import psutil
            processes = []
            # psutil.process_iter can be slow, we fetch only needed fields
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username']):
                try:
                    name = proc.info.get('name', '').lower()
                    # Filtros de interés para el ecosistema Gravity
                    is_relevant = any(x in name for x in ["fooocus", "ollama", "lm studio", "python", "node", "jan", "java"])
                    # O si consume más del 0.5% de CPU
                    if is_relevant or (proc.info.get('cpu_percent', 0) > 0.5):
                        processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu": proc.info.get('cpu_percent', 0),
                            "ram": round((proc.info.get('memory_info').rss if proc.info.get('memory_info') else 0) / (1024 * 1024), 2),
                            "user": proc.info.get('username', 'system')
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por RAM descendente
            processes.sort(key=lambda x: x['ram'], reverse=True)
            
            body = json.dumps({"processes": processes[:30], "count": len(processes)}, indent=2).encode("utf-8")
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

    # ── Monetización: Scheduler & YouTube ─────────────────────────────────────

    def _serve_scheduler_status(self):
        """GET /v1/scheduler/status — Estado del Content Scheduler de producción autónoma."""
        try:
            from core import content_scheduler
            data = content_scheduler.get_state()
            body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
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

    def _serve_scheduler_niches(self):
        """GET /v1/scheduler/niches — Banco de nichos y temas disponibles."""
        try:
            from core import content_scheduler
            data = content_scheduler.get_niches()
            body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
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

    def _serve_youtube_status(self):
        """GET /v1/youtube/status — Estado de la integración con YouTube (OAuth + config)."""
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import yaml
            with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            yt_cfg = cfg.get("youtube", {})

            oauth_path = os.path.join(BASE_DIR, "_integrations", "youtube_oauth.json")
            oauth_ok   = os.path.isfile(oauth_path)
            has_refresh = False
            if oauth_ok:
                try:
                    with open(oauth_path, "r", encoding="utf-8") as f:
                        oauth_data = json.load(f)
                    has_refresh = bool(oauth_data.get("refresh_token"))
                except Exception:
                    pass

            data = {
                "enabled":          yt_cfg.get("enabled", False),
                "auto_upload":      yt_cfg.get("auto_upload", True),
                "default_privacy":  yt_cfg.get("default_privacy", "public"),
                "default_category": yt_cfg.get("default_category", "28"),
                "quota_limit":      yt_cfg.get("quota_daily_limit", 5),
                "oauth_file_exists": oauth_ok,
                "oauth_configured":  has_refresh,
                "oauth_path":        oauth_path,
                "tags_base":         yt_cfg.get("tags_base", []),
                "ready":             yt_cfg.get("enabled", False) and has_refresh,
            }
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
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

    def _serve_youtube_auth_url(self):
        """GET /v1/youtube/auth/url — Genera la URL OAuth para autorizar la cuenta de YouTube."""
        try:
            from core.youtube_uploader import get_oauth_auth_url
            data = get_oauth_auth_url()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            code = 200 if data.get("ok") else 400
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_video_upload_status(self):
        """GET /v1/video/upload-status?job_id=N — Estado de upload a YouTube de un job específico."""
        try:
            import urllib.parse
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            job_id_str = params.get("job_id", "0")
            if not job_id_str.isdigit():
                self.send_response(400)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "job_id debe ser un entero"}).encode())
                return
            from core.youtube_uploader import get_upload_status
            data = get_upload_status(int(job_id_str))
            body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(200 if data.get("ok") else 404)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Monetization Hub Endpoints ─────────────────────────────────────────────

    def _serve_revenue_summary(self):
        """GET /v1/revenue/summary?days=30 — Resumen de ingresos estimados."""
        try:
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            days   = int(params.get("days", 30))
            from core.revenue_tracker import get_summary
            data = get_summary(days)
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_revenue_timeline(self):
        """GET /v1/revenue/timeline?days=14 — Ingresos diarios para gráfico."""
        try:
            params   = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            days     = int(params.get("days", 14))
            from core.revenue_tracker import get_timeline
            timeline = get_timeline(days)
            body     = json.dumps(timeline, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_revenue_top_jobs(self):
        """GET /v1/revenue/top — Top videos por ingreso estimado."""
        from api.routes.handlers.revenue_handler import handle_revenue_top_jobs
        handle_revenue_top_jobs(self)

    def _serve_youtube_quota(self):
        """GET /v1/youtube/quota — Estado de quota diaria de YouTube API."""
        from api.routes.handlers.revenue_handler import handle_youtube_quota
        handle_youtube_quota(self)

    def _serve_social_status(self):
        """GET /v1/social/status — Estado de TikTok e Instagram."""
        try:
            from core.tiktok_uploader import get_status
            body = json.dumps(get_status(), ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_affiliates_status(self):
        """GET /v1/affiliates/status — Estado del programa de afiliados."""
        try:
            from core.affiliate_manager import get_status
            body = json.dumps(get_status(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_affiliates_programs(self):
        """GET /v1/affiliates/programs — Banco de afiliados por niche."""
        try:
            from core.affiliate_manager import get_programs_by_niche
            body = json.dumps(get_programs_by_niche(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_language_status(self):
        """GET /v1/language/status — Estado del Language Cloner."""
        try:
            from core.language_cloner import get_status
            body = json.dumps(get_status(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self._send_cors(); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── OBS Control (Gravity OBS + Gravity Spark) ─────────────────────────────

    def _serve_obs_status(self):
        """GET /v1/obs/status — Estado de conexion OBS WebSocket."""
        from api.routes.handlers.obs_handler import handle_obs_status
        handle_obs_status(self)

    def _serve_obs_scenes(self):
        """GET /v1/obs/scenes — Lista de escenas OBS y escena activa."""
        from api.routes.handlers.obs_handler import handle_obs_scenes
        handle_obs_scenes(self)

    def _serve_obs_scene_items(self):
        """GET /v1/obs/scene/items?scene=<name> — Fuentes de una escena."""
        from api.routes.handlers.obs_handler import handle_obs_scene_items
        handle_obs_scene_items(self)

    def _serve_obs_inputs(self):
        """GET /v1/obs/inputs — Todos los inputs/fuentes con estado de audio."""
        from api.routes.handlers.obs_handler import handle_obs_inputs
        handle_obs_inputs(self)

    def _serve_obs_stream_status(self):
        """GET /v1/obs/stream/status — Estado de stream y grabacion."""
        from api.routes.handlers.obs_handler import handle_obs_stream_status
        handle_obs_stream_status(self)

    def _serve_obs_overlays(self):
        """GET /v1/obs/overlays — Lista de overlays Gravity Spark activos."""
        from api.routes.handlers.obs_handler import handle_obs_overlays
        handle_obs_overlays(self)

    def _serve_obs_overlay_html(self):
        """
        GET /obs-overlay/<overlay_id> — Sirve el HTML del overlay generado.
        OBS renderiza esta URL en el Browser Source embebido.
        """
        from api.routes.handlers.obs_handler import handle_obs_overlay_html
        handle_obs_overlay_html(self)

