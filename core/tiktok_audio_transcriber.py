import os
import sys
import time
import shutil
import logging
import subprocess
import threading
from collections import deque
from typing import Dict, Any, List, Optional
from core.whisper_engine import WhisperEngine
from core.logger import log

_last_diarize_fail_time = 0.0

class AudioTranscriber:
    """
    Captura audio en vivo desde HLS (m3u8) y transcribe en tiempo real
    usando ffmpeg y WhisperEngine.
    """
    def __init__(self, username: str, stream_url: str, model_size: str = "tiny"):
        self.username = username.lstrip("@").lower()
        self.stream_url = stream_url
        self.model_size = model_size
        self.transcripts = deque(maxlen=200)  # [{"timestamp_ms": int, "text": str}, ...]
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._ffmpeg_proc: Optional[subprocess.Popen] = None
        
        # Carpeta temporal para fragmentos de audio
        _CORE_DIR = os.path.dirname(os.path.abspath(__file__))
        _BASE_DIR = os.path.dirname(_CORE_DIR)
        self.temp_dir = os.path.join(_BASE_DIR, "temp_audio", self.username)
        
        self._whisper: Optional[WhisperEngine] = None
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        
        # Limpiar y crear carpeta temporal
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"TikTokAudio-{self.username}",
            daemon=True
        )
        self._thread.start()
        log.info(f"[TikTokAudio·{self.username}] Transcriptor de audio iniciado.")

    def stop(self):
        self.running = False
        if self._ffmpeg_proc:
            try:
                self._ffmpeg_proc.terminate()
                self._ffmpeg_proc.wait(timeout=2)
            except Exception:
                try:
                    self._ffmpeg_proc.kill()
                except Exception:
                    pass
            self._ffmpeg_proc = None
            
        # Limpiar archivos temporales
        time.sleep(1)
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
        log.info(f"[TikTokAudio·{self.username}] Transcriptor de audio detenido.")

    def get_lines(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.transcripts)

    def _run_loop(self):
        # Cargar WhisperEngine localmente en este hilo para no bloquear el inicio
        try:
            self._whisper = WhisperEngine(model_size=self.model_size, device="cpu", compute_type="int8")
        except Exception as e:
            log.error(f"[TikTokAudio·{self.username}] Error cargando WhisperEngine: {e}")
            self.running = False
            return

        # Iniciar ffmpeg segmentador
        chunk_pattern = os.path.join(self.temp_dir, "chunk_%03d.wav")
        cmd = [
            "ffmpeg", "-y", "-i", self.stream_url,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-f", "segment", "-segment_time", "5",
            "-reset_timestamps", "1",
            chunk_pattern
        ]
        
        try:
            self._ffmpeg_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            log.error(f"[TikTokAudio·{self.username}] Error iniciando ffmpeg: {e}")
            self.running = False
            return

        current_idx = 0
        while self.running:
            # Esperar a que el siguiente fragmento empiece a escribirse,
            # lo que significa que el fragmento actual ya terminó de escribirse.
            next_file = os.path.join(self.temp_dir, f"chunk_{current_idx + 1:03d}.wav")
            curr_file = os.path.join(self.temp_dir, f"chunk_{current_idx:03d}.wav")
            
            if os.path.exists(next_file):
                # El fragmento actual está completo, lo transcribimos
                if os.path.exists(curr_file):
                    try:
                        # Extraer palabras
                        words = self._whisper.extract_words(curr_file)
                        text = " ".join([w["word"] for w in words]).strip()
                        if text:
                            # Filtro simple de alucinaciones vacías de Whisper
                            if len(text) > 2:
                                timestamp_ms = int(time.time() * 1000)
                                line_id = f"{timestamp_ms}_{current_idx}"
                                line_data = {
                                    "id": line_id,
                                    "timestamp_ms": timestamp_ms,
                                    "text": text,
                                    "speaker": "Detectando..."
                                }
                                with self._lock:
                                    self.transcripts.append(line_data)
                                log.debug(f"[TikTokAudio·{self.username}] Transcrito: {text}")
                                
                                # Lanzar clasificación cognitiva del hablante en segundo plano
                                threading.Thread(
                                    target=self._cognitive_diarize,
                                    args=(line_id, text),
                                    daemon=True
                                ).start()
                    except Exception as te:
                        log.error(f"[TikTokAudio·{self.username}] Error transcribiendo chunk_{current_idx:03d}: {te}")
                    finally:
                        # Eliminar el archivo procesado para ahorrar espacio en disco
                        try:
                            os.remove(curr_file)
                        except Exception:
                            pass
                current_idx += 1
            else:
                # Comprobar si el proceso de ffmpeg ha terminado inesperadamente
                if self._ffmpeg_proc.poll() is not None:
                    log.warning(f"[TikTokAudio·{self.username}] ffmpeg finalizó inesperadamente.")
                    break
                time.sleep(2)

    def _cognitive_diarize(self, line_id: str, text: str):
        """Asignación semántica/cognitiva del hablante en segundo plano utilizando el LLM."""
        global _last_diarize_fail_time
        
        # Si falló recientemente, omitimos para no saturar la NPU/IA local
        if time.time() - _last_diarize_fail_time < 120.0:
            with self._lock:
                for l in self.transcripts:
                    if l.get("id") == line_id:
                        l["speaker"] = "Streamer"
                        return
            return

        try:
            with self._lock:
                current_lines = list(self.transcripts)
            
            # Encontrar el índice de nuestra línea
            target_idx = -1
            for i, l in enumerate(current_lines):
                if l.get("id") == line_id:
                    target_idx = i
                    break
            
            if target_idx == -1:
                return

            # Construir el contexto del diálogo reciente (hasta 6 líneas previas)
            context_lines = current_lines[max(0, target_idx - 6):target_idx]
            dialogue_context = ""
            for l in context_lines:
                sp = l.get("speaker", "Streamer")
                if sp == "Detectando...":
                    sp = "Streamer"
                dialogue_context += f"[{sp}]: {l['text']}\n"
            
            dialogue_context += f"[Nueva Línea]: {text}"

            prompt = f"""
            Estás analizando la transcripción de un directo de debate o charla en TikTok Live.
            Identifica quién dice la "Nueva Línea" basándote en la semántica del diálogo reciente.

            DIÁLOGO RECIENTE:
            {dialogue_context}

            Reglas de clasificación:
            - Responde únicamente con uno de estos nombres de hablante: "Streamer" (el anfitrión), "Invitado 1", "Invitado 2", o "Moderador".
            - Si parece que es la misma persona que habló en el turno anterior continuando su idea, responde igual.
            - Si hay una respuesta directa, cambio de tono, pregunta al aire o vocativos ("mira", "amiga", "tú qué dices"), asume cambio de hablante a "Invitado 1" o "Streamer".
            - Si no estás seguro, responde "Streamer".

            Responde ÚNICAMENTE con la opción correspondiente (ej: Streamer o Invitado 1). Sin preámbulos.
            """

            from core import provider_manager
            best_prov, _ = provider_manager.get_best("any")
            if best_prov and best_prov.category != "local":
                # Para evitar saturar las APIs en la nube (ej. Groq 429) en diarización continua,
                # asumimos 'Streamer' si el proveedor principal disponible es de la nube.
                speaker = "Streamer"
            else:
                speaker = provider_manager.complete(
                    messages=[
                        {"role": "system", "content": "Eres un clasificador de turnos de diálogo preciso en español. Respondes con una sola palabra."},
                        {"role": "user", "content": prompt}
                    ],
                    task="any"
                )
                speaker = speaker.strip().replace("[", "").replace("]", "").replace('"', '').replace("'", "")
                if speaker not in ["Streamer", "Invitado 1", "Invitado 2", "Moderador"]:
                    speaker = "Streamer"
        except Exception:
            _last_diarize_fail_time = time.time()
            speaker = "Streamer"

        # Actualizar la línea con el hablante detectado
        with self._lock:
            for l in self.transcripts:
                if l.get("id") == line_id:
                    l["speaker"] = speaker
                    break
