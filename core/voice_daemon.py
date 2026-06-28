"""
Módulo 1: Subsistema Vocal (Oídos y Voz)
Demonio que escucha pasivamente, transcribe audio usando faster-whisper y responde usando pyttsx3.
"""

import sounddevice as sd
import numpy as np
import pyttsx3
import queue
import time
import threading
import json
import websocket

class VoiceDaemon:
    def __init__(self):
        # Configurar TTS (Voz)
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        # Intentar buscar una voz en español
        for voice in voices:
            if "spanish" in voice.name.lower() or "es-es" in voice.id.lower() or "es-mx" in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
                
        self.engine.setProperty('rate', 160)  # Velocidad de habla
        
        # Audio config
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        # Whisper STT se cargará bajo demanda para ahorrar RAM
        self.whisper_model = None

    def speak(self, text: str):
        """Reproduce texto a voz (TTS)."""
        print(f"[JARVIS-VOICE] Diciendo: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback llamado por sounddevice para cada bloque de audio."""
        if status:
            print(status)
        if self.is_listening:
            self.audio_queue.put(indata.copy())

    def record_audio(self, duration=5):
        """Graba audio del micrófono durante 'duration' segundos."""
        print(f"[JARVIS-VOICE] Escuchando por {duration} segundos...")
        self.is_listening = True
        
        # Limpiar cola
        while not self.audio_queue.empty():
            self.audio_queue.get()
            
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32', callback=self._audio_callback):
            time.sleep(duration)
            
        self.is_listening = False
        
        # Concatenar todos los fragmentos
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
            
        if audio_data:
            return np.concatenate(audio_data, axis=0).flatten()
        return np.array([])

    def transcribe(self, audio_array):
        """Usa faster-whisper para transcribir el audio grabado."""
        if self.whisper_model is None:
            print("[JARVIS-VOICE] Cargando modelo Whisper (tiny)...")
            from faster_whisper import WhisperModel
            # Usamos tiny para que sea rápido en la CPU local
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
        print("[JARVIS-VOICE] Transcribiendo...")
        # faster-whisper acepta audio en float32
        segments, info = self.whisper_model.transcribe(audio_array, beam_size=5, language="es")
        
        text = " ".join([segment.text for segment in segments])
        print(f"[JARVIS-VOICE] Texto detectado: {text.strip()}")
        return text.strip()

    def ws_listener(self):
        """Hilo para escuchar respuestas del Sensory Bus y hablar."""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "voice_output":
                    self.speak(data.get("text", ""))
            except Exception as e:
                print(f"[JARVIS-VOICE] Error procesando WS: {e}")
                
        def on_error(ws, error):
            print(f"[JARVIS-VOICE] WS Error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print("[JARVIS-VOICE] Desconectado del Sensory Bus. Reconectando en 5s...")
            time.sleep(5)
            self.start_ws()

        def on_open(ws):
            print("[JARVIS-VOICE] Conectado exitosamente al Sensory Bus (ws://localhost:9999)")

        self.ws = websocket.WebSocketApp("ws://localhost:9999",
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
        self.ws.run_forever()

    def start_ws(self):
        threading.Thread(target=self.ws_listener, daemon=True).start()

    def run_demo(self):
        """Ciclo continuo J.A.R.V.I.S."""
        self.start_ws()
        self.speak("Subsistema vocal en línea. Esperando bus neuronal.")
        time.sleep(2)
        
        while True:
            # Grabar audio en bloques de 5 segundos (esto se refinará con VAD después)
            audio = self.record_audio(duration=5)
            texto = self.transcribe(audio)
            
            if texto and len(texto) > 5:
                print(f"[JARVIS-VOICE] Enviando al bus: {texto}")
                if hasattr(self, 'ws') and self.ws.sock and self.ws.sock.connected:
                    payload = json.dumps({"type": "voice_input", "text": texto})
                    self.ws.send(payload)
                else:
                    print("[JARVIS-VOICE] Bus desconectado. Texto descartado.")
            time.sleep(0.1)

if __name__ == "__main__":
    daemon = VoiceDaemon()
    daemon.run_demo()
