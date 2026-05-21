import numpy as np
import cv2
import logging
from PIL import Image

logger = logging.getLogger(__name__)

BG_SIZE = 512   # Tamanio de generacion de fondo


class BackgroundGenerator:
    """
    Genera fondos de escena usando SD-Turbo img2img con strength=1.0,
    lo que produce resultados equivalentes a txt2img.
    Reutiliza el MISMO pipe que el face transformer para no duplicar VRAM.
    """

    def __init__(self, pipe):
        """
        pipe: ORTStableDiffusionImg2ImgPipeline ya cargado y compartido.
        """
        self.pipe = pipe

    def generate(self, bg_prompt: str, bg_negative: str, seed: int = 42) -> np.ndarray:
        """
        Genera imagen de fondo BG_SIZE x BG_SIZE.
        Usa ruido aleatorio seeded como imagen de inicio + strength=1.0
        para comportamiento txt2img con el mismo pipe img2img.

        Retorna np.ndarray BGR (BG_SIZE, BG_SIZE, 3).
        """
        logger.info(f"Generando fondo: {bg_prompt[:70]}...")

        rng = np.random.default_rng(seed)
        # Imagen de ruido aleatorio seeded -> sd-turbo la ignora a strength=1.0
        noise = rng.integers(0, 256, (BG_SIZE, BG_SIZE, 3), dtype=np.uint8)
        init_image = Image.fromarray(noise)

        try:
            result = self.pipe(
                prompt=bg_prompt,
                negative_prompt=bg_negative,
                image=init_image,
                num_inference_steps=4,   # 4 pasos para mejor calidad en escenas
                strength=1.0,            # Destruye completamente la imagen init -> txt2img
                guidance_scale=4.0,      # Mayor guidance para seguir el prompt de escena
            ).images[0]

            bg_bgr = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
            logger.info("Fondo generado exitosamente.")
            return bg_bgr

        except Exception as e:
            logger.error(f"Error generando fondo: {e}. Usando fallback negro.")
            return np.zeros((BG_SIZE, BG_SIZE, 3), dtype=np.uint8)
