"""
TopicPickerNode — Selecciona aleatoriamente un topic de una lista JSON embebida en el workflow.
Devuelve: topic, angle, refs (para essayist) o solo topic (para scientist/reporter).
"""
import json
import random
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class TopicPickerNode(GravityNode):
    NODE_TYPE = "TopicPicker"
    DESCRIPTION = (
        "Selecciona aleatoriamente un elemento de una lista de tópicos embebida en el workflow. "
        "Devuelve los campos del tópico elegido (topic, angle, refs, query, etc.)."
    )
    INPUT_SCHEMA = {
        "topics_json": "TEXT",   # JSON array de objetos {topic, angle?, refs?, query?}
        "override_topic": "TEXT" # Si no está vacío, usa este topic directamente
    }
    OUTPUT_SCHEMA = {
        "topic": "TEXT",
        "angle": "TEXT",
        "refs": "TEXT",
        "query": "TEXT",
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        override = inputs.get("override_topic", "").strip()
        # Si el valor es un placeholder sin resolver (ej: "{{topic}}"), ignorarlo
        if override and not (override.startswith("{{") and override.endswith("}}")):
            log.info(f"[{self.__class__.__name__}] Topic override: {override[:80]}")
            return {"topic": override, "angle": "", "refs": "", "query": override}

        topics_json_str = inputs.get("topics_json", "[]")
        try:
            topics = json.loads(topics_json_str)
            if not isinstance(topics, list) or not topics:
                raise ValueError("Lista vacía o inválida")
        except Exception as e:
            raise ValueError(f"[TopicPickerNode] topics_json inválido: {e}")

        chosen = random.choice(topics)
        if isinstance(chosen, str):
            # Lista simple de strings
            chosen = {"topic": chosen}

        topic = chosen.get("topic", chosen.get("query", ""))
        angle = chosen.get("angle", "")
        refs = chosen.get("refs", "")
        query = chosen.get("query", topic)

        log.info(f"[{self.__class__.__name__}] Topic seleccionado: {topic[:80]}")
        return {
            "topic": topic,
            "angle": angle,
            "refs": refs,
            "query": query,
        }
