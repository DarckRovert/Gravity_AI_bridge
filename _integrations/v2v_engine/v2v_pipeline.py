import os
import cv2
import numpy as np
import pyvirtualcam
import onnxruntime as ort
import time

class V2VPipeline:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
        self.sessions = {}
        self.load_models()

    def load_models(self):
        print("[V2VPipeline] Iniciando carga de modelos ONNX via DirectML...")
        try:
            self.sessions['appearance'] = ort.InferenceSession(os.path.join(self.models_dir, 'appearance_feature_extractor.onnx'), providers=self.providers)
            self.sessions['motion'] = ort.InferenceSession(os.path.join(self.models_dir, 'motion_extractor.onnx'), providers=self.providers)
            self.sessions['spade'] = ort.InferenceSession(os.path.join(self.models_dir, 'spade_generator.onnx'), providers=self.providers)
            print("[V2VPipeline] Modelos cargados exitosamente (FP16).")
        except Exception as e:
            print(f"[V2VPipeline] Advertencia al cargar modelos: {e}. El sistema funcionara en modo Mock para demostracion.")

    def run(self, avatar_path, width=512, height=512, fps=30):
        print(f"[V2VPipeline] Inicializando webcam virtual {width}x{height} a {fps} FPS...")
        
        # Leer imagen base
        if os.path.exists(avatar_path):
            avatar_img = cv2.imread(avatar_path)
            avatar_img = cv2.resize(avatar_img, (width, height))
            avatar_rgb = cv2.cvtColor(avatar_img, cv2.COLOR_BGR2RGB)
        else:
            print("[V2VPipeline] No se encontro avatar_path. Usando fondo negro.")
            avatar_rgb = np.zeros((height, width, 3), dtype=np.uint8)

        # Iniciar captura de webcam fisica (indice 0)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[V2VPipeline] ERROR: No se pudo abrir la webcam fisica.")
            return

        try:
            with pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=pyvirtualcam.PixelFormat.RGB) as cam:
                print(f"[V2VPipeline] Camara virtual activa: {cam.device}. Presiona Ctrl+C para detener.")
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 1. Extraccion de movimiento (Mock de Inferencia)
                    # En la version completa, aqui se hace preprocesamiento (crop), se pasa por 'motion', 'warp' y 'spade'
                    # Simularemos que aplicamos una capa sobre el avatar original para demostrar la arquitectura.
                    
                    # 2. Generacion del frame resultante
                    # Hacemos un blend simple entre la webcam y el avatar (solo por dar feedback visual en OBS si faltan pesos)
                    frame_resized = cv2.resize(frame, (width, height))
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    
                    output_frame = cv2.addWeighted(avatar_rgb, 0.7, frame_rgb, 0.3, 0)
                    
                    cam.send(output_frame)
                    cam.sleep_until_next_frame()
                    
        except KeyboardInterrupt:
            print("[V2VPipeline] Detenido por el usuario.")
        finally:
            cap.release()
            print("[V2VPipeline] Recursos liberados.")

if __name__ == "__main__":
    MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
    AVATAR_PATH = os.path.join(os.path.dirname(__file__), "reference_avatar.jpg")
    
    # Crear un avatar dummy si no existe
    if not os.path.exists(AVATAR_PATH):
        dummy = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(dummy, "AVATAR BASE", (150, 256), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(AVATAR_PATH, dummy)

    pipeline = V2VPipeline(MODELS_DIR)
    pipeline.run(AVATAR_PATH)
