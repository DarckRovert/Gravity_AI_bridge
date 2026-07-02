"""
Módulo J.A.R.V.I.S: Bus Sensorial Multimodal (Pilar 1)
Servidor WebSocket asíncrono que centraliza la telemetría y los comandos de los módulos periféricos.
Actúa como la médula espinal de Gravity.
"""

import asyncio
import websockets
import threading
import logging

# Silenciar el spam de 'opening handshake failed' (generalmente causado por escaneos de puertos o firewalls locales)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

class SensoryBus:
    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.loop = None
        self._thread = None

    async def handler(self, websocket, *args, **kwargs):
        # Register client
        self.connected_clients.add(websocket)
        print(f"[SENSORY-BUS] Nuevo cliente conectado. Total: {len(self.connected_clients)}")
        try:
            async for message in websocket:
                # Filtrar mensajes de latidos (ping/status) para no hacer spam en la terminal
                if '"voice_daemon_ping"' not in message and '"voice_daemon_status"' not in message:
                    print(f"[SENSORY-BUS] Recibido: {message}")
                # Broadcast the message to all OTHER clients
                # For instance, Voice Daemon sends "voice_input", the Brain receives it.
                await self.broadcast(message, sender=websocket)
        except Exception:
            # Captura ConnectionClosed, OSError, etc., para que no tire el loop entero
            pass
        finally:
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
            print(f"[SENSORY-BUS] Cliente desconectado. Total: {len(self.connected_clients)}")

    async def broadcast(self, message, sender=None):
        if not self.connected_clients:
            return
        
        # Enviar a todos excepto al emisor original
        targets = [client for client in self.connected_clients if client != sender]
        if targets:
            for client in targets:
                try:
                    await client.send(message)
                except Exception:
                    # El handler principal de websocket se encargará de removerlo si se desconectó
                    pass

    async def main(self):
        print(f"[SENSORY-BUS] Iniciando servidor en ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port, ping_interval=None, ping_timeout=None):
            await asyncio.Future()  # Corre para siempre

    def start_server_thread(self):
        """Inicia el bucle asyncio en un hilo separado (para integrarlo en bridge_server.py)."""
        def _run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.main())
            
        self._thread = threading.Thread(target=_run, daemon=True, name="SensoryBusThread")
        self._thread.start()
        return self._thread

# Para correr el bus directamente en modo standalone (Test)
if __name__ == "__main__":
    bus = SensoryBus()
    asyncio.run(bus.main())
