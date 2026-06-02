import os
import logging
import threading
from typing import List, Dict, Any
from faster_whisper import WhisperModel

# Configurar logger
logger = logging.getLogger("WhisperEngine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Locks de nivel de módulo y cachés estáticas
_whisper_init_lock = threading.Lock()
_whisper_transcribe_lock = threading.Lock()
_model_cache: Dict[tuple, WhisperModel] = {}

class WhisperEngine:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Inicializa el motor de Faster-Whisper de forma segura y thread-safe reutilizando instancias.
        Optimizado nativamente para CPU (Gráficas integradas) usando int8 para no saturar memoria.
        """
        with _whisper_init_lock:
            cache_key = (model_size, device, compute_type)
            if cache_key in _model_cache:
                logger.info(f"Reutilizando instancia de modelo cacheada para '{model_size}' en {device} ({compute_type}).")
                self.model = _model_cache[cache_key]
                return
            
            logger.info(f"Cargando modelo faster-whisper '{model_size}' en {device} ({compute_type})...")
            try:
                self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
                _model_cache[cache_key] = self.model
                logger.info("Modelo cargado exitosamente en caché (Optimizacion Integrada).")
            except Exception as e:
                logger.critical(f"Falla catastrófica cargando faster-whisper en {device}: {e}.")
                raise RuntimeError(f"Error cargando motor Whisper: {e}") from e

    def extract_words(self, audio_path: str, language: str = "es") -> List[Dict[str, Any]]:
        """
        Transcribe el audio y devuelve una lista de diccionarios con tiempos por palabra.
        [{'word': 'Hola', 'start': 0.0, 'end': 0.5}, ...]
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio no encontrado: {audio_path}")

        logger.info(f"Extrayendo timestamps para {os.path.basename(audio_path)}")
        
        # Sincronizamos la llamada a .transcribe()
        with _whisper_transcribe_lock:
            try:
                # word_timestamps=True es vital para los subtítulos dinámicos
                segments, info = self.model.transcribe(audio_path, beam_size=5, language=language, word_timestamps=True)
                
                # Consumir generador de forma inmediata bajo el lock para evitar race conditions
                segments = list(segments)
            except Exception as e:
                logger.error(f"Error transcribiendo audio con Faster-Whisper: {e}")
                raise RuntimeError(f"Fallo en transcripción Whisper: {e}") from e
        
        words_data = []
        for segment in segments:
            if not segment.words:
                continue
            for word in segment.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3)
                })
                
        logger.info(f"Se extrajeron {len(words_data)} palabras.")
        return words_data

if __name__ == "__main__":
    # Prueba rápida
    import sys
    if len(sys.argv) > 1:
        engine = WhisperEngine()
        res = engine.extract_words(sys.argv[1])
        print(res[:5]) # Imprime las 5 primeras
