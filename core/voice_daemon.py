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

    def run_demo(self):
        """Demo funcional del ciclo Oído -> Cerebro -> Voz."""
        self.speak("Iniciando subsistema vocal. Sistemas en línea.")
        time.sleep(1)
        
        # Simular que escuchó la wake word
        audio = self.record_audio(duration=4)
        texto = self.transcribe(audio)
        
        if texto:
            self.speak("He procesado tu comando: " + texto)
        else:
            self.speak("No he detectado entrada de voz.")

if __name__ == "__main__":
    daemon = VoiceDaemon()
    daemon.run_demo()
