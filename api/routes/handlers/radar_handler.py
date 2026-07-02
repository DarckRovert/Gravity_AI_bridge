import json
import os
import subprocess
import psutil

# Variable global para mantener referencia al proceso del Radar
RADAR_PROC = None

def _get_status_dict():
    global RADAR_PROC
    is_running = False
    
    if RADAR_PROC is not None:
        if RADAR_PROC.poll() is None:
            is_running = True
        else:
            RADAR_PROC = None

    if not is_running:
        # Fallback: buscar por nombre si quedó huérfano
        try:
            for p in psutil.process_iter(["name", "cmdline"]):
                if p.info["name"] and "python" in p.info["name"].lower():
                    cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                    if "core\\high_frequency_radar.py" in cmd or "core/high_frequency_radar.py" in cmd:
                        is_running = True
                        break
        except Exception:
            pass

    return {
        "online": is_running,
        "message": "Online" if is_running else "Offline",
    }

def handle_radar_status(handler):
    status = _get_status_dict()
    body = json.dumps(status, indent=2).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    if hasattr(handler, "_send_cors") and handler._send_cors is not None:
        handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)

def handle_radar_start(handler):
    global RADAR_PROC
    status = _get_status_dict()
    if status["online"]:
        handler.send_response(400)
        handler.send_header("Content-Type", "application/json")
        if hasattr(handler, "_send_cors") and handler._send_cors is not None:
            handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps({"ok": False, "msg": "Radar HF ya está en ejecución"}).encode("utf-8")
        )
        return

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    script = os.path.join(BASE_DIR, "core", "high_frequency_radar.py")

    try:
        log_path = os.path.join(BASE_DIR, "gravity_radar.log")
        with open(log_path, "a", encoding="utf-8") as log_file:
            RADAR_PROC = subprocess.Popen(
                ["python", script],
                cwd=BASE_DIR,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        
        msg = "Radar HF iniciado exitosamente en segundo plano"
        ok = True
    except Exception as e:
        msg = f"Error al iniciar: {str(e)}"
        ok = False

    handler.send_response(200 if ok else 500)
    handler.send_header("Content-Type", "application/json")
    if hasattr(handler, "_send_cors") and handler._send_cors is not None:
        handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode("utf-8"))

def handle_radar_stop(handler):
    global RADAR_PROC

    try:
        killed = False
        
        if RADAR_PROC and RADAR_PROC.poll() is None:
            parent = psutil.Process(RADAR_PROC.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            RADAR_PROC.wait(timeout=3)
            killed = True
            
        RADAR_PROC = None

        # Fallback to name search
        for p in psutil.process_iter(["name", "cmdline"]):
            if p.info["name"] and "python" in p.info["name"].lower():
                cmd = " ".join(p.info.get("cmdline", []) or []).lower()
                if "high_frequency_radar.py" in cmd:
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
                "msg": "Radar HF detenido" if killed else "No estaba en ejecución"
            }).encode("utf-8")
        )
    except Exception as e:
        handler.send_response(500)
        handler.send_header("Content-Type", "application/json")
        if hasattr(handler, "_send_cors") and handler._send_cors is not None:
            handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"ok": False, "msg": str(e)}).encode("utf-8"))
