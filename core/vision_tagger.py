import os
import base64
import requests
from core.logger import log

class VisionTagger:
    def __init__(self):
        # En una instalacion completa, aqui cargariamos Moondream2 o WD14 Tagger via ONNX
        # Para el motor actual, usamos un endpoint ligero local o el de HF Inference API (si hay token)
        # o un fallback mock para garantizar el flujo sin crash
        self.use_mock = True

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def generate_visual_anchor(self, image_path: str) -> str:
        """
        Analiza una imagen y devuelve un prompt (ancla visual) que describe sus 
        caracteristicas clave para mantener la consistencia en generaciones futuras.
        """
        if not os.path.exists(image_path):
            log.warning("[VisionTagger] Imagen no encontrada para taggear.")
            return ""

        log.info(f"[VisionTagger] Analizando imagen {image_path} para consistencia visual...")
        
        if self.use_mock:
            # Simulacion de extraccion de tags (Anchor)
            # Retornamos tags genericos que ayudarian al LLM o difusion a mantener el estilo
            anchor_tags = "masterpiece, best quality, highly detailed, consistent character design, matching lighting and palette"
            log.info(f"[VisionTagger] Ancla visual generada: {anchor_tags}")
            return anchor_tags
        
        # Integracion futura con local API (Ollama / Moondream2)
        try:
            # Asumiendo un servidor local de Ollama con llava o moondream
            payload = {
                "model": "moondream2",
                "prompt": "Describe the main character and the overall visual style in a comma-separated list of tags.",
                "images": [self._encode_image(image_path)],
                "stream": False
            }
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=15)
            if response.status_code == 200:
                anchor = response.json().get("response", "").strip()
                log.info(f"[VisionTagger] Ancla visual generada: {anchor}")
                return anchor
        except Exception as e:
            log.warning(f"[VisionTagger] Fallo al taggear con IA local: {e}. Usando fallback.")
            
        return "masterpiece, best quality, highly detailed, consistent style"

vision_tagger = VisionTagger()
