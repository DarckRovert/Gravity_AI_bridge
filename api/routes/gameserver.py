import json
import urllib.parse
import threading
from core import game_server_manager

# ── Endpoints GET ─────────────────────────────────────────────────────────────


def serve_gameserver_status(handler):
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


def serve_gameserver_log(handler):
    try:
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


def serve_gameserver_players(handler):
    try:
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


def serve_registro(handler):
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
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(HTML.encode("utf-8"))


# ── Endpoints POST ────────────────────────────────────────────────────────────


def handle_start(handler, data):
    server_id = data.get("server", "wow_vanilla")
    result = game_server_manager.start(server_id)
    body = json.dumps(result).encode()
    code = 200 if result.get("ok", False) else 400
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)


def handle_stop(handler, data):
    server_id = data.get("server", "wow_vanilla")
    result = game_server_manager.stop(server_id)
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps(result).encode())


def handle_restart(handler, data):
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


def handle_command(handler, data):
    server_id = data.get("server", "wow_vanilla")
    command = data.get("command", "")
    result = game_server_manager.send_command(server_id, command)
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps(result).encode())


def handle_register(handler, data):
    server_id = data.get("server", "wow_vanilla")
    usr = data.get("username", "")
    pwd = data.get("password", "")
    result = game_server_manager.register_account(server_id, usr, pwd)
    handler.send_response(200 if result.get("ok") else 400)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps(result).encode("utf-8"))


def handle_expose(handler, data):
    server_id = data.get("server", "wow_vanilla")
    public_ip = data.get("public_address", "")
    result = game_server_manager.expose_wan(server_id, public_ip)
    handler.send_response(200 if result.get("ok") else 400)
    handler.send_header("Content-Type", "application/json")
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(json.dumps(result).encode("utf-8"))
