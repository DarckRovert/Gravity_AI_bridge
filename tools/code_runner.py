"""
Gravity AI — Code Runner Tool V16.0 PRO
Executes code blocks extracted from AI responses in an isolated subprocess.
Supports: Python, JavaScript (Node.js), PowerShell, Bash.
"""

import re
import os
import sys
import tempfile
import subprocess
from typing import Any
from tools.base_tool import Tool, ToolResult

TIMEOUT_SECS = 30
MAX_OUTPUT = 8000  # chars truncation limit


def _extract_blocks(text: str) -> list[tuple[str, str]]:
    """
    Extracts all fenced code blocks from text.
    Returns list of (language, code) tuples.
    """
    pattern = r"```([a-zA-Z0-9_\-\+]*)[ \t]*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang.lower() or "python", code.strip()) for lang, code in matches]


def _find_executable(name: str) -> str | None:
    """Returns the full path if executable is available, else None."""
    import shutil

    return shutil.which(name)


class CodeRunner(Tool):
    """
    Herramienta que ejecuta bloques de código extraídos de respuestas de IA en subprocesos aislados.
    Soporta Python, JavaScript (Node.js), PowerShell y Bash.
    """

    name: str = "code_runner"
    description: str = (
        "Ejecuta bloques de código de respuestas de IA en un subproceso seguro"
    )
    requires_confirmation: bool = True

    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = TIMEOUT_SECS,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Ejecuta un bloque de código en el lenguaje especificado dentro de un subproceso seguro.
        """
        lang = language.lower().strip()

        # Map language aliases
        lang_map = {
            "py": "python",
            "python3": "python",
            "js": "javascript",
            "node": "javascript",
            "ps1": "powershell",
            "pwsh": "powershell",
            "sh": "bash",
            "shell": "bash",
            "zsh": "bash",
        }
        lang = lang_map.get(lang, lang)

        runner_map = {
            "python": self._run_python,
            "javascript": self._run_javascript,
            "powershell": self._run_powershell,
            "bash": self._run_bash,
        }

        runner = runner_map.get(lang)
        if not runner:
            return ToolResult(
                success=False,
                stderr=f"Lenguaje '{language}' no soportado. "
                "Soportados: python, javascript, powershell, bash",
            )

        return runner(code, timeout)

    def _run_subprocess(
        self, cmd: list[str], input_data: str = "", timeout: int = TIMEOUT_SECS
    ) -> ToolResult:
        """
        Ejecuta un comando en un subproceso del sistema, gestionando timeouts y flags de ventana.
        """
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
            )
            stdout = result.stdout[:MAX_OUTPUT]
            stderr = result.stderr[:MAX_OUTPUT]
            return ToolResult(
                success=(result.returncode == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False, stderr=f"Timeout: el código tardó más de {timeout}s"
            )
        except FileNotFoundError as e:
            return ToolResult(success=False, stderr=f"Ejecutable no encontrado: {e}")
        except Exception as e:
            return ToolResult(success=False, stderr=str(e))

    def _run_python(self, code: str, timeout: int) -> ToolResult:
        """Ejecuta código Python guardándolo temporalmente en disco."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            fpath = f.name
        try:
            return self._run_subprocess([sys.executable, fpath], timeout=timeout)
        finally:
            try:
                os.unlink(fpath)
            except Exception:
                pass

    def _run_javascript(self, code: str, timeout: int) -> ToolResult:
        """Ejecuta código JavaScript (Node.js) guardándolo temporalmente en disco."""
        node = _find_executable("node") or _find_executable("nodejs")
        if not node:
            return ToolResult(
                success=False,
                stderr="Node.js no encontrado. Instálalo para ejecutar JS.",
            )
        with tempfile.NamedTemporaryFile(
            suffix=".js", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            fpath = f.name
        try:
            return self._run_subprocess([node, fpath], timeout=timeout)
        finally:
            try:
                os.unlink(fpath)
            except Exception:
                pass

    def _run_powershell(self, code: str, timeout: int) -> ToolResult:
        """Ejecuta código PowerShell directamente mediante CLI."""
        pwsh = _find_executable("pwsh") or _find_executable("powershell")
        if not pwsh:
            return ToolResult(success=False, stderr="PowerShell no encontrado.")
        return self._run_subprocess(
            [pwsh, "-NoProfile", "-Command", code], timeout=timeout
        )

    def _run_bash(self, code: str, timeout: int) -> ToolResult:
        """Ejecuta comandos Bash (usando WSL o Git Bash en Windows, o nativo en Unix)."""
        if sys.platform == "win32":
            # Try WSL or Git Bash
            wsl = _find_executable("wsl")
            if wsl:
                return self._run_subprocess([wsl, "bash", "-c", code], timeout=timeout)
            bash = _find_executable("bash")
            if bash:
                return self._run_subprocess([bash, "-c", code], timeout=timeout)
            return ToolResult(
                success=False, stderr="bash no disponible en Windows sin WSL."
            )
        return self._run_subprocess(["bash", "-c", code], timeout=timeout)

    def execute_from_text(
        self, ai_response: str, lang_filter: str = "", timeout: int = TIMEOUT_SECS
    ) -> ToolResult:
        """
        Extracts the first matching code block from an AI response and executes it.
        lang_filter: if set, only blocks of that language are considered.
        """
        blocks = _extract_blocks(ai_response)
        if not blocks:
            return ToolResult(
                success=False,
                stderr="No se encontró ningún bloque de código en la respuesta.",
            )
        if lang_filter:
            blocks = [(l, c) for l, c in blocks if l == lang_filter.lower()]  # noqa: E741
            if not blocks:
                return ToolResult(
                    success=False,
                    stderr=f"No hay bloque '{lang_filter}' en la respuesta.",
                )
        lang, code = blocks[0]
        return self.execute(code=code, language=lang, timeout=timeout)
