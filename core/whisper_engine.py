import os
import logging
from faster_whisper import WhisperModel

# Configurar logger
logger = logging.getLogger("WhisperEngine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class WhisperEngine:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Inicializa el motor de Faster-Whisper.
        Por defecto usa 'base' en 'cpu' con 'int8' para no saturar memoria.
        """
        logger.info(f"Cargando modelo faster-whisper '{model_size}' en {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Modelo cargado exitosamente.")

    def extract_words(self, audio_path: str, language="es"):
        """
        Transcribe el audio y devuelve una lista de diccionarios con tiempos por palabra.
        [{'word': 'Hola', 'start': 0.0, 'end': 0.5}, ...]
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio no encontrado: {audio_path}")

        logger.info(f"Extrayendo timestamps para {os.path.basename(audio_path)}")
        
        # word_timestamps=True es vital para los subtítulos dinámicos
        segments, info = self.model.transcribe(audio_path, beam_size=5, language=language, word_timestamps=True)
        
        words_data = []
        for segment in segments:
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
