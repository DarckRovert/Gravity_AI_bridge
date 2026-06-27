import os
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log

@registry.register
class VideoJobNode(GravityNode):
    NODE_TYPE = "VideoJob"
    DESCRIPTION = "Encola automáticamente la generación de un video vertical (TikTok/Shorts) en la base de datos."
    INPUT_SCHEMA = {
        "title": "TEXT",
        "excerpt": "TEXT"
    }
    OUTPUT_SCHEMA = {
        "status": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        title = inputs.get("title", "")
        excerpt = inputs.get("excerpt", "")

        # Si el input es un objeto JSON en string (desde normalizar_noticia)
        import json
        if title.startswith("{") and title.endswith("}"):
            try:
                data = json.loads(title)
                title = data.get("title", "")
                excerpt = data.get("excerpt", "")
            except Exception:
                pass

        if not title:
            log.warning(f"[{self.__class__.__name__}] Título vacío, saltando encolado de video.")
            return {"status": "skipped"}

        try:
            # Import dinámico para no romper el motor si el módulo de video no está instalado
            from core.video.pipeline import add_job

            topic_text = f"Resumen de Noticia: {title}. {excerpt}"
            video_title = f"TikTok: {title}"[:60]

            add_job(
                topic=topic_text,
                title=video_title,
                n_scenes=5,
                style="cyberpunk",
                resolution="832x1216",
                duration_mode="auto",
                fps=30,
                animation_effect="pulse",
                animation_level=1,
                ken_burns=True,
                intro_card=False,
                transitions=True,
                job_type="tts",
            )
            log.info(f"[{self.__class__.__name__}] Video Vertical (TikTok) encolado: {video_title}")
            return {"status": "queued"}
            
        except ImportError:
            log.warning(f"[{self.__class__.__name__}] Módulo 'core.video.pipeline' no encontrado. Video ignorado.")
            return {"status": "import_error"}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Error al encolar video: {e}")
            raise
