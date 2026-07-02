"""
Gravity Workflow Node: ComfyUIGen
Genera imágenes o video usando el cliente ComfyUI del proyecto.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class ComfyUIGenNode(GravityNode):
    NODE_TYPE = "ComfyUIGen"
    DESCRIPTION = "Genera imágenes o video usando ComfyUI (L2 AMD DirectML)."
    INPUT_SCHEMA = {
        "prompt": "TEXT",
        "output_path": "TEXT",      # opcional
        "workflow_json": "JSON",    # opcional — workflow personalizado
        "width": "INT",             # default 512
        "height": "INT",            # default 512
        "steps": "INT",             # default 20
        "seed": "INT",              # opcional
    }
    OUTPUT_SCHEMA = {
        "output_path": "IMAGE",
        "success": "BOOL",
        "message": "TEXT",
    }

    def execute(self, inputs: dict) -> dict:
        import os

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        comfy_client_path = os.path.join(BASE_DIR, "_integrations", "comfy_client.py")

        if not os.path.exists(comfy_client_path):
            log.warning("[ComfyUIGenNode] comfy_client.py no encontrado en _integrations/")
            return {"output_path": "", "success": False, "message": "ComfyUI client no encontrado."}

        try:
            # Importar dinámicamente
            import importlib.util
            spec = importlib.util.spec_from_file_location("comfy_client", comfy_client_path)
            comfy_client = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(comfy_client)

            prompt: str = inputs.get("prompt", "")
            output_path: str = inputs.get("output_path") or self.config.get("output_path") or ""
            width: int = int(inputs.get("width") or self.config.get("width") or 512)
            height: int = int(inputs.get("height") or self.config.get("height") or 512)
            steps: int = int(inputs.get("steps") or self.config.get("steps") or 20)
            seed: int = int(inputs.get("seed") or self.config.get("seed") or -1)

            log.info(f"[ComfyUIGenNode] Generando con ComfyUI: {prompt[:60]}")

            result = comfy_client.generate(
                prompt=prompt,
                output_path=output_path,
                width=width,
                height=height,
                steps=steps,
                seed=seed,
            )

            return {
                "output_path": result.get("output_path", ""),
                "success": result.get("success", False),
                "message": result.get("message", ""),
            }

        except Exception as exc:
            log.error(f"[ComfyUIGenNode] Error: {exc}")
            return {"output_path": "", "success": False, "message": str(exc)}
