"""
=============================================================================
        GRAVITY AI — WOW SERVER TOOL V1.0 PRO [AzerothCore WotLK]
        Herramienta Agentic para Ejecución de Comandos y Eventos GM
=============================================================================
Permite a los Agentes de IA interactuar con el servidor WoW Perú mediante:
  - Ejecución de comandos GM de AzerothCore (SOAP)
  - Emisión de anuncios globales (.announce)
  - Activación y control de eventos de mundo (.event start/stop)
  - Spawning dinámico de criaturas y objetos (.npc add / .gobject add)
  - Envío de recompensas por correo in-game (.send mail)
  - Recarga de subsistemas Eluna y scripts en caliente (.reload eluna)
"""

import os
import logging
from typing import Dict, Any, Optional
from tools.base_tool import Tool, ToolResult

log = logging.getLogger("gravity.tools.wow_server")


class WoWServerTool(Tool):
    """
    Herramienta de control del mundo para AzerothCore / WoW Perú.
    """

    name: str = "wow_server"
    description: str = (
        "Ejecuta acciones de Game Master y administración en el servidor AzerothCore "
        "de WoW Perú mediante SOAP. Permite emitir anuncios (.announce), controlar "
        "eventos (.event start/stop), invocar NPCs (.npc add), enviar correos (.send mail) "
        "y recargar scripts de Eluna (.reload eluna)."
    )
    requires_confirmation: bool = False

    def __init__(self) -> None:
        self.dangerous_commands = ["shutdown", "restart", "ban", "kick", "account delete", "setpassword"]

    def execute(self, action: str = "command", **kwargs: Any) -> ToolResult:
        """
        Punto de entrada de la herramienta para el ToolExecutor.
        Parámetros:
          - action: 'command' | 'announce' | 'event' | 'mail' | 'reload' | 'status'
          - command: comando GM a ejecutar (para action='command')
          - message: texto para .announce (para action='announce')
          - event_id: ID numérico del evento (para action='event')
          - event_action: 'start' | 'stop' (para action='event')
          - player: nombre del destinatario (para action='mail')
          - subject: asunto del correo (para action='mail')
          - body: contenido de la carta (para action='mail')
          - item_id: ID del ítem opcional (para action='mail')
          - count: cantidad del ítem (para action='mail')
          - money: dinero en cobres (para action='mail')
          - subsystem: 'eluna' | 'config' | 'all' (para action='reload')
        """
        from core import game_server_manager

        server_id = kwargs.get("server", "wow_peru")

        try:
            # 1. Ejecutar comando genérico
            if action == "command":
                cmd = kwargs.get("command", "").strip()
                if not cmd:
                    return ToolResult(success=False, stderr="Argumento 'command' requerido.")

                # Validar comandos destructivos
                low = cmd.lower()
                for dangerous in self.dangerous_commands:
                    if dangerous in low:
                        return ToolResult(
                            success=False,
                            stderr=f"Comando '{dangerous}' bloqueado por directiva de seguridad. Requiere autorización HITL explícita.",
                        )

                res = game_server_manager.send_command(server_id, cmd)
                if res.get("ok"):
                    return ToolResult(success=True, stdout=res.get("result", "Comando ejecutado sin salida."))
                return ToolResult(success=False, stderr=res.get("error", "Error ejecutando comando SOAP."))

            # 2. Anuncio Global
            elif action == "announce":
                msg = kwargs.get("message", "").strip()
                if not msg:
                    return ToolResult(success=False, stderr="Argumento 'message' requerido.")
                full_cmd = f".announce [WoW Perú AI] {msg}"
                res = game_server_manager.send_command(server_id, full_cmd)
                if res.get("ok"):
                    return ToolResult(success=True, stdout=f"Anuncio emitido: {msg}")
                return ToolResult(success=False, stderr=res.get("error", "Fallo al emitir anuncio."))

            # 3. Control de Eventos
            elif action == "event":
                event_id = kwargs.get("event_id")
                ev_action = kwargs.get("event_action", "start").lower()
                if not event_id:
                    return ToolResult(success=False, stderr="Argumento 'event_id' requerido.")
                if ev_action not in ("start", "stop"):
                    return ToolResult(success=False, stderr="event_action debe ser 'start' o 'stop'.")

                full_cmd = f".event {ev_action} {event_id}"
                res = game_server_manager.send_command(server_id, full_cmd)
                if res.get("ok"):
                    return ToolResult(success=True, stdout=res.get("result", f"Evento {event_id} {ev_action} exitoso."))
                return ToolResult(success=False, stderr=res.get("error", f"Fallo al modificar evento {event_id}."))

            # 4. Envío de Correo con Recompensa
            elif action == "mail":
                player = kwargs.get("player", "").strip()
                subject = kwargs.get("subject", "Recompensa Especial").strip()
                body = kwargs.get("body", "Felicidades por tu hazaña en el Reino Andino.").strip()
                item_id = int(kwargs.get("item_id", 0))
                count = int(kwargs.get("count", 1))
                money = int(kwargs.get("money", 0))

                if not player:
                    return ToolResult(success=False, stderr="Argumento 'player' requerido.")

                if item_id > 0:
                    full_cmd = f'.send mail {player} "{subject}" "{body}" {item_id} {count}'
                elif money > 0:
                    full_cmd = f'.send money {player} "{subject}" "{body}" {money}'
                else:
                    full_cmd = f'.send mail {player} "{subject}" "{body}"'

                res = game_server_manager.send_command(server_id, full_cmd)
                if res.get("ok"):
                    return ToolResult(success=True, stdout=f"Correo enviado a {player}: {res.get('result', 'OK')}")
                return ToolResult(success=False, stderr=res.get("error", f"Fallo al enviar correo a {player}."))

            # 5. Recarga de Subsistemas (Eluna, Config)
            elif action == "reload":
                subsystem = kwargs.get("subsystem", "eluna").lower()
                cmd_map = {
                    "eluna": ".reload eluna",
                    "config": ".reload config",
                    "all": ".reload all",
                    "quests": ".reload quest_template",
                }
                full_cmd = cmd_map.get(subsystem, f".reload {subsystem}")
                res = game_server_manager.send_command(server_id, full_cmd)
                if res.get("ok"):
                    return ToolResult(success=True, stdout=f"Recarga exitosa: {res.get('result', 'OK')}")
                return ToolResult(success=False, stderr=res.get("error", f"Fallo en recarga de {subsystem}."))

            # 6. Estado del Servidor
            elif action == "status":
                res = game_server_manager.send_command(server_id, ".server info")
                if res.get("ok"):
                    return ToolResult(success=True, stdout=res.get("result", "Online"))
                return ToolResult(success=False, stderr=res.get("error", "Servidor no responde."))

            else:
                return ToolResult(
                    success=False,
                    stderr=f"Acción '{action}' no reconocida. Acciones válidas: command, announce, event, mail, reload, status.",
                )

        except Exception as e:
            log.error(f"[WoWServerTool] Error en ejecución: {e}")
            return ToolResult(success=False, stderr=f"Excepción en wow_server: {str(e)}")
