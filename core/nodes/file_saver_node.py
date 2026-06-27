import os
from datetime import datetime
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@registry.register

class FileSaverNode(GravityNode):
    """
    Guarda contenido de texto a un archivo en disco.
    Inputs requeridos:
      - text: El contenido a guardar.
    Inputs opcionales:
      - directory: Directorio relativo a la raiz de Gravity (default: "_ensayos_generados")
      - filename: Nombre del archivo (default: auto-generado por timestamp)
      - prefix: Prefijo para el archivo auto-generado (default: "doc_")
      - extension: Extensión del archivo (default: ".md")
    """
    
    NODE_TYPE = "FileSaver"
    DESCRIPTION = "Guarda contenido de texto a un archivo en disco."
    INPUT_SCHEMA = {
        "text": "TEXT",
        "directory": "TEXT",
        "filename": "TEXT",
        "prefix": "TEXT",
        "extension": "TEXT"
    }
    OUTPUT_SCHEMA = {
        "filepath": "TEXT",
        "filename": "TEXT",
        "status": "TEXT"
    }
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        if not text:
            raise ValueError(f"[{self.node_id}] No se recibio 'text' para guardar.")

        directory = inputs.get("directory", "_ensayos_generados")
        filename = inputs.get("filename")
        prefix = inputs.get("prefix", "doc_")
        extension = inputs.get("extension", ".md")

        if not extension.startswith("."):
            extension = f".{extension}"

        # Resolve directory
        target_dir = os.path.join(BASE_DIR, directory)
        os.makedirs(target_dir, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}{timestamp}{extension}"

        filepath = os.path.join(target_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            log.info(f"[{self.__class__.__name__}] Archivo guardado en: {filepath}")
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error guardando archivo {filepath}: {e}")
            raise

        return {"filepath": filepath, "filename": filename, "status": "saved"}
