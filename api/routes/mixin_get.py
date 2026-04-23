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
        # DASHBOARD_HTML ahora es bytes constante en dashboard.py — import directo
        try:
            from dashboard import get_dashboard_html
            body = get_dashboard_html()
        except Exception:
            body = b"<h1>Gravity AI Bridge V10.1</h1><p>No se encontro web/dashboard.html. Restaura la carpeta web/.</p>"
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ConnectionAbortedError:
            pass

    def _serve_static_output(self):
        # Permite subdirectorios de fecha: /static/output/2026-04-13/filename.png
        raw = self.path[len("/static/output/"):]
        if not raw or ".." in raw:
            self.send_response(403)
            self.end_headers()
            return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fooocus_out = os.path.join(BASE, "_integrations", "Fooocus", "Fooocus", "outputs")

        filepath = None
        # 1. Intento ruta completa (con subcarpeta incluida en raw)
        candidate = os.path.join(fooocus_out, raw.replace("/", os.sep))
        if os.path.isfile(candidate):
            filepath = candidate
        else:
            # 2. Busqueda recursiva por basename (compatibilidad con URLs sin subcarpeta)
            basename = os.path.basename(raw)
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                matches = glob.glob(os.path.join(fooocus_out, "**", basename), recursive=True)
                if matches:
                    filepath = matches[0]
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
        status = {
            "version":         "10.3",
            "bridge_online":   True,
            "active_provider": best_p.name if best_p else None,
            "active_model":    best_m,
            "backends": [
                {
                    "name":       s.name,
                    "category":   getattr(s, "category", "local"),
                    "healthy":    s.is_healthy,
                    "models":     len(s.models),
                    "latency_ms": getattr(s, "response_ms", 0),
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
        recent_logs = audit_logger.get_recent(100)
        body = json.dumps({"object": "list", "data": recent_logs}, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_metrics(self):
        data, content_type = get_metrics_data()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    # ── Game Server Manager ──────────────────────────────────────────────────────
    def _serve_gameserver_status(self):
        try:
            body = json.dumps(game_server_manager.get_all_status(), indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_gameserver_log(self):
        try:
            import urllib.parse
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            server_id = params.get("server", "wow_vanilla")
            lines     = int(params.get("lines", 100))
            body = json.dumps(game_server_manager.get_log(server_id, lines), indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_gameserver_players(self):
        try:
            import urllib.parse
            params    = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            server_id = params.get("server", "wow_vanilla")
            body      = json.dumps(game_server_manager.get_players(server_id), indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

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
        try:
            fabricaweb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_integrations", "FabricaWeb")
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
        try:
            from core.mcp_adapter import active_adapters
            servers = []
            for name, adapter in active_adapters.items():
                is_connected = adapter.process is not None and adapter.process.poll() is None
                servers.append({
                    "name": name,
                    "connected": is_connected,
                    "tools": adapter.list_tools() if is_connected else [],
                    "resources": adapter.list_resources() if is_connected else []
                })
            
            body = json.dumps({"mcp_servers": servers, "count": len(servers)}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_mcp_resource(self):
        """Lee un recurso específico de un servidor MCP."""
        try:
            import urllib.parse
            from core.mcp_adapter import active_adapters
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            server = params.get("server")
            uri = params.get("uri")
            
            if not server or not uri or server not in active_adapters:
                raise ValueError("Servidor o URI no válido")
                
            adapter = active_adapters[server]
            data = adapter.read_resource(uri)
            
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

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

    # ── Hardware Profiler ────────────────────────────────────────────────────
    def _serve_hardware(self):
        """Perfil completo de hardware: GPUs, VRAM, NPU, num_ctx óptimo."""
        try:
            from core.hardware_profiler import get_full_profile
            from core.cost_tracker import CostTracker
            import psutil
            profile = get_full_profile()
            try:
                profile["cpu_percent"] = psutil.cpu_percent(interval=None)
                profile["ram_percent"] = psutil.virtual_memory().percent
                st = CostTracker.get_session_tokens()
                profile["tokens"] = int(st.get("input", 0)) + int(st.get("output", 0))
            except:
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
        try:
            from core.cost_tracker import CostTracker, _get_daily_limit
            over_limit, daily = CostTracker.check_limit()
            data = {
                "session_cost":    CostTracker.get_session_cost(),
                "session_tokens":  CostTracker.get_session_tokens(),
                "daily_cost":      daily,
                "daily_limit":     _get_daily_limit(),
                "over_limit":      over_limit,
                "daily_breakdown": CostTracker.get_daily_breakdown(),
            }
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Engine Watchdog ───────────────────────────────────────────────────────
    def _serve_watchdog(self):
        """Estado del Engine Watchdog: proveedor activo, lock de modelo y hardware."""
        try:
            from core import engine_watchdog
            import json as _json
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_path = os.path.join(BASE_DIR, "_settings.json")
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = _json.load(f)
            except Exception:
                settings = {}
            state = engine_watchdog.get_active_state()
            data = {
                "active_provider": state.get("provider"),
                "active_model":    state.get("model"),
                "model_locked":    settings.get("model_locked", False),
                "hardware":        state.get("hardware", {}),
            }
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_video_status(self):
        """GET /v1/video/status — Estado completo de la cola de video."""
        try:
            data = video_pipeline.get_queue_status()
            body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_video_voices(self):
        """GET /v1/video/voices — Lista las voces SAPI disponibles con metadatos."""
        try:
            voices = video_pipeline.get_available_voices()
            styles = {k: v["label"] for k, v in video_pipeline.CINEMA_STYLES.items()}
            body = json.dumps({
                "voices":  voices,
                "count":   len(voices),
                "styles":  styles,
                "langs":   {
                    "es": "Español",
                    "en": "English",
                    "pt": "Português",
                    "fr": "Français",
                    "de": "Deutsch",
                    "it": "Italiano",
                },
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())



    def _serve_video_download(self):
        """GET /v1/video/download?file=nombre.mp4 — Descarga un video generado."""
        try:
            from urllib.parse import urlparse, parse_qs
            qs       = parse_qs(urlparse(self.path).query)
            filename = qs.get("file", [None])[0]
            if not filename or ".." in filename or "/" in filename or "\\" in filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"Nombre de archivo invalido."}')
                return
            BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            video_path = os.path.join(BASE_DIR, "_videos", filename)
            if not os.path.isfile(video_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error":"Archivo no encontrado."}')
                return
            size = os.path.getsize(video_path)
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self._send_cors()
            self.end_headers()
            with open(video_path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Pollinations.ai Motor ─────────────────────────────────────────────────
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
            self.send_response(500)
            self.end_headers()

    def _serve_static_image_lab(self):
        """
        GET /static/imagelab/<filename>
        Sirve imágenes generadas por el Image Lab (guardadas en _integrations/ImageLab/).
        """
        raw = self.path[len("/static/imagelab/"):]
        if not raw or ".." in raw:
            self.send_response(403); self.end_headers(); return

        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lab_dir = os.path.join(BASE, "_integrations", "ImageLab")
        filepath = os.path.join(lab_dir, os.path.basename(raw))

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

