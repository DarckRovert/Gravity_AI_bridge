"""
Gravity Workflow Node: VideoConcat
Concatena múltiples clips de video en uno solo usando ffmpeg.
"""

import os
import tempfile
from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class VideoConcatNode(GravityNode):
    NODE_TYPE = "VideoConcat"
    DESCRIPTION = "Concatena una lista de clips de video en un único archivo MP4 usando ffmpeg."
    INPUT_SCHEMA = {
        "clips": "VIDEO_LIST",   # lista de rutas absolutas
        "output_path": "TEXT",   # opcional
        "fps": "INT",            # default 24
        "codec": "TEXT",         # default "libx264"
        "fade": "BOOL",          # default True — fade entre clips
    }
    OUTPUT_SCHEMA = {
        "video_path": "VIDEO",
        "success": "BOOL",
        "duration_s": "FLOAT",
    }

    def execute(self, inputs: dict) -> dict:
        from core.video.renderer import _concatenate_clips

        clips: list = inputs.get("clips") or []
        output_path: str = inputs.get("output_path") or self.config.get("output_path") or ""
        fps: int = int(inputs.get("fps") or self.config.get("fps") or 24)
        codec: str = inputs.get("codec") or self.config.get("codec") or "libx264"
        fade: bool = bool(inputs.get("fade") if "fade" in inputs else True)

        # Filtrar clips válidos
        valid_clips = [c for c in clips if c and os.path.isfile(c)]
        if not valid_clips:
            log.warning("[VideoConcatNode] No hay clips válidos para concatenar.")
            return {"video_path": "", "success": False, "duration_s": 0.0}

        if not output_path:
            output_path = os.path.join(tempfile.gettempdir(), f"gravity_concat_{id(self)}.mp4")

        log.info(f"[VideoConcatNode] Concatenando {len(valid_clips)} clips → {output_path}")

        try:
            result_path = _concatenate_clips(
                clips=valid_clips,
                output_path=output_path,
                fps=fps,
                codec=codec,
                fade=fade,
            )

            duration_s = 0.0
            if result_path and os.path.exists(result_path):
                size = os.path.getsize(result_path)
                # Heurística: ~1MB por 5s de video HD
                duration_s = round(size / (1024 * 1024) * 5, 2)

            return {
                "video_path": result_path or "",
                "success": bool(result_path),
                "duration_s": duration_s,
            }

        except Exception as exc:
            log.error(f"[VideoConcatNode] Error: {exc}")
            return {"video_path": "", "success": False, "duration_s": 0.0}
