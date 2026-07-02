"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — TOOL EXECUTOR V16.0 PRO [Diamond Edition]   ║
║     Analiza outputs de la IA y ejecuta tools automáticamente ║
╚══════════════════════════════════════════════════════════════╝

Registry y orquestador centralizado de herramientas.
Garantiza exclusión mutua mediante RLock de la ejecución de código y tools concurrentes.
"""

import re
import threading
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, List, Tuple

log = logging.getLogger("gravity.tool_executor")

from tools.code_runner import CodeRunner  # noqa: E402
from tools.web_search import WebSearch  # noqa: E402
from tools.git_tool import GitTool, FileOpsTool  # noqa: E402
from tools.file_edit_v2 import FileEditV2  # noqa: E402

# Cerrojo reentrante global para la exclusión mutua de ejecución concurrente de herramientas
_executor_lock: threading.RLock = threading.RLock()


class ToolExecutor:
    """
    Registry y orquestador de herramientas disponibles para la IA o el usuario.
    """

    def __init__(self) -> None:
        self.tools: Dict[str, Any] = {
            "code_runner": CodeRunner(),
            "web_search": WebSearch(),
            "git_tool": GitTool(),
            "file_ops": FileOpsTool(),
            "file_edit": FileEditV2(),
        }

    def execute_tool(self, tool_name: str, bg_mode: bool = False, **kwargs: Any) -> Tuple[bool, str]:
        """Ejecuta una herramienta y devuelve (éxito, output) de forma thread-safe."""
        with _executor_lock:
            tool = self.tools.get(tool_name)
            if not tool:
                return False, f"Herramienta '{tool_name}' no encontrada."

            # -- Fase 12: HITL Bypass Mitigation --
            # Si la herramienta de la IA es peligrosa (ej. code_runner), forzamos la intercepción.
            if getattr(tool, "requires_confirmation", False):
                from core.hitl_manager import intercept
                hitl_res = intercept(
                    tool_name=tool_name, 
                    arguments=kwargs, 
                    session_id="tool_executor",
                    bg_mode=bg_mode
                )
                if not hitl_res.get("proceed", False):
                    # Fase 13: AST Sandbox Bypass para Daemons
                    if bg_mode and tool_name == "code_runner":
                        code = kwargs.get("code", "")
                        lang = kwargs.get("language", "python").lower()
                        if lang not in ["python", "py", "python3"]:
                            return False, "AST Sandbox solo soporta Python en background mode. Rechazado."
                        
                        from core.ast_sandbox import is_code_safe
                        is_safe, reason = is_code_safe(code)
                        if is_safe:
                            log.info("[ToolExecutor] HITL Auto-aprobado por AST Sandbox: Código de Python Seguro.")
                        else:
                            log.warning(f"[ToolExecutor] AST Sandbox Bloqueó ejecución: {reason}")
                            return False, f"Error: AST Sandbox rechazó el código ({reason})"
                    else:
                        reason = hitl_res.get("decision", "rejected")
                        log.warning(f"[ToolExecutor] Ejecución de '{tool_name}' RECHAZADA por HITL ({reason})")
                        return False, f"Error: Ejecución rechazada por el administrador ({reason})."

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
                        kwargs[k.strip()] = v.strip().strip("\"'")

                succ, out = self.execute_tool(tname, **kwargs)
                results.append((tname, succ, out))

        return results

    def run_first_code_block(
        self, ai_response: str, language: str = ""
    ) -> Tuple[bool, str]:
        """Helper extraído del propio code runner para uso directo del comando !run de forma thread-safe."""
        with _executor_lock:
            # --- V16.5 PRO: Active Sandboxing ---
            try:
                # Comprobar si docker está disponible en el host
                subprocess.run(
                    ["docker", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # Extraemos el código
                match = re.search(
                    r"```(?:python|py)?\s*(.*?)```",
                    ai_response,
                    re.DOTALL | re.IGNORECASE,
                )
                code_to_run = match.group(1).strip() if match else ai_response.strip()

                with tempfile.TemporaryDirectory() as tmpdir:
                    script_path = os.path.join(tmpdir, "sandbox.py")
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(code_to_run)

                    log.info(
                        "[ToolExecutor] Ejecutando código en Docker Sandbox seguro..."
                    )
                    res = subprocess.run(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "--network",
                            "none",
                            "-m",
                            "512m",
                            "-v",
                            f"{tmpdir}:/sandbox",
                            "python:3.10-slim",
                            "python",
                            "/sandbox/sandbox.py",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )

                    if res.returncode == 0:
                        return True, f"[Docker Sandbox] {res.stdout}"
                    else:
                        return False, f"[Sandbox Error] {res.stderr or res.stdout}"
            except Exception as e:
                log.debug(
                    f"[ToolExecutor] Sandboxing falló o no disponible ({e}). Usando fallback local."
                )

            # --- Fallback Local ---
            res = self.tools["code_runner"].execute_from_text(ai_response, language)
            return res.success, res.stdout if res.success else res.stderr

    def apply_patch(self, ai_response: str) -> Tuple[bool, str]:
        """Helper extraído del file ops para aplicar !apply-patch de forma thread-safe."""
        with _executor_lock:
            res = self.tools["file_ops"].execute(action="apply", response=ai_response)
            return res.success, res.stdout if res.success else res.stderr


# Instancia singleton para uso general
executor: ToolExecutor = ToolExecutor()
