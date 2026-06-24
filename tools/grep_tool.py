"""
Gravity AI — Capa de Herramientas: Buscador de Patrones Avanzado (GrepTool)
Estándar: Diamond-Tier (Tipado estricto, evasión de CMD en Windows y algoritmos de resiliencia).
"""

import os
import re
import sys
import time
import subprocess
import json
import fnmatch
from typing import List, Dict, Any, Optional
from tools.base_tool import Tool, ToolResult


class GrepTool(Tool):
    """
    Herramienta avanzada de búsqueda y localización de texto inspirada en Claude Code / ripgrep.
    Optimiza el consumo de tokens limitando la salida y realiza un fallback nativo en Python
    si el ejecutable 'rg' no está instalado en el sistema.
    """

    name: str = "grep_search"
    description: str = (
        "Busca patrones de texto en el sistema de archivos. "
        "Soporta Regex, filtros por glob y límites de resultados."
    )
    requires_confirmation: bool = False

    def execute(
        self,
        pattern: str,
        path: str = ".",
        glob: Optional[str] = None,
        case_insensitive: bool = True,
        multiline: bool = False,
        head_limit: int = 250,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Ejecuta la búsqueda de patrones mediante ripgrep o fallback de Python.

        Parámetros:
            pattern (str): Expresión regular o cadena de texto a buscar.
            path (str): Directorio raíz de inicio de la búsqueda.
            glob (Optional[str]): Filtro de archivos mediante patrones glob (ej. '*.py').
            case_insensitive (bool): Ignorar mayúsculas y minúsculas si es True.
            multiline (bool): Permitir que los patrones de búsqueda coincidan entre varias líneas.
            head_limit (int): Número máximo de coincidencias individuales antes de truncar la salida.
            **kwargs: Parámetros del mapa dinámico de argumentos.

        Retorna:
            ToolResult: Coincidencias estructuradas y metadatos del proceso.
        """
        # 1. Intentar usar Ripgrep (rg) si está disponible en el PATH del sistema
        try:
            cmd: List[str] = ["rg", "--json"]
            if case_insensitive:
                cmd.append("-i")
            if multiline:
                cmd.append("-U")
            if glob:
                cmd.extend(["-g", glob])

            cmd.extend([pattern, path])

            # Impedir el parpadeo y la apertura de ventanas cmd adicionales en entornos Windows
            creationflags: int = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            # Ejecución asíncrona de Ripgrep
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=creationflags,
            )
            stdout, stderr = process.communicate(timeout=15)

            # Código 0 representa éxito, código 1 representa cero coincidencias sin error fatal
            if process.returncode in (0, 1):
                return self._parse_rg_json(stdout, head_limit)

        except subprocess.TimeoutExpired:
            process.kill()
            return ToolResult(
                success=False,
                stderr="Error: El proceso de búsqueda 'ripgrep' superó el timeout de 15 segundos.",
            )
        except FileNotFoundError:
            # Fallback transparente y robusto en puro Python si 'rg' no está instalado en la terminal actual
            return self._python_fallback_search(
                pattern, path, glob, case_insensitive, head_limit
            )
        except Exception as e:
            return ToolResult(
                success=False,
                stderr=f"Error inesperado al ejecutar grep_tool: {str(e)}",
            )

        return self._python_fallback_search(
            pattern, path, glob, case_insensitive, head_limit
        )

    def _parse_rg_json(self, json_output: str, limit: int) -> ToolResult:
        """
        Analiza sintácticamente la salida JSON estructurada que produce ripgrep.

        Parámetros:
            json_output (str): Salida completa de ripgrep --json.
            limit (int): Límite superior de elementos a incluir.

        Retorna:
            ToolResult: Listado formateado de coincidencias.
        """
        matches: List[str] = []
        count: int = 0

        for line in json_output.splitlines():
            if not line:
                continue
            try:
                data: Dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue

            if data.get("type") == "match":
                count += 1
                if count > limit:
                    break

                match_data = data.get("data", {})
                path_text: str = match_data.get("path", {}).get("text", "desconocido")
                line_number: int = match_data.get("line_number", 0)
                content: str = match_data.get("lines", {}).get("text", "").strip()
                matches.append(f"{path_text}:{line_number}: {content}")

        output: str = "\n".join(matches)
        if count > limit:
            output += f"\n\n[AVISO] Se alcanzó el límite de {limit} resultados. Refina la búsqueda."

        return ToolResult(
            success=True,
            stdout=output if matches else "No se encontraron coincidencias.",
            data={"match_count": count},
        )

    def _python_fallback_search(
        self,
        pattern: str,
        path: str,
        glob_pat: Optional[str],
        case_insensitive: bool,
        limit: int,
        wall_timeout: float = 12.0,
    ) -> ToolResult:
        """
        Implementación pura en Python de recorrido y filtrado de expresiones regulares.
        Respeta un timeout de pared (`wall_timeout`) para evitar cuelgues en repos grandes.

        Parámetros:
            pattern (str): Expresión regular.
            path (str): Directorio raíz.
            glob_pat (Optional[str]): Filtro de tipo *.extension.
            case_insensitive (bool): Distinguir o ignorar mayúsculas.
            limit (int): Límite de coincidencia para proteger memoria y tokens.
            wall_timeout (float): Máximo de segundos permitidos antes de truncar (default 12s).

        Retorna:
            ToolResult: Listado formateado con metadatos del fallback.
        """
        matches: List[str] = []
        count: int = 0
        regex_flags: int = re.IGNORECASE if case_insensitive else 0
        deadline: float = time.monotonic() + wall_timeout
        timed_out: bool = False

        try:
            regex = re.compile(pattern, regex_flags)
        except re.error as e:
            return ToolResult(
                success=False,
                stderr=f"Expresión regular inválida en búsqueda fallback: {str(e)}",
            )

        for root, dirs, files in os.walk(path):
            if time.monotonic() > deadline:
                timed_out = True
                break
            # Optimizar recorrido podando directorios innecesarios o del entorno virtual
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ("node_modules", "__pycache__", "vendor", "_integrations")
            ]

            for file in files:
                if time.monotonic() > deadline:
                    timed_out = True
                    break
                if glob_pat and not fnmatch.fnmatch(file, glob_pat):
                    continue

                file_path: str = os.path.join(root, file)
                try:
                    # Usar errors='ignore' para evitar caídas en archivos binarios o encodings extraños
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                count += 1
                                if count <= limit:
                                    matches.append(f"{file_path}:{i}: {line.strip()}")
                                if count > limit:
                                    break
                except IOError:
                    # Saltar archivos sin permisos o bloqueados por el sistema operativo
                    continue

                if count > limit:
                    break
            if count > limit or timed_out:
                break

        output: str = "\n".join(matches)
        if timed_out:
            output += f"\n\n[AVISO] Búsqueda truncada: timeout de {wall_timeout:.0f}s alcanzado (Modo Fallback Python)."
        elif count > limit:
            output += f"\n\n[AVISO] Se alcanzó el límite de {limit} resultados (Modo Fallback Python)."

        return ToolResult(
            success=True,
            stdout=(
                output
                if matches
                else "No se encontraron coincidencias (Modo Fallback)."
            ),
            data={
                "match_count": count,
                "mode": "python_fallback",
                "timed_out": timed_out,
            },
        )
