"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             GRAVITY AI — BASE API ROUTE MIXIN [Robustness Layer]             ║
║            Manejo Seguro de Payloads JSON, CORS y Respuestas HTTP            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
from typing import Any, Optional, Dict

log = logging.getLogger("gravity.api")


class BaseApiMixin:
    """
    Mixin base para proporcionar utilidades atómicas de serialización,
    lectura segura de requests y cabeceras CORS consistentes.
    """

    def _send_cors(self) -> None:
        """Emite cabeceras estándar CORS para clientes web y extensiones."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: Any, status: int = 200, indent: Optional[int] = None) -> None:
        """
        Serializa y despacha una respuesta JSON con cabeceras CORS atómicas.
        Previene caídas por BrokenPipeError si el cliente cierra la conexión prematuramente.
        """
        try:
            body = json.dumps(data, indent=indent, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, BrokenPipeError):
            log.debug(f"[BaseApiMixin] Cliente cerró socket prematuramente en respuesta HTTP {status}.")
        except Exception as e:
            log.error(f"[BaseApiMixin] Error serializando JSON (HTTP {status}): {e}")

    def _send_error(self, message: str, status: int = 400, details: Optional[Any] = None) -> None:
        """
        Despacha un error JSON estructurado con status HTTP acorde y cabeceras CORS.
        """
        err_payload: Dict[str, Any] = {"error": message}
        if details is not None:
            err_payload["details"] = details
        self._send_json(err_payload, status=status)

    def _read_json(self, max_bytes: int = 10 * 1024 * 1024) -> Optional[Dict[str, Any]]:
        """
        Lee y valida de forma segura el cuerpo JSON de una petición POST/PUT.
        - Valida que Content-Length sea un entero válido y no exceda max_bytes.
        - Captura json.JSONDecodeError y envía HTTP 400 automático.
        Retorna:
          dict parseado si es válido.
          None si ocurrió un error (en cuyo caso la respuesta de error ya fue enviada).
        """
        try:
            raw_len = self.headers.get("Content-Length", "0")
            try:
                content_len = int(raw_len)
            except (ValueError, TypeError):
                self._send_error("Cabecera Content-Length inválida", status=400)
                return None

            if content_len < 0:
                self._send_error("Content-Length no puede ser negativo", status=400)
                return None

            if content_len > max_bytes:
                self._send_error(f"Payload demasiado grande. Máximo permitido: {max_bytes} bytes", status=413)
                return None

            if content_len == 0:
                return {}

            raw_bytes = self.rfile.read(content_len)
            if len(raw_bytes) < content_len:
                self._send_error("Cuerpo de la petición truncado o incompleto", status=400)
                return None

            try:
                parsed = json.loads(raw_bytes.decode("utf-8", errors="replace"))
                if not isinstance(parsed, dict):
                    self._send_error("El cuerpo JSON debe ser un objeto/diccionario raíz", status=400)
                    return None
                return parsed
            except json.JSONDecodeError as jde:
                self._send_error("Sintaxis JSON inválida en el payload", status=400, details=str(jde))
                return None

        except (ConnectionResetError, BrokenPipeError):
            log.debug("[BaseApiMixin] Conexión abortada durante la lectura del body.")
            return None
        except Exception as e:
            log.error(f"[BaseApiMixin] Error no esperado leyendo payload: {e}")
            self._send_error("Error interno procesando cuerpo de la petición", status=500)
            return None
