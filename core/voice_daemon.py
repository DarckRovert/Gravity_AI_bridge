"""
Módulo 1: Subsistema Vocal (Oídos y Voz Neural) - V16.7 PRO
Demonio que escucha pasivamente usando sounddevice y faster_whisper,
y responde con voces neurales usando edge-tts.
(Refactorizado con arquitectura asíncrona inspirada en GAIA)
"""

import os
import json
import time
import asyncio
import threading
import queue
import websocket
import edge_tts
import pygame
import uuid
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from core.logger import log

class VoiceDaemonV2:
    def __init__(self):
        # Configurar pygame mixer para reproducción fluida de TTS MP3
        pygame.mixer.init()
        
        # Voz hiperrealista de Microsoft Edge (Español de España o México)
        self.tts_voice = "es-MX-JorgeNeural" 
        
        self.whisper_model = None
        self.is_speaking = False
        self.ws = None

        # Parámetros de captura de audio (16kHz, mono)
        self.RATE = 16000
        self.CHANNELS = 1
        self.CHUNK = 1024 * 2
        self.DTYPE = "float32"
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Parámetros de Voice Activity Detection (VAD)
        self.SILENCE_THRESHOLD = 0.003
        self.MIN_AUDIO_LENGTH = self.RATE * 0.25 # Mínimo 250 ms de audio para procesar
        self.is_listening = False # True cuando detecta que alguien está hablando
        self.is_paused = False # Control remoto de micrófono
        
        # Referencias a hilos
        self.record_thread = None
        self.process_thread = None

    def play_audio(self, file_path):
        """Reproduce un archivo MP3 usando pygame."""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        try:
            os.remove(file_path)
        except OSError:
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
            # Carga del modelo tiny en CPU usando cuantización int8 (rápido y eficiente)
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def _is_speech(self, audio_chunk):
        """Detecta si hay voz basándose en la energía (amplitud) del audio."""
        return np.abs(audio_chunk).mean() > self.SILENCE_THRESHOLD

    def _record_audio(self):
        """Hilo dedicado a grabar audio de forma continua sin bloquearse."""
        try:
            log.info("[JARVIS-VOICE] Inicializando dispositivo de grabación...")
            stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype=self.DTYPE,
                blocksize=self.CHUNK,
            )
            stream.start()

            log.info("[JARVIS-VOICE] Escuchando (VAD Activo)...")
            
            speech_buffer = np.array([], dtype=np.float32)
            silence_counter = 0
            SILENCE_LIMIT = 10  # Número de chunks de silencio antes de finalizar la frase

            while self.is_recording:
                # Leer siempre del stream para evitar overflow (PortAudioError)
                frames, overflowed = stream.read(self.CHUNK)

                # Si Jarvis está hablando o está pausado, descartamos el audio de entrada
                if self.is_speaking or self.is_paused:
                    speech_buffer = np.array([], dtype=np.float32)
                    self.is_listening = False
                    continue

                data = frames[:, 0].copy()
                data = np.clip(data, -1, 1)

                if self._is_speech(data):
                    silence_counter = 0
                    speech_buffer = np.concatenate((speech_buffer, data))
                    if not self.is_listening and len(speech_buffer) > self.MIN_AUDIO_LENGTH:
                        self.is_listening = True
                else:
                    silence_counter += 1
                    if self.is_listening:
                        speech_buffer = np.concatenate((speech_buffer, data))
                        
                    # Si hubo suficiente silencio y estábamos escuchando, enviamos el audio a procesar
                    if silence_counter >= SILENCE_LIMIT and self.is_listening:
                        if len(speech_buffer) > self.MIN_AUDIO_LENGTH:
                            self.audio_queue.put(speech_buffer)
                        speech_buffer = np.array([], dtype=np.float32)
                        self.is_listening = False
                        silence_counter = 0

            stream.stop()
            stream.close()
        except Exception as e:
            log.error(f"[JARVIS-VOICE] Error crítico en la grabación (verifica sounddevice): {e}")

    def _process_audio(self):
        """Hilo dedicado a procesar y transcribir el audio usando faster_whisper."""
        self._load_whisper()
        while self.is_recording:
            try:
                # Obtenemos audio de la cola (se bloquea 1 seg. para no consumir CPU en vacío)
                audio_data = self.audio_queue.get(timeout=1.0)
                
                log.info("[JARVIS-VOICE] Procesando frase en memoria...")
                # faster_whisper soporta arrays de numpy float32 normalizados a [-1, 1] a 16kHz nativamente
                segments, info = self.whisper_model.transcribe(
                    audio_data, 
                    beam_size=5, 
                    language="es",
                    temperature=0.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False
                )
                text = " ".join([segment.text for segment in segments]).strip()
                
                if text and len(text) > 5:
                    log.info(f"[JARVIS-VOICE] Escuché: {text}")
                    self._send_to_bus(text)
            except queue.Empty:
                continue
            except Exception as e:
                log.error(f"[JARVIS-VOICE] Error transcribiendo el array: {e}")

    def listen_and_transcribe(self):
        """Inicia los hilos separados para escuchar y transcribir asíncronamente."""
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record_audio, daemon=True, name="JarvisRecorder")
        self.process_thread = threading.Thread(target=self._process_audio, daemon=True, name="JarvisProcessor")
        
        self.record_thread.start()
        self.process_thread.start()

        # Mantener el hilo principal activo
        while True:
            time.sleep(1)

    def _send_to_bus(self, text):
        """Envía el texto transcrito al Sensory Bus (websocket)."""
        try:
            if getattr(self, 'ws', None) and getattr(self.ws, 'sock', None) and self.ws.sock.connected:
                self.ws.send(json.dumps({"type": "voice_input", "text": text}))
            else:
                temp_ws = websocket.create_connection("ws://127.0.0.1:9999", timeout=5)
                temp_ws.send(json.dumps({"type": "voice_input", "text": text}))
                temp_ws.close()
        except Exception as e:
            log.warning(f"[JARVIS-VOICE] Bus desconectado. Audio descartado: {e}")

    def ws_listener(self):
        """Hilo para escuchar respuestas generadas desde el Sensory Bus."""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "voice_output":
                    # Hablar en un hilo para no bloquear el websocket ni la escucha
                    threading.Thread(target=self.speak, args=(data.get("text", ""),)).start()
                elif data.get("type") == "voice_daemon_ping":
                    ws.send(json.dumps({
                        "type": "voice_daemon_status",
                        "status": "online",
                        "threshold": self.SILENCE_THRESHOLD,
                        "paused": self.is_paused
                    }))
                elif data.get("type") == "voice_daemon_cmd":
                    action = data.get("action")
                    if action == "pause":
                        self.is_paused = True
                        log.info("[JARVIS-VOICE] Micrófono silenciado remotamente.")
                    elif action == "resume":
                        self.is_paused = False
                        log.info("[JARVIS-VOICE] Micrófono reanudado remotamente.")
                    elif action == "set_threshold":
                        val = data.get("value")
                        if val is not None:
                            self.SILENCE_THRESHOLD = float(val)
                            log.info(f"[JARVIS-VOICE] Sensibilidad ajustada a {self.SILENCE_THRESHOLD}")
                    # Broadcast updated status
                    ws.send(json.dumps({
                        "type": "voice_daemon_status",
                        "status": "online",
                        "threshold": self.SILENCE_THRESHOLD,
                        "paused": self.is_paused
                    }))
            except Exception as e:
                log.error(f"[JARVIS-VOICE] Error procesando WS: {e}")

        def on_error(ws, error):
            log.error(f"[JARVIS-VOICE] WS Error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            pass

        def on_open(ws):
            log.info("[JARVIS-VOICE] Conectado exitosamente al Sensory Bus (ws://127.0.0.1:9999)")

        while True:
            try:
                self.ws = websocket.WebSocketApp("ws://127.0.0.1:9999",
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
        self.speak("Sistemas vocales recalibrados y optimizados. Operando en Nivel Neural asíncrono.")
        
        # Bloquea el hilo principal con el bucle de mantenimiento de los hilos de audio
        self.listen_and_transcribe()


if __name__ == "__main__":
    daemon = VoiceDaemonV2()
    daemon.run()
