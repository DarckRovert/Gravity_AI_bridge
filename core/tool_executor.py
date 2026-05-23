"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — TOOL EXECUTOR V15.0 PRO [Diamond Edition]   ║
║     Analiza outputs de la IA y ejecuta tools automáticamente ║
╚══════════════════════════════════════════════════════════════╝

Registry y orquestador centralizado de herramientas.
Garantiza exclusión mutua mediante RLock de la ejecución de código y tools concurrentes.
"""

import re
import threading
from typing import Dict, Any, List, Tuple

from tools.code_runner import CodeRunner
from tools.web_search  import WebSearch
from tools.git_tool    import GitTool, FileOpsTool
from tools.file_edit_v2 import FileEditV2

# Cerrojo reentrante global para la exclusión mutua de ejecución concurrente de herramientas
_executor_lock: threading.RLock = threading.RLock()


class ToolExecutor:
    """
    Registry y orquestador de herramientas disponibles para la IA o el usuario.
    """
    def __init__(self) -> None:
        self.tools: Dict[str, Any] = {
            "code_runner": CodeRunner(),
            "web_search":  WebSearch(),
            "git_tool":    GitTool(),
            "file_ops":    FileOpsTool(),
            "file_edit":   FileEditV2(),
        }

    def execute_tool(self, tool_name: str, **kwargs: Any) -> Tuple[bool, str]:
        """Ejecuta una herramienta y devuelve (éxito, output) de forma thread-safe."""
        with _executor_lock:
            tool = self.tools.get(tool_name)
            if not tool:
                return False, f"Herramienta '{tool_name}' no encontrada."

            res = tool.execute(**kwargs)
            if res.success:
                return True, res.stdout or "Ejecución exitosa sin output."
            return False, res.stderr or str(res.stdout)

    def parse_and_execute_all(self, ai_response: str) -> List[Tuple[str, bool, str]]:
        """
        Escanea la respuesta en busca de comandos incrustados (forma nativa/fall-back
        si el modelo no usa JSON function calling puro).
        Sintaxis detectada: {{ tool: web_search | query: "error python" }}
        Retorna lista de (tool_name, success, output).
        """
        results: List[Tuple[str, bool, str]] = []
        pattern = r"\{\{\s*tool:\s*(\w+)\s*\|\s*(.*?)\s*\}\}"
        matches = re.finditer(pattern, ai_response)

        with _executor_lock:
            for m in matches:
                tname: str = m.group(1).strip()
                args_str: str = m.group(2).strip()

                # Parse simple kwargs (k: v)
                kwargs: Dict[str, Any] = {}
                for pair in re.split(r"\|(?!\|)", args_str):  # split by pipe
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        kwargs[k.strip()] = v.strip().strip('"\'')

                succ, out = self.execute_tool(tname, **kwargs)
                results.append((tname, succ, out))

        return results

    def run_first_code_block(self, ai_response: str, language: str = "") -> Tuple[bool, str]:
        """Helper extraído del propio code runner para uso directo del comando !run de forma thread-safe."""
        with _executor_lock:
            res = self.tools["code_runner"].execute_from_text(ai_response, language)
            return res.success, res.stdout if res.success else res.stderr

    def apply_patch(self, ai_response: str) -> Tuple[bool, str]:
        """Helper extraído del file ops para aplicar !apply-patch de forma thread-safe."""
        with _executor_lock:
            res = self.tools["file_ops"].execute(action="apply", response=ai_response)
            return res.success, res.stdout if res.success else res.stderr


# Instancia singleton para uso general
executor: ToolExecutor = ToolExecutor()

