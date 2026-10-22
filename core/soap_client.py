"""
=============================================================================
        GRAVITY AI — AZEROTHCORE SOAP CLIENT V1.0 PRO [WotLK 3.3.5a]
        Conector SOAP de Alta Precisión para AzerothCore / TrinityCore
=============================================================================
Módulo que empaqueta y despacha peticiones HTTP SOAP hacia la consola de
AzerothCore. Diseñado para operar sobre túnel SSH seguro o red interna.
"""

import os
import re
import time
import base64
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

log = logging.getLogger("gravity.soap")


class AzerothCoreSOAPClient:
    """
    Cliente SOAP oficial para administración remota de AzerothCore (WotLK 3.3.5a).
    Soporta autenticación HTTP Basic (Capa 2: GM Rango 3) y manejo de namespaces.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7878,
        username: str = "",
        password: str = "",
        timeout: float = 12.0,
        namespace: str = "urn:AC",
    ) -> None:
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.timeout = float(timeout)
        self.namespace = namespace
        self.url = f"http://{self.host}:{self.port}/"

    def _build_envelope(self, command: str, ns: str) -> str:
        """Construye el sobre XML SOAP para executeCommand con escapado de entidades."""
        clean_cmd = (
            command.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">\n'
            "  <SOAP-ENV:Body>\n"
            f'    <ns1:executeCommand xmlns:ns1="{ns}">\n'
            f"      <command>{clean_cmd}</command>\n"
            "    </ns1:executeCommand>\n"
            "  </SOAP-ENV:Body>\n"
            "</SOAP-ENV:Envelope>"
        )

    def execute_command(self, command: str, retry_alt_ns: bool = True) -> Dict[str, Any]:
        """
        Despacha un comando a la consola de AzerothCore y retorna el resultado sincrónico.
        """
        if not command or not command.strip():
            return {"ok": False, "error": "Comando vacío", "result": ""}

        command = command.strip()
        auth_bytes = f"{self.username}:{self.password}".encode("utf-8")
        auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

        envelope = self._build_envelope(command, self.namespace)
        headers = {
            "Content-Type": "application/xml; charset=utf-8",
            "Authorization": auth_header,
            "User-Agent": "GravityAI-Bridge/30.0 (AzerothCore SOAP Client)",
            "Connection": "close",
        }

        t_start = time.time()
        try:
            req = urllib.request.Request(
                self.url,
                data=envelope.encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.status
                raw_body = resp.read().decode("utf-8", errors="replace")
                latency_ms = round((time.time() - t_start) * 1000, 2)

                # Extraer <result>...</result>
                res_match = re.search(r"<result>(.*?)</result>", raw_body, re.DOTALL)
                if res_match:
                    result_text = res_match.group(1).strip()
                    result_text = (
                        result_text.replace("&lt;", "<")
                        .replace("&gt;", ">")
                        .replace("&amp;", "&")
                        .replace("&quot;", '"')
                        .replace("&apos;", "'")
                    )
                    return {
                        "ok": True,
                        "result": result_text,
                        "latency_ms": latency_ms,
                        "status_code": status_code,
                        "command": command,
                    }

                # Si no hay <result>, verificar si hay fallo XML
                fault_match = re.search(r"<faultstring>(.*?)</faultstring>", raw_body, re.DOTALL)
                err_msg = fault_match.group(1).strip() if fault_match else "Respuesta SOAP sin etiqueta result"

                # Reintento con namespace alternativo (ej. urn:TC si urn:AC fue rechazado)
                if retry_alt_ns and self.namespace == "urn:AC":
                    log.warning(f"[SOAP] Fallo con urn:AC ({err_msg}). Reintentando con urn:TC...")
                    self.namespace = "urn:TC"
                    return self.execute_command(command, retry_alt_ns=False)

                return {
                    "ok": False,
                    "error": err_msg,
                    "raw_response": raw_body,
                    "latency_ms": latency_ms,
                    "status_code": status_code,
                    "command": command,
                }

        except urllib.error.HTTPError as he:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            err_body = he.read().decode("utf-8", errors="replace") if he.fp else ""
            fault_match = re.search(r"<faultstring>(.*?)</faultstring>", err_body, re.DOTALL)
            err_desc = fault_match.group(1).strip() if fault_match else str(he)

            if he.code == 401:
                return {
                    "ok": False,
                    "error": "401 Unauthorized: Credenciales GM incorrectas o cuenta sin SecurityLevel >= 3.",
                    "latency_ms": latency_ms,
                    "status_code": 401,
                    "command": command,
                }
            return {
                "ok": False,
                "error": f"HTTP {he.code}: {err_desc}",
                "latency_ms": latency_ms,
                "status_code": he.code,
                "command": command,
            }

        except urllib.error.URLError as ue:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            return {
                "ok": False,
                "error": f"Error de conexión a SOAP ({self.url}): {ue.reason}. ¿El túnel SSH está activo?",
                "latency_ms": latency_ms,
                "status_code": 0,
                "command": command,
            }

        except Exception as ex:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            return {
                "ok": False,
                "error": f"Excepción inesperada en llamada SOAP: {str(ex)}",
                "latency_ms": latency_ms,
                "status_code": 0,
                "command": command,
            }

    def test_connection(self) -> Dict[str, Any]:
        """Envía .server info para verificar liveness y nivel GM3."""
        return self.execute_command(".server info")


# ── Singleton facade ────────────────────────────────────────────────────────────
_soap: "AzerothCoreSOAPClient | None" = None
_soap_lock = __import__("threading").Lock()


def _load_wow_cfg_soap() -> dict:
    try:
        from core.config_manager import config
        gs = config.get("game_servers", {})
        if not isinstance(gs, dict):
            gs = {}
        return gs.get("wow_peru", {})
    except Exception:
        return {}


def _get_soap() -> "AzerothCoreSOAPClient":
    global _soap
    with _soap_lock:
        if _soap is None:
            wow = _load_wow_cfg_soap()
            _soap = AzerothCoreSOAPClient(
                host=wow.get("soap_host", "127.0.0.1"),
                port=int(wow.get("soap_port", 7878)),
                username=wow.get("soap_user", ""),
                password=wow.get("soap_pass", ""),
                namespace=wow.get("soap_namespace", "urn:AC"),
            )
    return _soap


def execute_command(command: str) -> dict:
    """Ejecuta un comando GM via SOAP (interfaz de módulo)."""
    return _get_soap().execute_command(command)


def test_connection() -> dict:
    """Verifica liveness del servidor via SOAP (.server info)."""
    return _get_soap().test_connection()

