import os
import sys
import json
import subprocess
import psutil
from core.logger import log

def get_base_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def handle_v2v_start(req):
    try:
        # Prevent starting if already running
        is_running = False
        for p in psutil.process_iter(['name', 'cmdline', 'cwd']):
            try:
                if p.info['name'] and 'python' in p.info['name'].lower():
                    cmd_str = " ".join(p.info.get('cmdline', []) or []).lower()
                    if 'v2v_pipeline.py' in cmd_str:
                        is_running = True
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if is_running:
            body = json.dumps({"ok": False, "message": "El motor V2V ya está en ejecución."}).encode()
            req.send_response(400)
            req.send_header("Content-Type", "application/json")
            req._send_cors()
            req.end_headers()
            req.wfile.write(body)
            return

        BASE = get_base_dir()
        v2v_dir = os.path.join(BASE, "_integrations", "v2v_engine")
        bat_path = os.path.join(v2v_dir, "run_v2v.bat")
        
        if not os.path.exists(bat_path):
            body = json.dumps({"ok": False, "message": "run_v2v.bat no encontrado."}).encode()
            req.send_response(404)
            req.send_header("Content-Type", "application/json")
            req._send_cors()
            req.end_headers()
            req.wfile.write(body)
            return

        # Start as a detached process (CREATE_NO_WINDOW or CREATE_NEW_CONSOLE)
        # Using CREATE_NEW_CONSOLE so user can see the logs if they want, or we can use CREATE_NO_WINDOW
        # Since it's a V2V engine, it might need to grab the camera, so a visible console is good for debugging.
        CREATE_NEW_CONSOLE = 0x00000010
        subprocess.Popen(
            [bat_path], 
            cwd=v2v_dir, 
            creationflags=CREATE_NEW_CONSOLE,
            shell=True
        )

        body = json.dumps({"ok": True, "message": "Motor V2V iniciado"}).encode()
        req.send_response(200)
        req.send_header("Content-Type", "application/json")
        req._send_cors()
        req.end_headers()
        req.wfile.write(body)
    except Exception as e:
        log.error(f"Error starting V2V: {e}")
        req.send_response(500)
        req._send_cors()
        req.end_headers()
        req.wfile.write(json.dumps({"error": str(e)}).encode())

def handle_v2v_stop(req):
    try:
        killed_count = 0
        for p in psutil.process_iter(['name', 'cmdline', 'cwd']):
            try:
                if p.info['name'] and 'python' in p.info['name'].lower():
                    cmd_str = " ".join(p.info.get('cmdline', []) or []).lower()
                    if 'v2v_pipeline.py' in cmd_str or 'v2v_server.py' in cmd_str:
                        p.terminate()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        body = json.dumps({"ok": True, "message": f"Motor V2V detenido. Procesos terminados: {killed_count}"}).encode()
        req.send_response(200)
        req.send_header("Content-Type", "application/json")
        req._send_cors()
        req.end_headers()
        req.wfile.write(body)
    except Exception as e:
        log.error(f"Error stopping V2V: {e}")
        req.send_response(500)
        req._send_cors()
        req.end_headers()
        req.wfile.write(json.dumps({"error": str(e)}).encode())
