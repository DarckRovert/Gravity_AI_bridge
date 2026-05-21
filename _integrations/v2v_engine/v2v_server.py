import asyncio
import json
import logging
import websockets

logging.basicConfig(level=logging.INFO, format="[V2V Server] %(message)s")
logging.getLogger("websockets").setLevel(logging.ERROR)


class V2VState:
    def __init__(self):
        self.active           = False
        self.prompt           = ""          # Prompt personalizado del usuario (vacío = sólo el preset)
        self.negative_prompt  = "low quality, blurry, watermark, text, deformed, extra limbs"
        self.preset           = "cyberpunk_commander"
        self.strength         = 0.85
        self.fps              = 0.0
        # Flags de regeneración
        self.bg_dirty    = True   # True = regenerar el fondo AI
        self.base_dirty  = True   # True = regenerar el avatar base (SD-Turbo)
        self.bg_image    = None   # np.ndarray BGR (512x512) del fondo generado
        self.reference_avatar = None # np.ndarray BGR (512x512) del avatar estático generado


state = V2VState()


async def control_handler(websocket, path=None):
    """Maneja las conexiones WebSocket entrantes desde Gravity Bridge."""
    logging.info("Cliente conectado al V2V Server")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get("command")

                if command == "set_prompt":
                    new_preset   = data.get("preset", state.preset)
                    new_prompt   = data.get("prompt", state.prompt) or ""
                    new_neg      = data.get("negative_prompt", state.negative_prompt) or state.negative_prompt
                    new_strength = float(data.get("strength", state.strength))

                    # Solo regenerar avatar si cambió preset, prompt o strength
                    avatar_changed = (
                        new_preset   != state.preset or
                        new_strength != state.strength or
                        new_prompt   != state.prompt
                    )
                    # Regenerar fondo si cambió el preset (define el bg_prompt)
                    bg_changed = new_preset != state.preset

                    if avatar_changed:
                        state.base_dirty = True
                        state.reference_avatar = None
                    if bg_changed:
                        state.bg_dirty = True
                        state.bg_image = None

                    state.preset          = new_preset
                    state.prompt          = new_prompt
                    state.negative_prompt = new_neg
                    state.strength        = new_strength

                    logging.info(
                        f"Nuevo config: {state.preset} | Strength: {state.strength:.2f} | "
                        f"Prompt: {state.prompt[:50]!r}"
                    )

                elif command == "toggle_active":
                    # IMPORTANTE: NO destruir el estado de generación al pausar.
                    # El BG y los settings se preservan para reactivación instantánea.
                    state.active = bool(data.get("active", not state.active))
                    logging.info(f"V2V Active: {state.active}")

                elif command == "refresh_bg":
                    state.bg_dirty = True
                    state.bg_image = None
                    logging.info("Fondo marcado para regeneración.")

                elif command == "generate_base":
                    state.base_dirty = True
                    state.reference_avatar = None
                    logging.info("Avatar base marcado para regeneración.")

                elif command == "get_status":
                    status = {
                        "active":   state.active,
                        "preset":   state.preset,
                        "strength": state.strength,
                        "fps":      state.fps,
                        "prompt":   state.prompt,
                        "negative_prompt": state.negative_prompt,
                        "bg_ready": state.bg_image is not None,
                        "bg_dirty": state.bg_dirty,
                        "base_ready": state.reference_avatar is not None,
                        "base_dirty": state.base_dirty,
                    }
                    await websocket.send(json.dumps({"type": "status", "data": status}))

            except json.JSONDecodeError:
                logging.error("Recibido JSON inválido")
    except websockets.exceptions.ConnectionClosed:
        logging.info("Cliente desconectado")


async def main():
    server = await websockets.serve(control_handler, "127.0.0.1", 7863)
    logging.info("V2V Control Server iniciado en ws://127.0.0.1:7863")
    await server.wait_closed()


def start_server_in_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())


if __name__ == "__main__":
    start_server_in_background()
