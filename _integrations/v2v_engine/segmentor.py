import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import logging

logger = logging.getLogger(__name__)


class PersonSegmentor:
    """
    Wrapper sobre MediaPipe Tasks ImageSegmenter (selfie segmenter landscape).
    Devuelve mascara float32 de la persona en cada frame.
    Instancia unica - no se recrea por frame.
    Requiere: models/selfie_segmenter_landscape.tflite
    """

    def __init__(self, model_path: str):
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_confidence_masks=True,
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)
        logger.info(f"PersonSegmentor inicializado desde: {model_path}")

    def get_mask(self, frame_bgr: np.ndarray, blur_radius: int = 21) -> np.ndarray:
        """
        Retorna mascara float32 (H, W) con valores 0.0-1.0.
        1.0 = persona, 0.0 = fondo.
        blur_radius: suavizado de bordes para compositing natural (debe ser impar).
        """
        h, w = frame_bgr.shape[:2]
        # Asegurar array contiguo (requerido por mediapipe)
        frame_rgb = cv2.cvtColor(np.ascontiguousarray(frame_bgr), cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self.segmenter.segment(mp_image)

        if result.confidence_masks is None or len(result.confidence_masks) == 0:
            # Fallback: toda la imagen es persona
            return np.ones((h, w), dtype=np.float32)

        mask = result.confidence_masks[0].numpy_view()

        # Resize si el modelo output difiere del input
        if mask.shape[:2] != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        # Suavizado de bordes para transicion natural
        if blur_radius > 1:
            r = blur_radius if blur_radius % 2 == 1 else blur_radius + 1
            mask = cv2.GaussianBlur(mask, (r, r), 0)

        return np.clip(mask, 0.0, 1.0)

    def close(self):
        self.segmenter.close()
