"""
Gravity Workflow Node: CinematicVideo
Encola un trabajo de producción de video cinematográfico completo en el pipeline de Gravity.
Expone todos los parámetros de add_job() como inputs del workflow.

Este nodo es el sustituto correcto de un hipotético ForeachNode para video_cinema.json:
en lugar de iterar escenas manualmente (que requeriría soporte de grafos cíclicos),
delega el pipeline completo (guión → imágenes por escena → TTS → render → concat → subir)
al Video Studio de Gravity que ya tiene toda esa lógica probada.
"""
from typing import Dict, Any

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class CinematicVideoNode(GravityNode):
    NODE_TYPE = "CinematicVideo"
    DESCRIPTION = (
        "Encola un video cinematográfico completo en el Video Studio de Gravity. "
        "Pipeline: guión → imágenes por escena → TTS → render GLSL → concat → upload."
    )
    INPUT_SCHEMA = {
        # Requeridos
        "topic": "TEXT",
        # Opcionales con defaults
        "title": "TEXT",          # default: primeras 60 chars del topic
        "style": "TEXT",          # default: "documental"
        "n_scenes": "INT",        # default: 6
        "lang": "TEXT",           # default: "es"
        "resolution": "TEXT",     # default: "1216x832" (horizontal) o "832x1216" (vertical)
        "fps": "INT",             # default: 24
        "job_type": "TEXT",       # "tts" | "music" | "voice_over"
        "bgm_type": "TEXT",       # "ninguna" | "ambiental" | "epica"
        "bgm_volume": "FLOAT",    # default: 0.1
        "use_lore": "BOOL",       # default: True
        "transitions": "BOOL",    # default: True
        "ken_burns": "BOOL",      # default: True
        "subtitles": "BOOL",      # default: True
        "intro_card": "BOOL",     # default: False
        "color_grade": "TEXT",    # "auto" | "tension" | "euforia" | etc.
        "animation_effect": "TEXT",  # "auto" | "pulse" | "wave" | etc.
        "animation_level": "INT", # 0-3, default: 1
        "niche_id": "TEXT",       # para content_scheduler tracking
        "quality": "TEXT",        # "hd" | "4k"
    }
    OUTPUT_SCHEMA = {
        "job_id": "INT",          # ID en la base de datos _video_queue.sqlite
        "status": "TEXT",         # "queued" | "error"
        "topic_preview": "TEXT",  # primeros 80 chars del topic
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        topic: str = inputs.get("topic", "")
        if not topic:
            raise ValueError(f"[{self.node_id}] 'topic' es obligatorio para CinematicVideo.")

        title: str = inputs.get("title") or self.config.get("title") or topic[:60]
        style: str = inputs.get("style") or self.config.get("style") or "documental"
        n_scenes: int = int(inputs.get("n_scenes") or self.config.get("n_scenes") or 6)
        lang: str = inputs.get("lang") or self.config.get("lang") or "es"
        resolution: str = inputs.get("resolution") or self.config.get("resolution") or "1216x832"
        fps: int = int(inputs.get("fps") or self.config.get("fps") or 24)
        job_type: str = inputs.get("job_type") or self.config.get("job_type") or "tts"
        bgm_type: str = inputs.get("bgm_type") or self.config.get("bgm_type") or "ninguna"
        bgm_volume: float = float(inputs.get("bgm_volume") or self.config.get("bgm_volume") or 0.1)
        use_lore: bool = bool(inputs.get("use_lore", True))
        transitions: bool = bool(inputs.get("transitions", True))
        ken_burns: bool = bool(inputs.get("ken_burns", True))
        subtitles: bool = bool(inputs.get("subtitles", True))
        intro_card: bool = bool(inputs.get("intro_card", False))
        color_grade: str = inputs.get("color_grade") or self.config.get("color_grade") or "auto"
        animation_effect: str = inputs.get("animation_effect") or self.config.get("animation_effect") or "auto"
        animation_level: int = int(inputs.get("animation_level") or self.config.get("animation_level") or 1)
        niche_id: str = inputs.get("niche_id") or self.config.get("niche_id") or ""
        quality: str = inputs.get("quality") or self.config.get("quality") or "hd"

        log.info(
            f"[CinematicVideoNode] Encolando video: '{title[:60]}' | "
            f"style={style} | n_scenes={n_scenes} | lang={lang} | job_type={job_type}"
        )

        try:
            from core.video.pipeline import add_job

            job_id = add_job(
                topic=topic,
                title=title,
                n_scenes=n_scenes,
                style=style,
                narration_lang=lang,
                resolution=resolution,
                fps=fps,
                job_type=job_type,
                bgm_type=bgm_type,
                bgm_volume=bgm_volume,
                use_lore=use_lore,
                transitions=transitions,
                ken_burns=ken_burns,
                subtitles=subtitles,
                intro_card=intro_card,
                color_grade=color_grade,
                animation_effect=animation_effect,
                animation_level=animation_level,
                niche_id=niche_id,
                quality=quality,
            )

            log.info(f"[CinematicVideoNode] Video encolado exitosamente. Job ID: {job_id}")
            return {
                "job_id": job_id,
                "status": "queued",
                "topic_preview": topic[:80],
            }

        except ImportError:
            log.warning("[CinematicVideoNode] Módulo 'core.video.pipeline' no disponible. Video ignorado.")
            return {"job_id": -1, "status": "import_error", "topic_preview": topic[:80]}

        except Exception as exc:
            log.error(f"[CinematicVideoNode] Error al encolar video: {exc}")
            raise
