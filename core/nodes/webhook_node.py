import json
import urllib.request
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register

class WebhookNode(GravityNode):
    """
    Envía peticiones HTTP a APIs externas.
    Inputs requeridos:
      - url: URL del webhook o API.
    Inputs opcionales:
      - method: "POST" o "GET" (default: "POST").
      - headers: Diccionario de cabeceras HTTP.
      - payload: Diccionario o texto a enviar en el cuerpo de la petición.
    """
    
    NODE_TYPE = "Webhook"
    DESCRIPTION = "Envía peticiones HTTP a APIs externas."
    INPUT_SCHEMA = {
        "url": "TEXT",
        "method": "TEXT",
        "headers": "JSON",
        "payload": "ANY"
    }
    OUTPUT_SCHEMA = {
        "status_code": "INT",
        "response_text": "TEXT",
        "response_json": "JSON"
    }
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        url = inputs.get("url")
        method = inputs.get("method", "POST").upper()
        headers = inputs.get("headers", {"Content-Type": "application/json"})
        payload = inputs.get("payload", {})

        if not url:
            raise ValueError(f"[{self.node_id}] URL de webhook no especificada.")

        log.info(f"[{self.__class__.__name__}] Disparando Webhook {method} -> {url}")

        data = None
        if method in ["POST", "PUT", "PATCH"]:
            if isinstance(payload, dict):
                data = json.dumps(payload).encode("utf-8")
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"
            elif isinstance(payload, str):
                data = payload.encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                resp_text = response.read().decode("utf-8", errors="ignore")
                status = response.getcode()
                
                # Attempt to parse json response
                try:
                    resp_json = json.loads(resp_text)
                except Exception:
                    resp_json = {}

                return {
                    "status_code": status,
                    "response_text": resp_text,
                    "response_json": resp_json
                }
        except urllib.error.URLError as e:
            log.error(f"[{self.__class__.__name__}] Error en Webhook: {e}")
            raise RuntimeError(f"Error HTTP en WebhookNode: {e}")
