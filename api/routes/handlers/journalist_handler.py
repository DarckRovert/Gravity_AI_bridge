import json
import os
import subprocess
import psutil
from urllib.parse import urlparse, parse_qs

# Referencias globales a los procesos de los periodistas
JOURNALIST_PROCS = {
    "web": None,
    "peru": None,
    "geopolitica": None
}

REPORTER_CONFIGS = {
    "web": {
        "script": "news_daemon.py",
        "state_file": "_periodista_state.json",
        "lock_file": "gravity_periodista.lock",
        "log_file": "gravity.log"
    },
    "peru": {
        "script": "news_daemon_peru.py",
        "state_file": "_periodista_peru_state.json",
        "lock_file": "gravity_periodista_peru.lock",
        "log_file": "gravity_peru.log"
    },
    "geopolitica": {
        "script": "news_daemon_geopolitica.py",
        "state_file": "_periodista_geopolitica_state.json",
        "lock_file": "gravity_periodista_geopolitica.lock",
        "log_file": "gravity_geopolitica.log"
    }
}


def _get_type_param(handler) -> str:
    try:
        parsed = urlparse(handler.path)
        params = parse_qs(parsed.query)
        val = params.get("type", ["web"])[0].lower()
        if val in REPORTER_CONFIGS:
            return val
    except Exception:
        pass
    return "web"


def _get_status_dict(reporter_type="web"):
    global JOURNALIST_PROCS
    is_running = False
    pid = None

    cfg = REPORTER_CONFIGS[reporter_type]

    # Verificación rápida y segura vía referencia directa del proceso
    proc = JOURNALIST_PROCS.get(reporter_type)
    if proc is not None:
        if proc.poll() is None:
            is_running = True
            pid = proc.pid
        else:
            JOURNALIST_PROCS[reporter_type] = None

    # Fallback: buscar por nombre en caso de haber sido lanzado por .bat
    if not is_running:
        try:
            for p in psutil.process_iter(["pid", "name", "cmdline"]):
                if p.info["name"] and "python" in p.info["name"].lower():
                    cmd_list = [arg.lower() for arg in p.info.get("cmdline", []) or []]
                    script_name = cfg["script"].lower()
                    for arg in cmd_list:
                        if arg == script_name or arg.endswith("\\" + script_name) or arg.endswith("/" + script_name):
                            is_running = True
                            pid = p.info["pid"]
                            break
                    if is_running:
                        break
        except Exception:
            pass

    # Intentar leer estado interno
    local_app_data = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
        "Gravity", 
        "Databases"
    )
    state_file = os.path.join(local_app_data, cfg["state_file"])
    
    internal_state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                internal_state = json.load(f)
        except Exception:
            pass

    status_data = {
        "online": is_running,
        "pid": pid,
        "message": "Online" if is_running else "Offline",
        "internal_status": internal_state.get("status", "unknown"),
        "cycle_count": internal_state.get("cycle_count", 0),
        "last_article_title": internal_state.get("last_article_title", ""),
        "next_run_ts": internal_state.get("next_run_ts", 0)
    }

    # Agregar reportes de los tres de forma anidada para el Dashboard (para preservar compatibilidad web)
    if reporter_type == "web":
        status_data["reporters"] = {
            "web": {
                "online": is_running,
                "pid": pid,
                "status": internal_state.get("status", "unknown"),
                "cycle_count": internal_state.get("cycle_count", 0),
                "last_article_title": internal_state.get("last_article_title", ""),
                "next_run_ts": internal_state.get("next_run_ts", 0)
            },
            "peru": _get_status_dict("peru"),
            "geopolitica": _get_status_dict("geopolitica")
        }

    return status_data


def handle_journalist_status(handler):
    rtype = _get_type_param(handler)
    status = _get_status_dict(rtype)
    body = json.dumps(status, indent=2).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)


def handle_journalist_start(handler):
    global JOURNALIST_PROCS
    rtype = _get_type_param(handler)
    status = _get_status_dict(rtype)
    if status["online"]:
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps(
                {"ok": False, "msg": f"El Reportero {rtype} ya está en ejecución"}
            ).encode("utf-8")
        )
        return

    cfg = REPORTER_CONFIGS[rtype]
    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    script = os.path.join(BASE_DIR, cfg["script"])

    try:
        log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
            "Gravity", 
            "Logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, cfg["log_file"])
        
        log_file = open(log_file_path, "a", encoding="utf-8")
        proc = subprocess.Popen(
            ["python", script],
            cwd=BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        JOURNALIST_PROCS[rtype] = proc
        msg = f"Reportero {rtype} iniciado exitosamente"
        ok = True
    except Exception as e:
        msg = f"Error al iniciar: {str(e)}"
        ok = False

    handler.send_response(200 if ok else 500)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode("utf-8"))


def handle_journalist_stop(handler):
    global JOURNALIST_PROCS
    rtype = _get_type_param(handler)
    cfg = REPORTER_CONFIGS[rtype]

    try:
        killed = False
        proc = JOURNALIST_PROCS.get(rtype)
        if proc and proc.poll() is None:
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except Exception:
                        pass
                parent.terminate()
                proc.wait(timeout=3)
                killed = True
            except Exception:
                pass


        # Fallback a buscar por nombre si no lo tenemos trackeado localmente
        for p in psutil.process_iter(["name", "cmdline"]):
            if p.info["name"] and "python" in p.info["name"].lower():
                cmd_list = [arg.lower() for arg in p.info.get("cmdline", []) or []]
                script_name = cfg["script"].lower()
                for arg in cmd_list:
                    if arg == script_name or arg.endswith("\\" + script_name) or arg.endswith("/" + script_name):
                        try:
                            p.terminate()
                            killed = True
                        except Exception:
                            pass
                        break

        JOURNALIST_PROCS[rtype] = None

        if killed:
            app_data = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
                "Gravity", 
                "Databases"
            )
            state_file = os.path.join(app_data, cfg["state_file"])
            try:
                if os.path.exists(state_file):
                    with open(state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    state["status"] = "stopped"
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps(
                {
                    "ok": True,
                    "msg": (
                        f"Reportero {rtype} detenido" if killed else "No estaba en ejecución"
                    ),
                }
            ).encode("utf-8")
        )
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))


def handle_journalist_log(handler):
    rtype = _get_type_param(handler)
    cfg = REPORTER_CONFIGS[rtype]
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
        "Gravity", 
        "Logs"
    )
    log_path = os.path.join(log_dir, cfg["log_file"])

    if not os.path.exists(log_path):
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": True, "logs": f"No hay logs de {rtype} disponibles aún."}).encode(
                "utf-8"
            )
        )
        return

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        filtered = []
        for line in reversed(lines):
            filtered.insert(0, line)
            if len(filtered) >= 100:
                break

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": True, "logs": "".join(filtered)}).encode("utf-8")
        )
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))


def handle_journalist_news(handler):
    actual_path = r"f:\gravity-news-portal\src\data\news.json"

    if not os.path.exists(actual_path):
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": True, "news": []}).encode("utf-8"))
        return

    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            news = json.load(f)

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": True, "news": news}).encode("utf-8"))
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))


def handle_journalist_portal_start(handler):
    import subprocess

    try:
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        launcher_path = os.path.join(
            BASE_DIR, "launchers", "INICIAR_PORTAL_FRONTAL.bat"
        )

        if os.name == "nt":
            import os
            os.startfile(launcher_path)
        else:
            subprocess.Popen(["bash", launcher_path])

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": True, "message": "Portal iniciado"}).encode("utf-8")
        )
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
