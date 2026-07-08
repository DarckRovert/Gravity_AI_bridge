"""
TopicPickerNode — Selecciona un topic de una lista JSON embebida en el workflow.
V2.0: Añade deduplicación via editorial_memory y sistema de pesos por uso.
Devuelve: topic, angle, refs (para essayist) o topic/query (para scientist).
"""
import json
import random
from typing import Dict, Any, List, Optional

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class TopicPickerNode(GravityNode):
    NODE_TYPE = "TopicPicker"
    DESCRIPTION = (
        "Selecciona un topic de una lista embebida en el workflow. "
        "V2.0: evita repetir topics recientes (deduplicación) y "
        "prioriza los menos usados mediante sistema de pesos."
    )
    INPUT_SCHEMA = {
        "topics_json": "TEXT",    # JSON array de objetos {topic, angle?, refs?, query?, weight?}
        "override_topic": "TEXT", # Si no está vacío, usa este topic directamente
        "workflow": "TEXT",       # Nombre del workflow para scoping de deduplicación
        "dedup_window_days": "INT", # Ventana de deduplicación en días (default: 14)
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
            self._record(override, inputs)
            return {"topic": override, "angle": "", "refs": "", "query": override}

        topics_json_str = inputs.get("topics_json", "[]")
        try:
            topics = json.loads(topics_json_str)
            if not isinstance(topics, list) or not topics:
                raise ValueError("Lista vacía o inválida")
        except Exception as e:
            raise ValueError(f"[TopicPickerNode] topics_json inválido: {e}")

        workflow = inputs.get("workflow", "").strip()
        dedup_days = int(inputs.get("dedup_window_days") or 14)

        # Cargar función de deduplicación
        _seen_fn = None
        try:
            from core.editorial_memory import seen_topic as _seen_fn
        except Exception:
            pass

        # Normalizar topics a dicts
        normalized: List[Dict] = []
        for t in topics:
            if isinstance(t, str):
                normalized.append({"topic": t, "weight": 1})
            elif isinstance(t, dict):
                normalized.append(t)

        # Filtrar topics ya usados recientemente
        available = []
        excluded = []
        for t in normalized:
            topic_text = t.get("topic", t.get("query", ""))
            if _seen_fn and _seen_fn(topic_text, workflow=workflow, window_days=dedup_days):
                excluded.append(topic_text)
            else:
                available.append(t)

        if excluded:
            log.info(
                f"[{self.__class__.__name__}] {len(excluded)} topics excluidos por deduplicación "
                f"(ventana {dedup_days}d). {len(available)} disponibles."
            )

        # Si todos están excluidos, usar todos (mejor repetir que bloquearse)
        if not available:
            log.warning(
                f"[{self.__class__.__name__}] Todos los topics fueron usados recientemente. "
                "Usando lista completa para evitar bloqueo."
            )
            available = normalized

        # Selección ponderada por campo "weight" (default=1)
        chosen = self._weighted_choice(available)

        topic = chosen.get("topic", chosen.get("query", ""))
        angle = chosen.get("angle", "")
        refs = chosen.get("refs", "")
        query = chosen.get("query", topic)

        log.info(f"[{self.__class__.__name__}] Topic seleccionado: {topic[:80]}")

        # Registrar en memoria editorial para deduplicación futura
        self._record(topic, inputs)

        return {
            "topic": topic,
            "angle": angle,
            "refs": refs,
            "query": query,
        }

    def _weighted_choice(self, topics: List[Dict]) -> Dict:
        """Selección aleatoria ponderada por el campo 'weight'."""
        weights = [max(float(t.get("weight", 1)), 0.1) for t in topics]
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0.0
        for t, w in zip(topics, weights):
            cumulative += w
            if r <= cumulative:
                return t
        return topics[-1]

    def _record(self, topic: str, inputs: Dict[str, Any]) -> None:
        """Registra el topic en la memoria editorial."""
        if not topic:
            return
        workflow = inputs.get("workflow", "").strip()
        try:
            from core.editorial_memory import record_topic
            record_topic(topic, workflow=workflow)
        except Exception:
            pass
