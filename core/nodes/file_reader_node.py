import os
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@registry.register
class FileReaderNode(GravityNode):
    NODE_TYPE = "FileReader"
    DESCRIPTION = "Lee el contenido de un archivo local en texto plano."
    INPUT_SCHEMA = {
        "filepath": "TEXT"      # Ruta relativa a BASE_DIR
    }
    OUTPUT_SCHEMA = {
        "content": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        filepath = inputs.get("filepath", "")
        if not filepath:
            raise ValueError(f"[{self.node_id}] No se especificó el filepath.")

        full_path = self.safe_path_resolve(filepath)
        if not os.path.exists(full_path):
            log.warning(f"[{self.__class__.__name__}] El archivo {full_path} no existe. Devolviendo vacío.")
            return {"content": ""}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                text = f.read()
            log.info(f"[{self.__class__.__name__}] Archivo leído: {filepath} ({len(text)} chars)")
            return {"content": text}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error leyendo {filepath}: {e}")
            raise
