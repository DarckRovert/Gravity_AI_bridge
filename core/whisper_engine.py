import os
from typing import Optional

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import logging
import threading
from typing import List, Dict, Any

# Configurar logger
logger = logging.getLogger("WhisperEngine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Locks de nivel de módulo y cachés estáticas
_whisper_init_lock = threading.Lock()
_whisper_transcribe_lock = threading.Lock()
_model_cache: Dict[tuple, Any] = {}


class WhisperEngine:
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cpu",
        compute_type: str = "int8",
        use_npu: bool = True,
    ):
        """
        Inicializa el motor de reconocimiento. Intenta usar ONNX Runtime (DirectML) para NPU si use_npu es True.
        Si falla o no está disponible, hace fallback seguro a Faster-Whisper optimizado para CPU.
        """
        self.use_npu = use_npu
        with _whisper_init_lock:
            cache_key = (model_size, device, compute_type, self.use_npu)
            if cache_key in _model_cache:
                logger.info(
                    f"Reutilizando instancia de modelo cacheada (NPU={self.use_npu})."
                )
                self.model = _model_cache[cache_key]
                return

            if self.use_npu:
                try:
                    logger.info(
                        "Fase 3: Intentando activar motor ONNX Runtime para aceleración NPU/DirectML..."
                    )
                    from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
                    from transformers import AutoProcessor, pipeline

                    model_id = f"openai/whisper-{model_size}"
                    processor = AutoProcessor.from_pretrained(model_id)
                    model = ORTModelForSpeechSeq2Seq.from_pretrained(
                        model_id, export=True, provider="DmlExecutionProvider"
                    )
                    self.model = pipeline(
                        "automatic-speech-recognition",
                        model=model,
                        tokenizer=processor.tokenizer,
                        feature_extractor=processor.feature_extractor,
                        return_timestamps="word",
                    )
                    _model_cache[cache_key] = self.model
                    logger.info("¡Modelo ONNX cargado exitosamente en NPU/DirectML!")
                    return
                except ImportError:
                    logger.warning(
                        "Librerías 'optimum' o 'transformers' no encontradas. Cayendo a Faster-Whisper..."
                    )
                    self.use_npu = False
                except Exception as e:
                    logger.warning(
                        f"Error cargando NPU/DirectML: {e}. Cayendo a Faster-Whisper..."
                    )
                    self.use_npu = False

            if not self.use_npu:
                from faster_whisper import WhisperModel

                logger.info(
                    f"Cargando modelo faster-whisper '{model_size}' en {device} ({compute_type})..."
                )
                self.model = WhisperModel(
                    model_size, device=device, compute_type=compute_type
                )
                _model_cache[cache_key] = self.model
                logger.info(
                    "Modelo cargado exitosamente en caché (Optimizacion Integrada)."
                )

    def extract_words(
        self, audio_path: str, language: str = "es", initial_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe el audio y devuelve una lista de diccionarios con tiempos por palabra.
        [{'word': 'Hola', 'start': 0.0, 'end': 0.5}, ...]
        Si se provee initial_prompt, se usa para guiar a la IA y evitar alucinaciones fonéticas.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio no encontrado: {audio_path}")

        logger.info(f"Extrayendo timestamps para {os.path.basename(audio_path)}")

        words_data = []
        with _whisper_transcribe_lock:
            try:
                if not hasattr(self.model, "transcribe"):
                    logger.info("Transcribiendo usando Pipeline ONNX (DirectML)...")
                    result = self.model(
                        audio_path, generate_kwargs={"language": "spanish"}
                    )
                    for chunk in result.get("chunks", []):
                        ts = chunk["timestamp"]
                        if ts[0] is not None and ts[1] is not None:
                            words_data.append(
                                {
                                    "word": chunk["text"].strip(),
                                    "start": round(ts[0], 3),
                                    "end": round(ts[1], 3),
                                }
                            )
                else:
                    segments, info = self.model.transcribe(
                        audio_path,
                        beam_size=5,
                        language=language,
                        word_timestamps=True,
                        initial_prompt=initial_prompt,
                    )
                    segments = list(segments)
                    for segment in segments:
                        if not segment.words:
                            continue
                        for word in segment.words:
                            words_data.append(
                                {
                                    "word": word.word.strip(),
                                    "start": round(word.start, 3),
                                    "end": round(word.end, 3),
                                }
                            )
            except Exception as e:
                logger.error(f"Error transcribiendo audio: {e}")
                raise RuntimeError(f"Fallo en transcripción Whisper: {e}") from e

        logger.info(f"Se extrajeron {len(words_data)} palabras.")
        return words_data


if __name__ == "__main__":
    # Prueba rápida
    import sys

    if len(sys.argv) > 1:
        engine = WhisperEngine()
        res = engine.extract_words(sys.argv[1])
        print(res[:5])  # Imprime las 5 primeras
