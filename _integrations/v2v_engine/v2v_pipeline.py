import os
import numpy as np
import threading
import time
import base64
import json
import asyncio
from typing import Optional, Set, Any

try:
    import cv2
except ImportError:
    cv2 = None


class V2VPipeline:
    def __init__(self, models_dir: Optional[str] = None):
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = models_dir or os.path.join(base_path, "models")
        self.avatar_path = os.path.join(base_path, "reference_avatar.jpg")
        self.running: bool = False
        self.ai_active: bool = True
        self.clients: Set[Any] = set()
        self.lock = threading.Lock()
        self.current_fps: float = 0.0
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.config = {
            "preset": "cyberpunk_commander",
            "prompt": "",
            "negative_prompt": "low quality, blurry",
            "strength": 0.85,
        }
        self.load_models()

    def load_models(self):
        print(f"[V2VPipeline] Inicializando ONNX DirectML en {self.models_dir}...")
        self.models_ready = os.path.exists(os.path.join(self.models_dir, "spade_generator.onnx"))

    def add_client(self, ws):
        with self.lock:
            self.clients.add(ws)

    def remove_client(self, ws):
        with self.lock:
            self.clients.discard(ws)

    def update_config(self, cfg: dict):
        with self.lock:
            self.config.update(cfg)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _broadcast(self, msg: str):
        with self.lock:
            dead = []
            for client in list(self.clients):
                try:
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(client.send_text(msg), self.loop)
                except Exception:
                    dead.append(client)
            for d in dead:
                self.clients.discard(d)

    def _loop(self):
        print("[V2VPipeline] Bucle de captura y renderizado en vivo activado.")
        if cv2 is None:
            print("[V2VPipeline] OpenCV (cv2) no está disponible en este entorno Python.")
            while self.running:
                time.sleep(0.5)
            return

        cap = cv2.VideoCapture(0)
        width, height = 512, 512
        frame_count = 0
        t_start = time.time()

        if not os.path.exists(self.avatar_path):
            dummy = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.putText(dummy, "AVATAR V2V", (140, 256), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 200), 2)
            cv2.imwrite(self.avatar_path, dummy)

        avatar_img = cv2.imread(self.avatar_path)
        if avatar_img is not None:
            avatar_img = cv2.resize(avatar_img, (width, height))
        else:
            avatar_img = np.zeros((height, width, 3), dtype=np.uint8)

        while self.running:
            t0 = time.time()
            if cap.isOpened():
                ret, frame = cap.read()
            else:
                ret, frame = False, None

            if not ret or frame is None:
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                cv2.putText(frame, "WEBCAM NO DISPONIBLE", (80, 256), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                frame = cv2.resize(frame, (width, height))

            if self.ai_active:
                out_frame = cv2.addWeighted(avatar_img, 0.6, frame, 0.4, 0)
            else:
                out_frame = frame

            frame_count += 1
            elapsed = time.time() - t_start
            if elapsed >= 1.0:
                self.current_fps = round(frame_count / elapsed, 1)
                frame_count = 0
                t_start = time.time()

            _, buffer = cv2.imencode('.jpg', out_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            b64_frame = base64.b64encode(buffer).decode('utf-8')

            self._broadcast(json.dumps({
                "type": "frame",
                "data": b64_frame,
            }))

            dt = time.time() - t0
            sleep_time = max(0.001, (1.0 / 30.0) - dt)
            time.sleep(sleep_time)

        cap.release()
        print("[V2VPipeline] Recursos de cámara liberados.")


if __name__ == "__main__":
    pipeline = V2VPipeline()
    pipeline.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pipeline.stop()
