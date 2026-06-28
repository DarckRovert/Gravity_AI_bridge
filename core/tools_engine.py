import os
import subprocess
import glob
import logging
import threading
import shlex
import re
from typing import Dict, Any, List, Optional

log = logging.getLogger("gravity.tools_engine")
_singleton_lock = threading.RLock()


class ToolEngine:
    """
    Motor de Herramientas (Agentic Core V16.0)
    Proporciona capacidades autónomas al LLM de Gravity para interactuar con el sistema operativo,
    sistema de archivos y ejecución de código con exclusión mutua estricta y resiliencia en Windows.
    """

    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self._lock = threading.RLock()
        self.tools = {
            "view_file": self.view_file,
            "replace_file_content": self.replace_file_content,
            "list_dir": self.list_dir,
            "run_command": self.run_command,
            "grep_search": self.grep_search,
        }

    def _safe_path(self, path: str, is_write: bool = False) -> str:
        """Verifica que la ruta esté dentro del workspace para evitar directory traversal."""
        abs_path_orig = os.path.abspath(os.path.join(self.workspace_root, path))
        abs_path_check = os.path.normcase(abs_path_orig)
        root_path_check = os.path.normcase(os.path.abspath(self.workspace_root))

        # Excepción para el despliegue del portal de noticias
        news_portal_check = os.path.normcase(os.path.abspath("F:/gravity-news-portal"))
        is_news_portal = abs_path_check.startswith(news_portal_check + os.sep) or abs_path_check == news_portal_check

        if (
            not abs_path_check.startswith(root_path_check + os.sep)
            and abs_path_check != root_path_check
            and not is_news_portal
        ):
            raise PermissionError(f"Ruta denegada (fuera del workspace): {path}")
            
        # AgentShield V16.5 Ring 0 Protection - Bloqueo de Lectura (Secretos)
        blocked_reads = [
            os.path.join(self.workspace_root, ".env"),
        ]
        for prot in blocked_reads:
            prot_check = os.path.normcase(os.path.abspath(prot))
            if abs_path_check == prot_check:
                raise PermissionError(f"AgentShield Core Protection blocked read attempt to secret-bearing path: {path}")
                
        # AgentShield V16.5 Ring 0 Protection - Bloqueo de Escritura
        if is_write:
            protected_paths = [
                os.path.join(self.workspace_root, "core"),
                os.path.join(self.workspace_root, ".agents"),
                os.path.join(self.workspace_root, "bridge_server.py"),
                os.path.join(self.workspace_root, "mcp_server.py"),
                os.path.join(self.workspace_root, "_settings.json"),
                os.path.join(self.workspace_root, "_knowledge.json"),
                os.path.join(self.workspace_root, "config.yaml"),
                os.path.join(self.workspace_root, ".env"),
            ]
            for prot in protected_paths:
                prot_check = os.path.normcase(os.path.abspath(prot))
                if abs_path_check.startswith(prot_check) or abs_path_check == prot_check:
                    raise PermissionError(f"AgentShield Core Protection blocked write attempt to system critical path: {path}")

        return abs_path_orig

    def _sanitize_unicode(self, text: str) -> str:
        """[AgentShield V16.0] Anti-Prompt Injection: Strip hidden unicode chars, zero-width spaces, and bidi overrides."""
        # Strips: \u200B-\u200D (zero-width), \u2060 (word joiner), \uFEFF (BOM), \u202A-\u202E (Bidi)
        pattern = re.compile(r'[\u200B\u200C\u200D\u2060\uFEFF\u202A-\u202E]')
        return pattern.sub('', text)

    def _read_file_with_fallback(self, safe_path: str) -> str:
        """Intenta leer un archivo con codificación utf-8, con fallback a cp1252 y latin-1."""
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                with open(safe_path, "r", encoding=encoding) as f:
                    return self._sanitize_unicode(f.read())
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            0,
            f"No se pudo decodificar {safe_path} con utf-8, cp1252 ni latin-1.",
        )

    def _read_lines_with_fallback(self, safe_path: str) -> List[str]:
        """Intenta leer las líneas de un archivo con codificación utf-8, con fallback a cp1252 y latin-1."""
        for encoding in ("utf-8", "cp1252", "latin-1"):
            try:
                with open(safe_path, "r", encoding=encoding) as f:
                    return [self._sanitize_unicode(line) for line in f.readlines()]
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            0,
            f"No se pudo decodificar {safe_path} con utf-8, cp1252 ni latin-1.",
        )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Retorna el esquema JSON de las herramientas para inyectar en el LLM prompt."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "view_file",
                    "description": "Lee el contenido de un archivo. Usa start_line y end_line para archivos grandes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Ruta relativa al archivo.",
                            },
                            "start_line": {"type": "integer"},
                            "end_line": {"type": "integer"},
                        },
                        "required": ["filepath"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "replace_file_content",
                    "description": "Reemplaza un bloque exacto de código en un archivo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string"},
                            "target_content": {
                                "type": "string",
                                "description": "Texto exacto a buscar.",
                            },
                            "replacement_content": {
                                "type": "string",
                                "description": "Nuevo texto.",
                            },
                        },
                        "required": [
                            "filepath",
                            "target_content",
                            "replacement_content",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "Lista los archivos y carpetas de un directorio.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directorio relativo a listar.",
                            }
                        },
                        "required": ["directory"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Ejecuta un comando en la consola (terminal).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando bash/powershell a ejecutar.",
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Directorio de trabajo relativo.",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "grep_search",
                    "description": "Busca coincidencias de texto exacto recursivamente en archivos del workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Texto exacto a buscar.",
                            },
                            "filepath": {
                                "type": "string",
                                "description": "Ruta relativa del archivo o carpeta donde buscar.",
                            },
                        },
                        "required": ["query", "filepath"],
                    },
                },
            },
        ]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name not in self.tools:
            return f"Error: Tool '{name}' not found."
            
        # Fase 15: Dual-Engine Sandbox Bypass Mitigation
        if name in ["run_command", "replace_file_content"]:
            from core.hitl_manager import intercept
            # Mapeamos a los nombres ya registrados en HIGH_RISK_TOOLS del hitl_manager
            hitl_name = "shell_exec" if name == "run_command" else "file_edit"
            
            # Asumimos bg_mode=False (interactivo) ya que ToolEngine es llamado por GravityBrain (sesión de chat)
            hitl_res = intercept(
                tool_name=hitl_name,
                arguments=args,
                session_id="ToolEngine",
                bg_mode=False
            )
            
            if not hitl_res.get("proceed", False):
                reason = hitl_res.get("decision", "rejected")
                log.warning(f"[ToolEngine] Ejecución de '{name}' RECHAZADA por HITL ({reason})")
                return f"Error: Ejecución rechazada por el administrador ({reason})."
                
        try:
            log.info(f"[ToolEngine] Ejecutando {name} con {args}")
            return self.tools[name](**args)
        except Exception as e:
            log.error(f"[ToolEngine] Error en {name}: {e}")
            return f"Error ejecutando {name}: {str(e)}"

    def view_file(self, filepath: str, start_line: int = 1, end_line: int = -1) -> str:
        safe_p = self._safe_path(filepath)
        if not os.path.isfile(safe_p):
            return f"Error: Archivo no encontrado {filepath}"
        with self._lock:
            try:
                lines = self._read_lines_with_fallback(safe_p)
                if end_line == -1:
                    end_line = len(lines)
                idx_start = max(0, start_line - 1)
                idx_end = min(len(lines), end_line)
                chunk = "".join(lines[idx_start:idx_end])
                return f"--- {filepath} (Líneas {start_line}-{end_line}) ---\n{chunk}"
            except Exception as e:
                return f"Error al decodificar o leer el archivo: {e}"

    def replace_file_content(
        self, filepath: str, target_content: str, replacement_content: str
    ) -> str:
        try:
            safe_p = self._safe_path(filepath, is_write=True)
        except PermissionError as e:
            return f"Error de Permisos: {str(e)}"
        if not os.path.isfile(safe_p):
            return f"Error: Archivo no encontrado {filepath}"
        with self._lock:
            try:
                content = self._read_file_with_fallback(safe_p)

                if target_content not in content:
                    return (
                        "Error: No se encontró 'target_content' exacto en el archivo."
                    )

                count = content.count(target_content)
                if count > 1:
                    return f"Error: Múltiples ({count}) ocurrencias de 'target_content' encontradas. Sé más específico."

                new_content = content.replace(target_content, replacement_content)
                with open(safe_p, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return f"Éxito: Archivo {filepath} actualizado."
            except Exception as e:
                return f"Error actualizando el archivo: {e}"

    def list_dir(self, directory: str = ".") -> str:
        safe_p = self._safe_path(directory)
        if not os.path.isdir(safe_p):
            return f"Error: Directorio no encontrado {directory}"
        items = os.listdir(safe_p)
        result = []
        for item in items:
            p = os.path.join(safe_p, item)
            size = os.path.getsize(p) if os.path.isfile(p) else "-"
            tipo = "DIR" if os.path.isdir(p) else "FILE"
            result.append(f"[{tipo}] {item} (Size: {size})")
        return "\n".join(result)

    def run_command(self, command: str, cwd: str = ".") -> str:
        safe_cwd = self._safe_path(cwd)
        try:
            # Dividir comando usando shlex para desactivar operadores de shell y prevenir Command Injection
            args = shlex.split(command, posix=(os.name != "nt"))
            result = subprocess.run(
                args,
                cwd=safe_cwd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            res = ""
            if out:
                res += f"STDOUT:\n{out}\n"
            if err:
                res += f"STDERR:\n{err}\n"
            res += f"Exit Code: {result.returncode}"
            return res
        except subprocess.TimeoutExpired:
            return "Error: Comando abortado tras 60 segundos por timeout."
        except Exception as e:
            return f"Error ejecutando comando: {str(e)}"

    def grep_search(self, query: str, filepath: str) -> str:
        safe_p = self._safe_path(filepath)
        with self._lock:
            # Búsqueda simple basada en python sin depender de grep de sistema para compatibilidad multi-OS
            results = []
            if os.path.isfile(safe_p):
                files = [safe_p]
            elif os.path.isdir(safe_p):
                # Escaneo recursivo simple (.py, .ts, .tsx, .json)
                files = []
                for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.json", "*.md"):
                    files.extend(
                        glob.glob(os.path.join(safe_p, "**", ext), recursive=True)
                    )
            else:
                return "Error: Ruta no válida."

            count = 0
            for fpath in files:
                try:
                    lines = self._read_lines_with_fallback(fpath)
                    for idx, line in enumerate(lines):
                        if query in line:
                            rel = os.path.relpath(fpath, self.workspace_root)
                            results.append(f"{rel}:{idx+1}: {line.strip()}")
                            count += 1
                            if count > 100:
                                results.append("... Demasiados resultados, se truncó.")
                                return "\n".join(results)
                except Exception:
                    pass
            return "\n".join(results) if results else "No se encontraron coincidencias."


# Instancia Global
tool_engine: Optional[ToolEngine] = None


def get_tool_engine(workspace_root: str) -> ToolEngine:
    global tool_engine
    with _singleton_lock:
        if tool_engine is None:
            tool_engine = ToolEngine(workspace_root)
        return tool_engine
