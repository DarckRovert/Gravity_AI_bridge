"""
Gravity AI — MCP Adapter V9.0 PRO (Claw Edition)
Puente de comunicación para el Model Context Protocol (MCP).
Permite integrar herramientas y recursos de servidores MCP externos.
"""
import json
import subprocess
import threading
from typing import Dict, Any, List, Optional


class MCPAdapter:
    """
    Adaptador para servidores MCP que operan a través de la terminal (stdio).
    """

    def __init__(self, server_path: str, args: List[str] = []):
        self.server_path = server_path
        self.args = args
        self.process: Optional[subprocess.Popen] = None
        self._id_counter = 1

    def connect(self) -> bool:
        """Inicia el proceso del servidor MCP."""
        try:
            cmd = [self.server_path] + self.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1
            )
            # Verificar si el proceso sigue vivo
            if self.process.poll() is not None:
                return False
            return True
        except Exception:
            return False

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una llamada a una herramienta del servidor MCP mediante JSON-RPC."""
        if not self.process:
            return {"error": "Servidor MCP no conectado"}

        request = {
            "jsonrpc": "2.0",
            "id": self._id_counter,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        self._id_counter += 1

        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            line = self.process.stdout.readline()
            if not line:
                return {"error": "Respuesta vacía del servidor MCP"}
            
            return json.loads(line)
        except Exception as e:
            return {"error": f"Fallo en comunicación MCP: {str(e)}"}

    def list_tools(self) -> List[Dict[str, Any]]:
        """Solicita la lista de herramientas disponibles al servidor MCP."""
        if not self.process:
            return []

        request = {
            "jsonrpc": "2.0",
            "id": self._id_counter,
            "method": "tools/list",
            "params": {}
        }
        self._id_counter += 1

        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            
            line = self.process.stdout.readline()
            response = json.loads(line)
            return response.get("result", {}).get("tools", [])
        except Exception:
            return []

    def disconnect(self):
        """Detiene el servidor MCP."""
        if self.process:
            self.process.terminate()
            self.process = None
