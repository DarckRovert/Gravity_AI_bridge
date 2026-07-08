"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — BookSerializer Node                                           ║
║                                                                              ║
║   Nodo que toma un libro generado (directorio con cap_1.md, cap_2.md, etc.)  ║
║   y serializa sus capítulos, publicándolos progresivamente en Nexo Ágora o   ║
║   encolándolos para generación de videos en TikTok.                          ║
║                                                                              ║
║   NODE_TYPE: "BookSerializer"                                                ║
║                                                                              ║
║   Inputs:                                                                    ║
║     book_dir       (TEXT)  — Directorio del libro (debe contener cap_N.md)   ║
║     publish_target (TEXT)  — Destino de publicación (ej. "nexo_agora")       ║
║     schedule       (TEXT)  — Frecuencia de publicación (ej. "daily")         ║
║                                                                              ║
║   Outputs:                                                                   ║
║     status           (TEXT)  — Estado de la serialización                    ║
║     queued_chapters  (INT)   — Número de capítulos encolados/procesados      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import sys
import glob
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.workflow_engine import GravityNode, registry  # noqa: E402
from core.logger import log  # noqa: E402

@registry.register
class BookSerializerNode(GravityNode):
    """
    Nodo de serialización de libros. 
    Ideal para publicación por entregas (estilo novela web o folletín).
    """

    NODE_TYPE = "BookSerializer"
    DESCRIPTION = "Serializa y encola capítulos individuales de un libro para publicación externa (Nexo Ágora/TikTok)."

    INPUT_SCHEMA = {
        "book_dir": "TEXT",
        "publish_target": "TEXT",
        "schedule": "TEXT",
    }
    OUTPUT_SCHEMA = {
        "status": "TEXT",
        "queued_chapters": "INT",
    }

    async def _execute(self, context: dict, input_data: dict) -> dict:
        book_dir = input_data.get("book_dir", "")
        publish_target = input_data.get("publish_target", "nexo_agora")
        schedule = input_data.get("schedule", "daily")

        if not book_dir or not os.path.exists(book_dir):
            log.error(f"[BookSerializerNode] El directorio del libro no existe: {book_dir}")
            return {"status": "FAILED: Directorio inválido", "queued_chapters": 0}

        # Extraer título del libro
        book_title = os.path.basename(os.path.normpath(book_dir)).replace("_", " ")

        # Detectar capítulos generados (cap_1.md, cap_2.md...)
        cap_files = glob.glob(os.path.join(book_dir, "cap_*.md"))
        cap_files = sorted(
            cap_files,
            key=lambda x: int(re.search(r"cap_(\d+)", os.path.basename(x)).group(1))
            if re.search(r"cap_(\d+)", os.path.basename(x)) else 0
        )

        if not cap_files:
            log.warning(f"[BookSerializerNode] No se encontraron capítulos en {book_dir}")
            return {"status": "FAILED: Sin capítulos", "queued_chapters": 0}

        log.info(f"[BookSerializerNode] Iniciando serialización de '{book_title}' para {publish_target} ({schedule}).")
        
        # En una implementación real, aquí nos conectaríamos a la API de Nexo Ágora
        # o escribiríamos a una cola (RabbitMQ/SQLite) con la programación deseada.
        # Por ahora, simulamos el encolado guardando un manifesto de serialización.

        serialization_manifest = {
            "book_title": book_title,
            "target": publish_target,
            "schedule": schedule,
            "queue": []
        }

        for i, cap_path in enumerate(cap_files):
            cap_num = i + 1
            serialization_manifest["queue"].append({
                "chapter": cap_num,
                "file": cap_path,
                "status": "queued",
                "scheduled_day": f"Day {cap_num}" if schedule == "daily" else f"Week {cap_num}"
            })

        manifest_path = os.path.join(book_dir, f"serialization_{publish_target}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(serialization_manifest, f, indent=4, ensure_ascii=False)

        log.info(f"[BookSerializerNode] {len(cap_files)} capítulos encolados con éxito. Manifiesto: {manifest_path}")

        return {
            "status": "SUCCESS",
            "queued_chapters": len(cap_files)
        }
