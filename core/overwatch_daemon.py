"""
Módulo J.A.R.V.I.S: Overwatch Visual (Pilar 3)
Captura en background usando MSS y clasifica usando el provider_manager de Gravity.
Funciona con cualquier backend local activo: LM Studio, Ollama, Native Llama, etc.
"""

import time
import mss
import mss.tools
import base64
import os
import threading
from core.logger import log
from core import provider_manager

class OverwatchDaemon:
    def __init__(self, interval=15):
        self.interval = interval
        self.running = False
        self._thread = None

        self.scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scratch")
        if not os.path.exists(self.scratch_dir):
            os.makedirs(self.scratch_dir)

        self.context_file = os.path.join(self.scratch_dir, "current_context.txt")

    def capture_frame(self) -> str:
        """Captura el monitor primario y retorna la imagen en Base64."""
        with mss.MSS() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            raw_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            return base64.b64encode(raw_bytes).decode('utf-8')

    def analyze_frame(self, b64_img: str) -> str:
        """
        Usa el provider_manager de Gravity para analizar el frame.
        Intenta primero con un mensaje multimodal (visión).
        Si el provider activo no soporta visión, usa un fallback textual.
        """
        prompt = "En una línea breve, describe qué está haciendo el usuario en esta pantalla (ej. 'Programando en VSCode', 'Viendo YouTube')."

        try:
            bp, bm = provider_manager.get_best()
            if not bp:
                return "Overwatch offline: sin proveedor de IA activo."

            # Intentar con mensaje multimodal (formato OpenAI con image_url)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]
                }
            ]

            try:
                raw_text = provider_manager.complete(
                    messages,
                    model=bm,
                    provider=bp.name,
                    options={"temperature": 0.1, "max_tokens": 128}
                )
                result = (raw_text or "").strip()
                if result:
                    return result
            except Exception:
                # El provider no soporta visión multimodal — usar descripción de fallback
                pass

            # Fallback: confirmación de que visión no está disponible
            return "Visión no disponible en este proveedor (modelo sin capacidad multimodal)."

        except Exception as e:
            log.warning(f"[JARVIS-Overwatch] Error analizando frame: {e}")
            return "Visión temporalmente offline."

    def loop(self):
        log.info("[JARVIS-Overwatch] Iniciando vigilancia subconsciente.")
        while self.running:
            try:
                b64 = self.capture_frame()
                context = self.analyze_frame(b64)

                # Escribir al scratch circular
                with open(self.context_file, "w", encoding="utf-8") as f:
                    f.write(f"[Contexto Visual en tiempo real]: {context}")

                log.debug(f"[JARVIS-Overwatch] Contexto actualizado: {context}")

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

