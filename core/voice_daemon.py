"""
Módulo 1: Subsistema Vocal (Oídos y Voz Neural) - V16.7 PRO
Demonio que escucha pasivamente usando SpeechRecognition (True VAD)
y responde con voces neurales usando edge-tts.
"""

import os
import json
import time
import asyncio
import threading
import websocket
import speech_recognition as sr
import edge_tts
import pygame
import uuid
from core.logger import log

class VoiceDaemonV2:
    def __init__(self):
        # Configurar pygame mixer para reproducción fluida de TTS MP3
        pygame.mixer.init()
        
        # Voz hiperrealista de Microsoft Edge (Español de España o México)
        self.tts_voice = "es-MX-JorgeNeural" 
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Nivel de ruido mínimo
        self.recognizer.dynamic_energy_threshold = True

        self.whisper_model = None
        self.is_speaking = False
        self.ws = None

    def play_audio(self, file_path):
        """Reproduce un archivo MP3 usando pygame."""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        try:
            os.remove(file_path)
        except:
            pass

    async def _async_speak(self, text: str):
        """Genera el TTS neural y lo reproduce."""
        self.is_speaking = True
        log.info(f"[JARVIS-VOICE] Diciendo: {text}")
        output_file = f"temp_response_{uuid.uuid4().hex}.mp3"
        try:
            communicate = edge_tts.Communicate(text, self.tts_voice)
            await communicate.save(output_file)
            self.play_audio(output_file)
        except Exception as e:
            log.error(f"[JARVIS-VOICE] Error en TTS neural: {e}")
        finally:
            self.is_speaking = False

    def speak(self, text: str):
        """Wrapper síncrono para llamar al TTS asíncrono."""
        asyncio.run(self._async_speak(text))

    def _load_whisper(self):
        if self.whisper_model is None:
            log.info("[JARVIS-VOICE] Cargando modelo Whisper (tiny)...")
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def listen_and_transcribe(self):
        """Escucha usando el micrófono con VAD dinámico (SpeechRecognition)."""
        with sr.Microphone(sample_rate=16000) as source:
            log.info("[JARVIS-VOICE] Calibrando ruido de fondo...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            log.info("[JARVIS-VOICE] Escuchando (VAD Activo)...")
            
            while True:
                if self.is_speaking:
                    time.sleep(0.5)
                    continue
                    
                try:
                    # phrase_time_limit evita que se quede colgado en ruidos muy largos
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=15)
                    log.info("[JARVIS-VOICE] Procesando frase...")
                    
                    self._load_whisper()
                    
                    # Guardar temporalmente a wav para faster-whisper
                    with open("temp_record.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                        
                    segments, info = self.whisper_model.transcribe("temp_record.wav", beam_size=5, language="es")
                    text = " ".join([segment.text for segment in segments]).strip()
                    
                    if text and len(text) > 5:
                        log.info(f"[JARVIS-VOICE] Escuché: {text}")
                        self._send_to_bus(text)
                        
                except sr.WaitTimeoutError:
                    pass # Timeout normal, no hablaron
                except Exception as e:
                    log.error(f"[JARVIS-VOICE] Error en escucha: {e}")

    def _send_to_bus(self, text):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            payload = json.dumps({"type": "voice_input", "text": text})
            self.ws.send(payload)
        else:
            log.warning("[JARVIS-VOICE] Bus desconectado. Audio descartado.")

    def ws_listener(self):
        """Hilo para escuchar respuestas del Sensory Bus."""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "voice_output":
                    # Hablar en un hilo para no bloquear el websocket
                    threading.Thread(target=self.speak, args=(data.get("text", ""),)).start()
            except Exception as e:
                log.error(f"[JARVIS-VOICE] Error procesando WS: {e}")

        def on_error(ws, error):
            log.error(f"[JARVIS-VOICE] WS Error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            log.info("[JARVIS-VOICE] Conectado exitosamente al Sensory Bus (ws://localhost:9999)")

        while True:
            try:
                self.ws = websocket.WebSocketApp("ws://localhost:9999",
                                                on_open=on_open,
                                                on_message=on_message,
                                                on_error=on_error,
                                                on_close=on_close)
                self.ws.run_forever()
            except Exception:
                pass
            
            log.warning("[JARVIS-VOICE] WS desconectado. Reconectando en 5s...")
            time.sleep(5)

    def start_ws(self):
        threading.Thread(target=self.ws_listener, daemon=True, name="JarvisVoiceWS").start()

    def run(self):
        """Punto de entrada principal."""
        self.start_ws()
        # Dar tiempo al bus para conectar
        time.sleep(1) 
        self.speak("Sistemas vocales recalibrados. Operando en Nivel Neural.")
        
        # Bloquea el hilo principal con el bucle de escucha
        self.listen_and_transcribe()


if __name__ == "__main__":
    daemon = VoiceDaemonV2()
    daemon.run()
