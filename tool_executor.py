"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — TOOL EXECUTOR V7.0                          ║
║     Analiza outputs de la IA y ejecuta tools automáticamente ║
╚══════════════════════════════════════════════════════════════╝
"""
import re
from tools.code_runner import CodeRunner
from tools.web_search  import WebSearch
from tools.git_tool    import GitTool, FileOpsTool


class ToolExecutor:
    """
    Registry y orquestador de herramientas disponibles para la IA o el usuario.
    """
    def __init__(self):
        self.tools = {
            "code_runner": CodeRunner(),
            "web_search":  WebSearch(),
            "git_tool":    GitTool(),
            "file_ops":    FileOpsTool(),
        }

    def execute_tool(self, tool_name: str, **kwargs) -> tuple[bool, str]:
        """Ejecuta una herramienta y devuelve (éxito, output)."""
        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Herramienta '{tool_name}' no encontrada."

        res = tool.execute(**kwargs)
        if res.success:
            return True, res.stdout or "Ejecución exitosa sin output."
        return False, res.stderr or str(res.stdout)

    def parse_and_execute_all(self, ai_response: str) -> list[tuple[str, bool, str]]:
        """
        Escanea la respuesta en busca de comandos incrustados (forma nativa/fall-back
        si el modelo no usa JSON function calling puro).
        Sintaxis detectada: {{ tool: web_search | query: "error python" }}
        Retorna lista de (tool_name, success, output).
        """
        results = []
        pattern = r"\{\{\s*tool:\s*(\w+)\s*\|\s*(.*?)\s*\}\}"
        matches = re.finditer(pattern, ai_response)

        for m in matches:
            tname = m.group(1).strip()
            args_str = m.group(2).strip()

            # Parse simple kwargs (k: v)
            kwargs = {}
            for pair in re.split(r"\|(?!\|)", args_str):  # split by pipe
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    kwargs[k.strip()] = v.strip().strip('"\'')

            succ, out = self.execute_tool(tname, **kwargs)
            results.append((tname, succ, out))

        return results

    def run_first_code_block(self, ai_response: str, language: str = "") -> tuple[bool, str]:
        """Helper extraído del propio code runner para uso directo del comando !run"""
        res = self.tools["code_runner"].execute_from_text(ai_response, language)
        return res.success, res.stdout if res.success else res.stderr

    def apply_patch(self, ai_response: str) -> tuple[bool, str]:
        """Helper extraído del file ops para aplicar !apply-patch"""
        res = self.tools["file_ops"].execute(action="apply", response=ai_response)
        return res.success, res.stdout if res.success else res.stderr


# Instancia singleton para uso general
executor = ToolExecutor()
