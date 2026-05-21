import os
import sys
import cv2
import numpy as np
import logging

# Insertar FasterLivePortrait en el path
flp_path = os.path.join(os.path.dirname(__file__), 'models', 'FasterLivePortrait')
if flp_path not in sys.path:
    sys.path.insert(0, flp_path)

from omegaconf import OmegaConf
from src.pipelines.faster_live_portrait_pipeline import FasterLivePortraitPipeline

logger = logging.getLogger(__name__)

class MotionDriver:
    def __init__(self, is_animal=False):
        logger.info(f"Inicializando LivePortrait {'(Animal)' if is_animal else '(Humano)'}...")
        
        cfg_path = os.path.join(flp_path, 'configs', 'onnx_infer.yaml')
        self.cfg = OmegaConf.load(cfg_path)
        
        # Forzar ONNXRuntime
        for model_name in self.cfg.models:
            self.cfg.models[model_name]['predict_type'] = 'ort'
            # Corregir rutas relativas
            model_path = self.cfg.models[model_name]['model_path']
            if isinstance(model_path, str):
                self.cfg.models[model_name]['model_path'] = os.path.join(flp_path, model_path)
            else:
                self.cfg.models[model_name]['model_path'] = [os.path.join(flp_path, p) for p in model_path]

        for model_name in self.cfg.animal_models:
            self.cfg.animal_models[model_name]['predict_type'] = 'ort'
            model_path = self.cfg.animal_models[model_name]['model_path']
            if isinstance(model_path, str):
                self.cfg.animal_models[model_name]['model_path'] = os.path.join(flp_path, model_path)
            else:
                self.cfg.animal_models[model_name]['model_path'] = [os.path.join(flp_path, p) for p in model_path]

        # Fix relative path for mask_crop_path
        if 'mask_crop_path' in self.cfg.infer_params:
            self.cfg.infer_params.mask_crop_path = os.path.join(flp_path, self.cfg.infer_params.mask_crop_path)

        self.pipeline = FasterLivePortraitPipeline(cfg=self.cfg, is_animal=is_animal)
        self.is_prepared = False
        self.source_img = None
        self.is_animal = is_animal

    def set_source_image(self, img_bgr: np.ndarray):
        """Prepara el pipeline con la imagen fuente (Avatar generado por SD)"""
        # Guardamos temporalmente en disco porque el pipeline espera un path
        temp_path = os.path.join(os.path.dirname(__file__), 'scratch', 'temp_source.jpg')
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        cv2.imwrite(temp_path, img_bgr)
        
        success = self.pipeline.prepare_source(temp_path, realtime=True)
        if success:
            self.is_prepared = True
            self.source_img = img_bgr
            logger.info("Source Avatar registrado exitosamente en LivePortrait.")
        else:
            logger.error("LivePortrait no pudo encontrar un rostro en el Avatar generado.")
            self.is_prepared = False

    def animate(self, frame_bgr: np.ndarray, first_frame: bool = False) -> np.ndarray | None:
        """
        Anima el avatar base usando el frame_bgr de la webcam.
        Retorna BGR del avatar animado, o None si no hay source preparado
        o si LivePortrait no detectó cara en este frame.
        """
        if not self.is_prepared or self.source_img is None:
            return None

        # Asegurar array contiguo para ONNX (cv2 a veces produce non-contiguous)
        frame_in = np.ascontiguousarray(frame_bgr)
        src_in   = np.ascontiguousarray(self.source_img)

        try:
            img_crop, out_crop, out_full, dri_motion_info = self.pipeline.run(
                image=frame_in,
                img_src=src_in,
                src_info=self.pipeline.src_infos[0],
                realtime=True,
                first_frame=first_frame
            )
        except Exception as e:
            logger.error(f"Error en pipeline.run: {e}")
            return None

        if out_full is None:
            # LivePortrait no detectó cara en la webcam este frame
            return self.source_img

        # Clip para evitar valores fuera de rango uint8 (puede ocurrir con pasteback)
        return np.clip(out_full, 0, 255).astype(np.uint8)
