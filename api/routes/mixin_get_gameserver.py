"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GRAVITY AI — GET ROUTES MIXIN: GAME SERVERS [Modular Sub-Router]      ║
║           Gestión de servidores C++ (MangosD/WoW Vanilla) y Registro         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json


class GetGameserverMixin:
    """Sub-mixin especializado en rutas GET para Servidores de Juego y Túneles."""

    def _serve_gameserver_status(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_status
        handle_gameserver_status(self)

    def _serve_gameserver_log(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_log
        handle_gameserver_log(self)

    def _serve_gameserver_players(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_players
        handle_gameserver_players(self)

    def _serve_tunnel_status(self):
        from api.routes.handlers.gameserver_handler import handle_tunnel_status
        handle_tunnel_status(self)

    def _serve_gameserver_progression(self):
        from api.routes.handlers.gameserver_handler import handle_gameserver_progression
        handle_gameserver_progression(self)

    def _serve_gm_daemon_status(self):
        from api.routes.handlers.gameserver_handler import handle_gm_daemon_status
        handle_gm_daemon_status(self)

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
