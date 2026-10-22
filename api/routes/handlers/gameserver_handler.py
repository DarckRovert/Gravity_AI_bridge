import json
import os
import time
import shutil
import threading
from core import game_server_manager


def handle_gameserver_status(handler):
    try:
        body = json.dumps(game_server_manager.get_all_status(), indent=2).encode(
            "utf-8"
        )
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_log(handler):
    try:
        import urllib.parse

        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(handler.path).query))
        server_id = params.get("server", "wow_vanilla")
        lines = int(params.get("lines", 100))
        body = json.dumps(
            game_server_manager.get_log(server_id, lines), indent=2
        ).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_players(handler):
    try:
        import urllib.parse

        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(handler.path).query))
        server_id = params.get("server", "wow_vanilla")
        body = json.dumps(game_server_manager.get_players(server_id), indent=2).encode(
            "utf-8"
        )
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_start(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        result = game_server_manager.start(server_id)
        body = json.dumps(result).encode()
        code = 200 if result.get("ok", False) else 400
        handler.send_response(code)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_stop(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        result = game_server_manager.stop(server_id)
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_restart(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        threading.Thread(
            target=game_server_manager.restart,
            args=(server_id,),
            daemon=True,
            name=f"GravityGameRestart-{server_id}",
        ).start()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(
            json.dumps(
                {"ok": True, "note": "Reinicio en proceso...", "server": server_id}
            ).encode()
        )
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_command(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        command = data.get("command", "")
        result = game_server_manager.send_command(server_id, command)
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gameserver_register(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        usr = data.get("username", "")
        pwd = data.get("password", "")
        result = game_server_manager.register_account(server_id, usr, pwd)
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode("utf-8"))
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def handle_gameserver_expose(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        server_id = data.get("server", "wow_vanilla")
        public_ip = data.get("public_address", "")
        result = game_server_manager.expose_wan(server_id, public_ip)
        handler.send_response(200 if result.get("ok") else 400)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode("utf-8"))
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def handle_gameserver_backup(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        json.loads(handler.rfile.read(length)) if length else {}
        BASE = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        backup_dir = os.path.join(BASE, "_archivo", "server_backups")
        os.makedirs(backup_dir, exist_ok=True)
        ts = int(time.time())
        from core.db_migrator import _get_db_path
        gs_db = _get_db_path("image_queue")
        if os.path.isfile(gs_db):
            shutil.copy2(gs_db, os.path.join(backup_dir, f"backup_{ts}.sqlite"))
            msg = f"Backup creado: backup_{ts}.sqlite en _archivo/server_backups/"
        else:
            msg = f"Backup dir listo: {backup_dir} (no hay DB de servidor local para copiar)"
        body = json.dumps({"ok": True, "message": msg, "timestamp": ts}).encode()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


# ── WoW Perú SSH Tunnel ──────────────────────────────────────────────────────

def handle_tunnel_status(handler):
    """GET /v1/gameserver/tunnel/status"""
    try:
        from core.ssh_tunnel_manager import get_status as tunnel_status
        body = json.dumps(tunnel_status(), indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_tunnel_connect(handler):
    """POST /v1/gameserver/tunnel/connect"""
    try:
        from core.ssh_tunnel_manager import start_tunnel
        result = start_tunnel()
        code = 200 if result.get("ok") else 500
        handler.send_response(code)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_tunnel_disconnect(handler):
    """POST /v1/gameserver/tunnel/disconnect"""
    try:
        from core.ssh_tunnel_manager import stop_tunnel
        result = stop_tunnel()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


# ── WoW Perú GM Daemon ───────────────────────────────────────────────────────

def handle_gm_daemon_status(handler):
    """GET /v1/gameserver/gm/status"""
    try:
        from core import game_master_daemon
        body = json.dumps(game_master_daemon.get_status(), indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gm_daemon_start(handler):
    """POST /v1/gameserver/gm/start"""
    try:
        from core import game_master_daemon
        result = game_master_daemon.start()
        code = 200 if result.get("ok") else 500
        handler.send_response(code)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_gm_daemon_stop(handler):
    """POST /v1/gameserver/gm/stop"""
    try:
        from core import game_master_daemon
        result = game_master_daemon.stop()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


# ── Línea de Fases: Progression Governor ───────────────────────────────────

def handle_gameserver_progression(handler):
    """GET /v1/gameserver/progression"""
    try:
        from core.progression_governor import governor
        data = governor.get_progression_data()
        body = json.dumps(data, indent=2).encode('utf-8')
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({'error': str(e)}).encode())


def handle_gameserver_progression_set(handler):
    """POST /v1/gameserver/progression/set"""
    try:
        length = int(handler.headers.get('Content-Length', 0))
        data = json.loads(handler.rfile.read(length)) if length else {}
        phase = data.get('phase', '')
        changed_by = data.get('changed_by', 'Gravity AI Dashboard')
        if not phase:
            handler.send_response(400)
            handler.end_headers()
            handler.wfile.write(json.dumps({'error': "Parámetro 'phase' requerido."}).encode())
            return

        from core.progression_governor import governor
        result = governor.set_phase(phase, changed_by=changed_by)
        code = 200 if result.get('ok') else 400
        handler.send_response(code)
        handler.send_header('Content-Type', 'application/json')
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(json.dumps(result).encode())
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({'error': str(e)}).encode())
