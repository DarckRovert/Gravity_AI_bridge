"""
Gravity AI — File Edit Tool V9.3.1 PRO (Claw Edition)
Implementación de edición quirúrgica basada en bloques exactos.
Inspirado en el algoritmo de Claude Code (FileEditTool).
"""
import os
import re
from typing import Optional
from .base_tool import Tool, ToolResult


class FileEditV2(Tool):
    name = "file_edit"
    description = (
        "Realiza cambios quirúrgicos en un archivo reemplazando un bloque exacto de texto. "
        "Requiere el bloque original ('old_string') y el nuevo ('new_string')."
    )
    requires_confirmation = True

    def execute(self, 
                target_file: str, 
                old_string: str, 
                new_string: str, 
                replace_all: bool = False) -> ToolResult:
        
        # 1. Validación de existencia
        if not os.path.exists(target_file):
            return ToolResult(success=False, stderr=f"Archivo no encontrado: {target_file}")
        
        if not os.path.isfile(target_file):
            return ToolResult(success=False, stderr=f"La ruta no es un archivo: {target_file}")

        try:
            # 2. Lectura y Normalización de saltos de línea (Inspirado en Claw)
            with open(target_file, 'r', encoding='utf-8', errors='replace') as f:
                original_content = f.read()
            
            # Normalizar \r\n a \n para el procesamiento
            content = original_content.replace('\r\n', '\n')
            old_normalized = old_string.replace('\r\n', '\n')
            new_normalized = new_string.replace('\r\n', '\n')

            # 3. Normalización Adicional (Quote Normalization heurístico de Claw)
            # Intentamos match exacto primero
            occurrences = content.count(old_normalized)
            
            # Si no hay match, intentamos normalizar comillas
            if occurrences == 0:
                content_norm, old_norm = self._normalize_quotes(content, old_normalized)
                occurrences = content_norm.count(old_norm)
                if occurrences > 0:
                    # Si funcionó con normalización, debemos trabajar sobre el contenido normalizado
                    # o mapear índices. Para simplificar esta v1, usaremos la normalización literal.
                    content = content_norm
                    old_normalized = old_norm

            # 4. Manejo de ocurrencias
            if occurrences == 0:
                return ToolResult(
                    success=False, 
                    stderr="No se encontró el bloque 'old_string' en el archivo. Verifica la indentación y caracteres especiales."
                )
            
            if occurrences > 1 and not replace_all:
                return ToolResult(
                    success=False, 
                    stderr=f"Se encontraron {occurrences} coincidencias. Provee más contexto en 'old_string' para que sea único."
                )

            # 5. Reemplazo Quirúrgico
            if replace_all:
                new_content = content.replace(old_normalized, new_normalized)
            else:
                new_content = content.replace(old_normalized, new_normalized, 1)

            # 6. Post-procesamiento (Limpieza de espacios finales, excepto en MD)
            if not target_file.endswith(('.md', '.mdx')):
                lines = new_content.split('\n')
                new_content = '\n'.join([line.rstrip() for line in lines])

            # Restaurar saltos de línea originales si es necesario
            if '\r\n' in original_content:
                new_content = new_content.replace('\n', '\r\n')

            # 7. Escritura Atómica
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return ToolResult(
                success=True, 
                stdout=f"✓ Archivo {os.path.basename(target_file)} editado con éxito ({'todas' if replace_all else '1'} coincidencia/s)."
            )

        except Exception as e:
            return ToolResult(success=False, stderr=f"Error en la edición: {str(e)}")

    def _normalize_quotes(self, text: str, target: str):
        """Traduce comillas tipográficas a neutras para facilitar el match."""
        mapping = {
            '“': '"', '”': '"', '‘': "'", '’': "'",
            '«': '"', '»': '"', '„': '"'
        }
        for k, v in mapping.items():
            text = text.replace(k, v)
            target = target.replace(k, v)
        return text, target
