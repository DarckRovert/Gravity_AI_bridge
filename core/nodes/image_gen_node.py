"""
Gravity Workflow Node: ImageGenerator
Genera una imagen a partir de un prompt usando image_router (Pollinations → SVG fallback).
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class ImageGeneratorNode(GravityNode):
    NODE_TYPE = "ImageGenerator"
    DESCRIPTION = "Genera una imagen desde un prompt usando el image_router de Gravity."
    INPUT_SCHEMA = {
        "prompt": "TEXT",
        "output_path": "TEXT",
        "width": "INT",   # opcional, default 1216
        "height": "INT",  # opcional, default 832
        "title": "TEXT",  # opcional — para el SVG placeholder
    }
    OUTPUT_SCHEMA = {
        "image_path": "IMAGE",
        "provider": "TEXT",
        "success": "BOOL",
    }

    def execute(self, inputs: dict) -> dict:
        from core.image_router import generate

        prompt: str = inputs.get("prompt", "")
        output_path: str = inputs.get("output_path", "")
        width: int = int(inputs.get("width") or self.config.get("width") or 1216)
        height: int = int(inputs.get("height") or self.config.get("height") or 832)
        title: str = inputs.get("title") or self.config.get("title") or ""

        if not output_path:
            import os
            import tempfile
            output_path = os.path.join(tempfile.gettempdir(), f"gravity_img_{id(self)}.png")

        log.info(f"[ImageGeneratorNode] Generando imagen: {prompt[:60]}...")
        result = generate(
            prompt=prompt,
            output_path=output_path,
            width=width,
            height=height,
            title=title,
        )

        return {
            "image_path": result.get("path", ""),
            "provider": result.get("provider", ""),
            "success": result.get("success", False),
        }
