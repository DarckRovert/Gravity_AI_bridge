"""
Gravity AI — Capa de Herramientas: Git y Operaciones de Archivos (GitTool & FileOpsTool)
Estándar: Diamond-Tier (Tipado estricto, robustez extrema ante I/O y control de procesos en Windows).
"""

import os
import re
import shutil
import subprocess
import sys
import difflib
from typing import Dict, List, Any, Optional
from tools.base_tool import Tool, ToolResult, safe_path_resolve


class GitTool(Tool):
    """
    Herramienta robusta de control de versiones Git.
    Proporciona operaciones seguras de estado, logs, diffs, ramas y stashes,
    garantizando la evasión de popups de consola en sistemas Windows mediante creationflags.
    """

    name: str = "git_tool"
    description: str = "Operaciones de Git: status, log, diff, branch, stash."

    def execute(self, operation: str = "status", **kwargs: Any) -> ToolResult:
        """
        Ejecuta la operación Git especificada con manejo seguro de subprocess y timeouts.

        Parámetros:
            operation (str): La acción a realizar ('status', 'log', 'diff', 'branch', 'stash').
            **kwargs: Parámetros adicionales (no utilizados actualmente).

        Retorna:
            ToolResult: El resultado de la operación incluyendo salida estándar y código de salida.
        """
        ops: Dict[str, List[str]] = {
            "status": ["git", "status", "--short"],
            "log": ["git", "log", "--oneline", "-15"],
            "diff": ["git", "diff", "HEAD"],
            "branch": ["git", "branch", "-a"],
            "stash": ["git", "stash"],
        }
        cmd: Optional[List[str]] = ops.get(operation)
        if not cmd:
            return ToolResult(
                success=False, stderr=f"Operación '{operation}' no soportada."
            )

        # Evitar ventanas emergentes de consola (CMD) en sistemas Windows
        creationflags: int = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=creationflags,
            )
            return ToolResult(
                success=(result.returncode == 0),
                stdout=result.stdout[:6000],
                stderr=result.stderr[:2000],
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                stderr=f"Error: Excedido el tiempo de espera de 10 segundos ejecutando 'git {operation}'.",
            )
        except Exception as e:
            return ToolResult(
                success=False, stderr=f"Error inesperado ejecutando Git: {str(e)}"
            )


