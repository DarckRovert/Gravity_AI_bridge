import json
import os
import subprocess
import psutil

# Variable global para mantener la referencia al proceso del periodista
JOURNALIST_PROC = None


def _get_status_dict():
    global JOURNALIST_PROC
    is_running = False
    pid = None

    # Verificación rápida y segura vía referencia directa del proceso
    if JOURNALIST_PROC is not None:
        if JOURNALIST_PROC.poll() is None:
            is_running = True
            pid = JOURNALIST_PROC.pid
        else:
            JOURNALIST_PROC = None

    # Fallback: buscar por nombre en caso de haber sido lanzado por .bat
    if not is_running:
        try:
            for p in psutil.process_iter(["pid", "name", "cmdline"]):
                if p.info["name"] and "python" in p.info["name"].lower():
                    cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                    if "news_daemon.py" in cmd:
                        is_running = True
                        pid = p.info["pid"]
                        break
        except Exception:
            pass

    # Intentar leer estado interno de _periodista_state.json
    local_app_data = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
        "Gravity", 
        "Databases"
    )
    state_file = os.path.join(local_app_data, "_periodista_state.json")
    
    internal_state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                internal_state = json.load(f)
        except Exception:
            pass

    return {
        "online": is_running,
        "pid": pid,
        "message": "Online" if is_running else "Offline",
        "internal_status": internal_state.get("status", "unknown"),
        "cycle_count": internal_state.get("cycle_count", 0),
        "last_article_title": internal_state.get("last_article_title", ""),
        "next_run_ts": internal_state.get("next_run_ts", 0)
    }


def handle_journalist_status(handler):
    status = _get_status_dict()
    body = json.dumps(status, indent=2).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)


def handle_journalist_start(handler):
    global JOURNALIST_PROC
    status = _get_status_dict()
    if status["online"]:
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps(
                {"ok": False, "msg": "El Periodista ya está en ejecución"}
            ).encode("utf-8")
        )
        return

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    script = os.path.join(BASE_DIR, "news_daemon.py")

    try:
        log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
            "Gravity", 
            "Logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "gravity.log")
        
        log_file = open(log_file_path, "a", encoding="utf-8")
        JOURNALIST_PROC = subprocess.Popen(
            ["python", script],
            cwd=BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        msg = "Periodista iniciado exitosamente"
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
    global JOURNALIST_PROC

    try:
        killed = False
        if JOURNALIST_PROC and JOURNALIST_PROC.poll() is None:
            parent = psutil.Process(JOURNALIST_PROC.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            JOURNALIST_PROC.wait(timeout=3)
            killed = True

        # Fallback a buscar por nombre si no lo tenemos trackeado localmente
        for p in psutil.process_iter(["name", "cmdline"]):
            if p.info["name"] and "python" in p.info["name"].lower():
                cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                if "news_daemon.py" in cmd:
                    p.terminate()
                    killed = True

        JOURNALIST_PROC = None

        if killed:
            # Fix D5: Si lo matamos a la fuerza, el daemon no puede actualizar su estado. 
            # Actualizamos el JSON aquí para evitar estado "fantasma".
            app_data = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
                "Gravity", 
                "Databases"
            )
            state_file = os.path.join(app_data, "_periodista_state.json")
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
                        "Periodista detenido" if killed else "No estaba en ejecución"
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
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
        "Gravity", 
        "Logs"
    )
    log_path = os.path.join(log_dir, "gravity.log")

    if not os.path.exists(log_path):
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": True, "logs": "No hay logs disponibles aún."}).encode(
                "utf-8"
            )
        )
        return

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Filtrar sólo las líneas que digan [PERIODISTA] (si aplica) o mostrar las últimas N
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
