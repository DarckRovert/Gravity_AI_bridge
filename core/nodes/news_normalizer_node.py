"""
[DEPRECATED] NewsNormalizerNode — Obsoleto desde V16.3 PRO.
Redirige automáticamente a ContentNormalizerNode con content_type='news'.
Mantenido en el registro para compatibilidad con workflows externos que aún lo referencien.
"""
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


@registry.register
class NewsNormalizerNode(GravityNode):
    NODE_TYPE = "NewsNormalizer"
    DEPRECATED = True
    DESCRIPTION = (
        "[DEPRECATED] Usa ContentNormalizer con content_type='news'. "
        "Redirige automáticamente a ContentNormalizerNode para compatibilidad."
    )
    INPUT_SCHEMA = {
        "raw_json": "TEXT"
    }
    OUTPUT_SCHEMA = {
        "normalized_json": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        log.warning(
            "[NewsNormalizerNode] DEPRECATED: este nodo está obsoleto desde V16.3 PRO. "
            "Usa ContentNormalizer con content_type='news'. "
            "Redirigiendo automáticamente..."
        )
        # Redirección automática a ContentNormalizerNode
        from core.nodes.content_normalizer_node import ContentNormalizerNode
        delegate = ContentNormalizerNode(self.node_id, self.config)
        return delegate.execute({
            **inputs,
            "content_type": "news",
            "author": "Nexo Ágora — Redacción Periodística",
            "image_prompt_prefix": "cyberpunk news dark photorealistic",
            "valid_categories": json.dumps([
                "Control Biométrico", "Resistencia Digital", "Soberanía Criptográfica",
                "Vigilancia del Leviatán", "Tecnología Descentralizada", "Geopolítica y Macro-Leviatán",
                "Medicina y Bioética", "Cultura y Psicometría", "Cine e Ingeniería Social",
                "Deporte y Control Biométrico", "Ciencia y Sustrato", "Religión y Creencias Masivas",
                "Crimen de Estado y Abuso Policial"
            ]),
            "default_category": "Tecnología Descentralizada",
        })