class FileOpsTool(Tool):
    """
    Herramienta avanzada para operaciones complejas y seguras del sistema de archivos.
    Soporta creación de copias de seguridad de resiliencia, diffs unificados y aplicación
    estructurada de parches de código desde las respuestas del modelo.
    """

    name: str = "file_ops"
    description: str = (
        "Operaciones de archivo seguras: respaldos, diferencias y aplicación de parches."
    )
    requires_confirmation: bool = True

    def backup(self, path: str) -> ToolResult:
        """
        Crea una copia de seguridad con extensión '.gravity.bak' antes de realizar modificaciones.

        Parámetros:
            path (str): Ruta absoluta o relativa del archivo a respaldar.

        Retorna:
            ToolResult: Estatus de la copia de seguridad.
        """
        if not path or not os.path.exists(path):
            return ToolResult(
                success=False,
                stderr=f"El archivo especificado para respaldo no existe: '{path}'",
            )
        bak: str = path + ".gravity.bak"
        try:
            shutil.copy2(path, bak)
            return ToolResult(
                success=True, stdout=f"Copia de seguridad creada con éxito en: {bak}"
            )
        except IOError as e:
            return ToolResult(
                success=False,
                stderr=f"Error de E/S al crear copia de seguridad: {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                stderr=f"Error inesperado al crear copia de seguridad: {str(e)}",
            )

    def diff(self, original_path: str, new_content: str) -> ToolResult:
        """
        Genera una visualización de diferencias (diff unificado) entre un archivo y un nuevo contenido.

        Parámetros:
            original_path (str): Ruta al archivo original existente en disco.
            new_content (str): Cadena de texto que contiene el nuevo contenido propuesto.

        Retorna:
            ToolResult: Un diff legible en formato unificado de diferencias.
        """
        if not original_path or not os.path.exists(original_path):
            return ToolResult(
                success=False,
                stderr=f"El archivo original para comparar no existe: '{original_path}'",
            )
        try:
            with open(original_path, "r", encoding="utf-8", errors="replace") as f:
                orig: List[str] = f.readlines()
            new: List[str] = new_content.splitlines(keepends=True)
            diff_lines: List[str] = list(
                difflib.unified_diff(
                    orig, new, fromfile=original_path, tofile="[nuevo]"
                )
            )
            return ToolResult(
                success=True, stdout="".join(diff_lines[:200]), language="diff"
            )
        except IOError as e:
            return ToolResult(
                success=False,
                stderr=f"Error de E/S al leer '{original_path}': {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                success=False, stderr=f"Error inesperado al generar diff: {str(e)}"
            )

    def apply_patch(self, ai_response: str) -> ToolResult:
        """
        Analiza sintácticamente la respuesta de la IA para extraer y aplicar un parche estructurado.
        Busca patrones de bloques con formato '# Archivo: <ruta>' seguidos de bloques de código Markdown.

        Parámetros:
            ai_response (str): Respuesta de texto libre del modelo.

        Retorna:
            ToolResult: Estatus detallado de la aplicación del parche.
        """
        # Patrón 1: "# Archivo: <ruta>" seguido de bloque de código markdown
        match = re.search(
            r"#\s*[Aa]rchivo:\s*(.+?)\n```\w*\n(.*?)```", ai_response, re.DOTALL
        )
        if match:
            path: str = match.group(1).strip()
            code: str = match.group(2)
            
            # AgentShield Ring 0 protection
            try:
                path = safe_path_resolve(os.getcwd(), path, is_write=True)
            except Exception as e:
                return ToolResult(
                    success=False,
                    stderr=f"Cancelando parche: AgentShield bloqueó acceso a {path}: {str(e)}",
                )

            # Crear respaldo por resiliencia y seguridad
            backup_res: ToolResult = self.backup(path)
            if not backup_res.success and os.path.exists(path):
                return ToolResult(
                    success=False,
                    stderr=f"Cancelando aplicación de parche. No se pudo crear respaldo: {backup_res.stderr}",
                )

            try:
                # Asegurar directorios contenedores creados
                dir_name: str = os.path.dirname(os.path.abspath(path))
                os.makedirs(dir_name, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                return ToolResult(
                    success=True, stdout=f"✓ Parche aplicado exitosamente en {path}"
                )
            except IOError as e:
                return ToolResult(
                    success=False, stderr=f"Fallo de escritura en archivo: {str(e)}"
                )
            except Exception as e:
                return ToolResult(
                    success=False, stderr=f"Error inesperado aplicando parche: {str(e)}"
                )

        # Patrón 2: Bloques directos de diff unificados (no autoportados por el binario patch)
        diff_match = re.search(r"```diff\n(.*?)```", ai_response, re.DOTALL)
        if diff_match:
            return ToolResult(
                success=False,
                stderr="Diferencia de tipo 'diff' detectada. "
                "La aplicación automática de parches diff requiere utilidades externas de sistema. "
                "Por favor, aplique la edición manualmente o proporcione un bloque de código completo.",
            )

        return ToolResult(
            success=False,
            stderr="No se localizó un bloque de código aplicable en la respuesta. "
            "Formatos válidos: '# Archivo: <ruta>' seguido de un bloque de código en triple acento grave.",
        )

    def execute(self, action: str = "diff", **kwargs: Any) -> ToolResult:
        """
        Punto de entrada genérico para ejecutar acciones del FileOpsTool.

        Parámetros:
            action (str): Acción a realizar ('backup', 'diff', 'apply').
            **kwargs: Parámetros del mapa de argumentos dinámicos de ejecución.

        Retorna:
            ToolResult: Estatus y datos resultantes.
        """
        if action == "backup":
            return self.backup(kwargs.get("path", ""))
        elif action == "diff":
            return self.diff(kwargs.get("path", ""), kwargs.get("content", ""))
        elif action == "apply":
            return self.apply_patch(kwargs.get("response", ""))
        return ToolResult(
            success=False, stderr=f"Acción de sistema '{action}' no es reconocida."
        )
