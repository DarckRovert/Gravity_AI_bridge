import os
import json
from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register
class FileWriterNode(GravityNode):
    """
    Escribe contenido de texto (o JSON) a un archivo local de forma segura.
    Ideal para generar exportaciones, kits de redes sociales o logs personalizados.
    """

    NODE_TYPE = "FileWriter"
    DESCRIPTION = "Guarda contenido de texto a un archivo especificado."
    INPUT_SCHEMA = {
        "filepath": "str (Ruta del archivo a escribir)",
        "content": "str (Contenido a escribir)",
        "append": "bool (opcional, por defecto False)",
    }
    OUTPUT_SCHEMA = {
        "status": "str",
        "saved_path": "str"
    }

    def execute(self, inputs: dict) -> dict:
        self.validate_inputs(inputs)
        
        filepath = inputs["filepath"]
        content = inputs["content"]
        append = inputs.get("append", False)

        # Si el contenido es dict/list, intentar convertirlo a string
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content = str(content)

        # Asegurar que el directorio exista usando safe_path_resolve con Core Protection
        filepath = self.safe_path_resolve(filepath, is_write=True)
        abs_dir = os.path.dirname(filepath)
        if abs_dir:
            os.makedirs(abs_dir, exist_ok=True)
        
        mode = "a" if append else "w"
        
        try:
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(content)
            
            log.info(f"[FileWriterNode] Archivo guardado correctamente: {filepath} ({len(content)} caracteres)")
            return {
                "status": "success",
                "saved_path": filepath
            }
        except Exception as e:
            log.error(f"[FileWriterNode] Error escribiendo archivo {filepath}: {e}")
            raise RuntimeError(f"Fallo al escribir el archivo {filepath}: {e}")
