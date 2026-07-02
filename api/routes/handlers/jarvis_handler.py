import json
import os
import subprocess
import psutil

# Variable global para mantener referencias a los procesos de J.A.R.V.I.S
JARVIS_PROCS = []

def _get_status_dict():
    global JARVIS_PROCS
    is_running = False
    
    # Limpiar procesos muertos
    JARVIS_PROCS = [p for p in JARVIS_PROCS if p.poll() is None]
    
    if len(JARVIS_PROCS) > 0:
        is_running = True
    else:
        # Fallback: buscar por nombre si quedaron huérfanos
        try:
            for p in psutil.process_iter(["name", "cmdline"]):
                if p.info["name"] and "python" in p.info["name"].lower():
                    cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                    if "core\\voice_daemon.py" in cmd or "core/voice_daemon.py" in cmd:
                        is_running = True
                        break
        except Exception:
            pass

    return {
        "online": is_running,
        "message": "Online" if is_running else "Offline",
    }

def handle_jarvis_status(handler):
    status = _get_status_dict()
    body = json.dumps(status, indent=2).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    if hasattr(handler, "_send_cors") and handler._send_cors is not None:
        handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)

def handle_jarvis_start(handler):
    global JARVIS_PROCS
    status = _get_status_dict()
    if status["online"]:
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json")
        if hasattr(handler, "_send_cors") and handler._send_cors is not None:
            handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": False, "msg": "J.A.R.V.I.S ya está en ejecución"}).encode("utf-8")
        )
        return

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    
    modules = [
        os.path.join(BASE_DIR, "core", "voice_daemon.py"),
        os.path.join(BASE_DIR, "core", "overwatch_daemon.py"),
        os.path.join(BASE_DIR, "core", "thermal_watchdog.py"),
        os.path.join(BASE_DIR, "core", "ui", "hud_overlay.py"),
        os.path.join(BASE_DIR, "core", "sentinel_core.py"),
    ]

    try:
        log_path = os.path.join(BASE_DIR, "gravity_jarvis.log")
        launched = []
        for script in modules:
            if os.path.exists(script):
                with open(log_path, "a", encoding="utf-8") as log_file:
                    proc = subprocess.Popen(
                        ["python", script],
                        cwd=BASE_DIR,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                JARVIS_PROCS.append(proc)
                launched.append(os.path.basename(script))
        
        msg = f"J.A.R.V.I.S iniciado: {', '.join(launched)}" if launched else "No se encontraron módulos"
        ok = bool(launched)
    except Exception as e:
        msg = f"Error al iniciar: {str(e)}"
        ok = False

    handler.send_response(200 if ok else 500)
    handler.send_header("Content-Type", "application/json")
    if hasattr(handler, "_send_cors") and handler._send_cors is not None:
        handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode("utf-8"))

def handle_jarvis_stop(handler):
    global JARVIS_PROCS

    try:
        killed = False
        
        # Kill tracked processes
        for proc in JARVIS_PROCS:
            if proc.poll() is None:
                try:
                    parent = psutil.Process(proc.pid)
                    for child in parent.children(recursive=True):
                        child.terminate()
                    parent.terminate()
                    proc.wait(timeout=3)
                    killed = True
                except Exception:
                    pass
                    
        JARVIS_PROCS = []

        # Fallback to name search
        modules_names = ["voice_daemon.py", "overwatch_daemon.py", "thermal_watchdog.py", "hud_overlay.py", "sentinel_core.py"]
        for p in psutil.process_iter(["name", "cmdline"]):
            if p.info["name"] and "python" in p.info["name"].lower():
                cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                if any(m in cmd for m in modules_names):
                    p.terminate()
                    killed = True

        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        if hasattr(handler, "_send_cors") and handler._send_cors is not None:
            handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({
                "ok": True,
                "msg": "J.A.R.V.I.S detenido" if killed else "No estaba en ejecución"
            }).encode("utf-8")
        )
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        if hasattr(handler, "_send_cors") and handler._send_cors is not None:
            handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
