import os
import json
from datetime import datetime
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register
class JSONAppenderNode(GravityNode):
    NODE_TYPE = "JSONAppender"
    DESCRIPTION = "Inserta un nuevo objeto JSON al inicio de una lista JSON en disco, manteniendo un máximo de elementos."
    INPUT_SCHEMA = {
        "filepath": "TEXT",       # Ruta absoluta o relativa a BASE_DIR
        "new_item": "TEXT",       # Objeto JSON serializado como string (desde LLM)
        "max_items": "INT",       # Límite máximo de la lista
        "root_key": "TEXT"        # (Opcional) Si el JSON es un dict, la key donde está el array (ej. 'niches')
    }
    OUTPUT_SCHEMA = {
        "status": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        filepath = inputs.get("filepath", "")
        new_item_str = inputs.get("new_item", "{}")
        max_items = int(inputs.get("max_items", 50))
        root_key = inputs.get("root_key", "")

        if not filepath:
            raise ValueError(f"[{self.node_id}] Ruta del JSON no especificada.")

        import re
        # Intentar parsear el new_item para asegurar que es un dict
        try:
            new_item = json.loads(new_item_str, strict=False)
        except Exception as e:
            # Fallback: intentar extraer un JSON con regex (útil si el LLM envía bloques de código)
            json_match = re.search(r"(\{[\s\S]*\})", new_item_str)
            if json_match:
                try:
                    new_item = json.loads(json_match.group(1), strict=False)
                except Exception as e2:
                    log.error(f"[{self.__class__.__name__}] El new_item extraído por regex tampoco es válido: {e2}")
                    raise ValueError(f"new_item inválido: {e2}")
            else:
                log.error(f"[{self.__class__.__name__}] El new_item no es un JSON válido y no se encontró patrón: {e}")
                raise ValueError(f"new_item inválido: {e}")

        # Añadir timestamp automáticamente si no existe o si es necesario unificarlos (Gravity hace esto en reporter)
        if "date" not in new_item:
            new_item["date"] = datetime.now().isoformat()
        if "id" not in new_item:
            new_item["id"] = int(datetime.now().timestamp() * 1000)

        # Leer array actual
        file_data = None
        items = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
            except Exception as e:
                log.warning(f"[{self.__class__.__name__}] Archivo JSON corrupto o vacío en {filepath}, creando base nueva.")
                file_data = None

        if root_key:
            if not isinstance(file_data, dict):
                file_data = {root_key: []}
            items = file_data.get(root_key, [])
            if not isinstance(items, list):
                items = []
        else:
            if not isinstance(file_data, list):
                file_data = []
            items = file_data

        # Eliminar duplicados (si existe un item con el mismo ID, se sobrescribe)
        if "id" in new_item:
            items = [art for art in items if art.get("id") != new_item["id"]]

        # Insertar al inicio y recortar
        items.insert(0, new_item)
        
        # Opcional: ordenar por date inverso
        try:
            items = sorted(items, key=lambda x: x.get("date", ""), reverse=True)
        except Exception:
            pass

        items = items[:max_items]

        if root_key:
            file_data[root_key] = items
        else:
            file_data = items

        # Guardar atómicamente
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            tmp_path = filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, filepath)
            log.info(f"[{self.__class__.__name__}] Objeto inyectado en {filepath}. Total items: {len(items)}")
            return {"status": "success"}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error escribiendo JSON: {e}")
            raise
