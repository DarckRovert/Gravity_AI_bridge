"""
Gravity AI — Grep Tool V8.5 (Claw Edition)
Implementación avanzada de búsqueda de patrones inspirada en Claude Code.
"""
import os
import re
import subprocess
from typing import List, Optional
from .base_tool import Tool, ToolResult


class GrepTool(Tool):
    name = "grep_search"
    description = (
        "Busca patrones de texto en el sistema de archivos. "
        "Soporta Regex, globs y límites de salida para optimización de tokens."
    )
    requires_confirmation = False

    def execute(self, 
                pattern: str, 
                path: str = ".", 
                glob: Optional[str] = None, 
                case_insensitive: bool = True,
                multiline: bool = False,
                head_limit: int = 250) -> ToolResult:
        
        # 1. Intentar usar Ripgrep (rg) si está disponible
        try:
            cmd = ["rg", "--json"]
            if case_insensitive:
                cmd.append("-i")
            if multiline:
                cmd.append("-U")
            if glob:
                cmd.extend(["-g", glob])
            
            cmd.extend([pattern, path])
            
            # Ejecución de Ripgrep
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 or process.returncode == 1: # 1 es "no matches"
                return self._parse_rg_json(stdout, head_limit)
                
        except FileNotFoundError:
            # 2. Fallback a implementación nativa de Python si rg no existe
            return self._python_fallback_search(pattern, path, glob, case_insensitive, head_limit)
        
        except Exception as e:
            return ToolResult(success=False, stderr=f"Error inesperado en grep_tool: {str(e)}")

    def _parse_rg_json(self, json_output: str, limit: int) -> ToolResult:
        import json
        matches = []
        count = 0
        
        for line in json_output.splitlines():
            if not line: continue
            data = json.loads(line)
            if data["type"] == "match":
                count += 1
                if count > limit:
                    break
                
                path = data["data"]["path"]["text"]
                line_number = data["data"]["line_number"]
                content = data["data"]["lines"]["text"].strip()
                matches.append(f"{path}:{line_number}: {content}")
        
        output = "\n".join(matches)
        if count > limit:
            output += f"\n\n[AVISO] Se alcanzó el límite de {limit} resultados. Refina la búsqueda."
            
        return ToolResult(
            success=True, 
            stdout=output if matches else "No se encontraron coincidencias.",
            data={"match_count": count}
        )

    def _python_fallback_search(self, pattern: str, path: str, glob_pat: Optional[str], case_insensitive: bool, limit: int) -> ToolResult:
        import fnmatch
        matches = []
        count = 0
        regex_flags = re.IGNORECASE if case_insensitive else 0
        
        try:
            regex = re.compile(pattern, regex_flags)
        except re.error as e:
            return ToolResult(success=False, stderr=f"Regex inválido: {str(e)}")

        for root, dirs, files in os.walk(path):
            # Excluir carpetas ocultas/comunes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'vendor')]
            
            for file in files:
                if glob_pat and not fnmatch.fnmatch(file, glob_pat):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                count += 1
                                if count <= limit:
                                    matches.append(f"{file_path}:{i}: {line.strip()}")
                                if count > limit:
                                    break
                except Exception:
                    continue
                
                if count > limit:
                    break
            if count > limit:
                break

        output = "\n".join(matches)
        if count > limit:
            output += f"\n\n[AVISO] Se alcanzó el límite de {limit} resultados (Modo Fallback Python)."
            
        return ToolResult(
            success=True, 
            stdout=output if matches else "No se encontraron coincidencias (Modo Fallback).",
            data={"match_count": count, "mode": "python_fallback"}
        )
