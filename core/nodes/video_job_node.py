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
        "status": "TEXT",
        "job_id": "INT"
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
            return {"status": "skipped", "job_id": 0}

        try:
            # Import dinámico para no romper el motor si el módulo de video no está instalado
            from core.video.pipeline import add_job, start_detached_worker as start_video_pipeline

            # Asegurar que el worker procesador independiente esté activo en segundo plano
            start_video_pipeline()

            topic_text = f"Resumen de Noticia: {title}. {excerpt}"
            video_title = f"TikTok: {title}"[:60]

            job_id = add_job(
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
            log.info(f"[{self.__class__.__name__}] Video Vertical (TikTok) encolado con ID {job_id}: {video_title}")
            return {"status": "queued", "job_id": job_id}
            
        except ImportError:
            log.warning(f"[{self.__class__.__name__}] Módulo 'core.video.pipeline' no encontrado. Video ignorado.")
            return {"status": "error", "job_id": 0}
        except Exception as e:
            log.error(f"[{self.__class__.__name__}] Falló al encolar video: {e}")
            return {"status": "error", "job_id": 0}
