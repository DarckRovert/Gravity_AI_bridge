import asyncio
import base64
import cv2
import io
import json
import logging
import threading
import time
from PIL import Image

logger = logging.getLogger("v2v_pipeline")

try:
    from diffusers import OnnxStableDiffusionImg2ImgPipeline
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("No se encontraron modulos ONNX. Funcionando en modo passthrough (Webcam test).")

class V2VPipeline:
    def __init__(self):
        self.clients = set()
        self.running = False
        self.ai_active = False  # Changed: controlled by frontend
        self.thread = None
        
        self.prompt = "cinematic, detailed, high quality, masterpiece"
        self.negative_prompt = "low quality, blurry, worst quality, mutated"
        self.strength = 0.5
        self.guidance_scale = 7.5
        
        self.model_dir = "models/sd15_turbo_onnx"
        self.pipe = None
        
        # Iniciar camara (Webcam local)
        self.cap = cv2.VideoCapture(0)
        # Reducir resolucion para mejorar FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 384)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
        
        self._load_model()

    def _load_model(self):
        if not ONNX_AVAILABLE:
            return
            
        import os
        if not os.path.exists(self.model_dir):
            logger.warning(f"Directorio de modelos '{self.model_dir}' no encontrado. Usa optimize_models.py primero.")
            return
            
        logger.info("Cargando modelo ONNX en iGPU (DMLExecutionProvider)...")
        try:
            # Usar DirectML
            provider = "DMLExecutionProvider"
            self.pipe = OnnxStableDiffusionImg2ImgPipeline.from_pretrained(
                self.model_dir,
                provider=provider
            )
            # Desactivar checker para mas velocidad
            self.pipe.safety_checker = None
            logger.info("Modelo cargado exitosamente.")
        except Exception as e:
            logger.error(f"Error cargando ONNX: {e}")
            self.pipe = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._capture_and_process_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap.isOpened():
            self.cap.release()

    def add_client(self, websocket):
        self.clients.add(websocket)

    def remove_client(self, websocket):
        if websocket in self.clients:
            self.clients.remove(websocket)

    def update_config(self, config: dict):
        if "prompt" in config:
            self.prompt = config["prompt"]
        if "negative_prompt" in config:
            self.negative_prompt = config["negative_prompt"]
        if "strength" in config:
            self.strength = float(config["strength"])
        if "guidance_scale" in config:
            self.guidance_scale = float(config["guidance_scale"])

    def _broadcast_frame(self, frame_b64: str):
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "frame",
            "data": f"data:image/jpeg;base64,{frame_b64}"
        })
        
        # Enviar a todos los websockets
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _send_all():
            tasks = []
            for ws in list(self.clients):
                try:
                    tasks.append(ws.send_text(message))
                except Exception:
                    pass
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        loop.run_until_complete(_send_all())
        loop.close()

    def _capture_and_process_loop(self):
        logger.info("V2V Inferencia iniciada.")
        
        while self.running:
            start_t = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Convertir BGR (OpenCV) a RGB (PIL)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Ajustar tamano (SD 1.5 necesita multiplos de 8)
            # Usaremos 384x384 para maximos FPS en iGPU
            pil_image = pil_image.resize((384, 384), Image.LANCZOS)
            
            result_img = pil_image
            
            # Inferencia ONNX (si el modelo esta cargado y AI activa)
            if self.pipe and self.ai_active:
                try:
                    out = self.pipe(
                        prompt=self.prompt,
                        image=pil_image,
                        negative_prompt=self.negative_prompt,
                        strength=self.strength,
                        guidance_scale=self.guidance_scale,
                        num_inference_steps=4  # Turbo usa muy pocos pasos (1-4)
                    )
                    result_img = out.images[0]
                except Exception as e:
                    logger.error(f"Fallo en inferencia V2V: {e}")

            # Codificar a Base64 para enviarlo al frontend
            buffered = io.BytesIO()
            result_img.save(buffered, format="JPEG", quality=80)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            self._broadcast_frame(img_str)
            
            # Control simple de FPS
            elapsed = time.time() - start_t
            sleep_time = max(0, (1.0 / 15.0) - elapsed)  # Cap maximo 15 FPS
            time.sleep(sleep_time)
