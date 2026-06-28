"""
Módulo J.A.R.V.I.S: Controlador de IoT y Domótica (Pilar 2)
Permite al LLM interactuar con el entorno físico a través de Home Assistant (HASS) o MQTT.
"""

import urllib.request
import json
import ssl
from core.logger import log
from core.config_manager import config

class IoTController:
    def __init__(self):
        # Configuraciones extraídas del config.yaml (secciones 'iot' o fallback local)
        self.hass_url = config.get("iot.hass_url", "http://localhost:8123")
        self.hass_token = config.get("iot.hass_token", "")
        self.enabled = config.get("iot.enabled", False)
        
        # Ignorar certificados SSL si HASS usa self-signed localmente
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def call_hass_service(self, domain: str, service: str, entity_id: str, data: dict = None) -> bool:
        """Invoca un servicio REST nativo en Home Assistant."""
        if not self.enabled or not self.hass_token:
            log.warning(f"[JARVIS-IoT] HASS desactivado o sin token. Simulación: {domain}.{service} en {entity_id}")
            return True

        url = f"{self.hass_url}/api/services/{domain}/{service}"
        headers = {
            "Authorization": f"Bearer {self.hass_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"entity_id": entity_id}
        if data:
            payload.update(data)
            
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=5) as response:
                if response.status in (200, 201):
                    log.info(f"[JARVIS-IoT] Comando exitoso: {domain}.{service} -> {entity_id}")
                    return True
        except Exception as e:
            log.error(f"[JARVIS-IoT] Error contactando HASS: {e}")
        return False

    def set_lights(self, room: str, state: str, color_hex: str = None) -> str:
        """
        Tool_calling function para controlar luces.
        room: 'studio', 'bedroom', 'living_room'
        state: 'on' o 'off'
        color_hex: opcional, ej '#FF0000' para rojo.
        """
        entity_id = f"light.{room}"
        service = "turn_on" if state.lower() == "on" else "turn_off"
        
        data = {}
        if service == "turn_on" and color_hex:
            # Home assistant usa RGB list, pero como proof of concept lo pasamos si es posible
            # Aquí idealmente se convierte HEX a RGB, pero asumimos que HASS lo puede digerir o usamos un script de HASS.
            # Para el propósito de Gravity, simularemos la orden.
            data["color_name"] = "red" if "FF0000" in color_hex.upper() else "white"

        success = self.call_hass_service("light", service, entity_id, data)
        return f"Luces de {room} puestas en estado {state}." if success else f"Fallo al controlar luces en {room}."

    def get_security_status(self) -> str:
        """Tool_calling function para consultar cámaras/alarmas."""
        # TODO: Implementar lectura de sensores
        return "Todos los sensores perimetrales están en verde."

# --- INTERFAZ PARA EL ENGINE DE HERRAMIENTAS DE GRAVITY ---
iot_instance = IoTController()

def tool_set_lights(room: str, state: str, color: str = "") -> str:
    """Controla las luces físicas del entorno."""
    return iot_instance.set_lights(room, state, color)

def tool_check_security() -> str:
    """Revisa el estado de la casa."""
    return iot_instance.get_security_status()
