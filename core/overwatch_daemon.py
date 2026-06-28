"""
Módulo J.A.R.V.I.S: Overwatch Visual (Pilar 3)
Captura en background usando MSS y clasifica con un modelo de visión ligero.
"""

import time
import mss
import mss.tools
import base64
import os
import threading
import requests
import json
from core.logger import log

class OverwatchDaemon:
    def __init__(self, interval=15):
        self.interval = interval
        self.running = False
        self._thread = None
        # Definir un modelo de visión local (ej. moondream o llava-phi3)
        self.vision_model = "llava-phi3" 
        self.ollama_url = "http://localhost:11434/api/generate"
        
        self.scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scratch")
        if not os.path.exists(self.scratch_dir):
            os.makedirs(self.scratch_dir)
            
        self.context_file = os.path.join(self.scratch_dir, "current_context.txt")

    def capture_frame(self) -> str:
        """Captura el monitor primario y retorna la imagen en Base64."""
        with mss.mss() as sct:
            # Tomamos el primer monitor
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            raw_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            return base64.b64encode(raw_bytes).decode('utf-8')

    def analyze_frame(self, b64_img: str) -> str:
        """Envía el frame a Ollama para extraer contexto."""
        prompt = "En una línea breve, describe qué está haciendo el usuario en esta pantalla (ej. 'Programando en VSCode', 'Viendo YouTube')."
        
        payload = {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [b64_img],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 1024
            }
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                return f"Error Ollama: {resp.status_code}"
        except Exception as e:
            return "Visión temporalmente offline (Ollama inactivo o modelo no cargado)."

    def loop(self):
        log.info("[JARVIS-Overwatch] Iniciando vigilancia subconsciente.")
        while self.running:
            try:
                b64 = self.capture_frame()
                context = self.analyze_frame(b64)
                
                # Escribir al scratch circular
                with open(self.context_file, "w", encoding="utf-8") as f:
                    f.write(f"[Contexto Visual en tiempo real]: {context}")
                    
            except Exception as e:
                log.error(f"[JARVIS-Overwatch] Error en loop: {e}")
                
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self.loop, daemon=True, name="OverwatchDaemon")
            self._thread.start()
            
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

if __name__ == "__main__":
    daemon = OverwatchDaemon(interval=10)
    daemon.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
