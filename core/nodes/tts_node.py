"""
Gravity Workflow Node: TTSGenerator
Convierte texto a audio usando pyttsx3/SAPI Windows o el motor de audio de Gravity.
"""

import os
import tempfile
from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class TTSGeneratorNode(GravityNode):
    NODE_TYPE = "TTSGenerator"
    DESCRIPTION = "Convierte texto a audio usando el motor TTS de Gravity (SAPI/pyttsx3)."
    INPUT_SCHEMA = {
        "text": "TEXT",
        "output_path": "TEXT",   # opcional
        "voice_id": "TEXT",      # opcional
        "rate": "INT",           # opcional, default 150
        "lang": "TEXT",          # opcional, default "es"
    }
    OUTPUT_SCHEMA = {
        "audio_path": "AUDIO",
        "duration_s": "FLOAT",
        "success": "BOOL",
    }

    def execute(self, inputs: dict) -> dict:
        from core.video.audio_processor import _generate_audio

        text: str = inputs.get("text", "")
        output_path: str = inputs.get("output_path", "")
        voice_id: str = inputs.get("voice_id") or self.config.get("voice_id") or ""
        rate: int = int(inputs.get("rate") or self.config.get("rate") or 150)
        lang: str = inputs.get("lang") or self.config.get("lang") or "es"

        if not output_path:
            output_path = os.path.join(tempfile.gettempdir(), f"gravity_tts_{id(self)}.wav")

        log.info(f"[TTSGeneratorNode] Generando audio para: {text[:60]}...")

        try:
            audio_path = _generate_audio(
                text=text,
                out_path=output_path,
                rate=rate,
                voice_id=voice_id,
                lang=lang,
            )
            duration_s = 0.0
            if audio_path and os.path.exists(audio_path):
                size = os.path.getsize(audio_path)
                # Estimación conservadora: WAV PCM 16-bit 22050Hz mono ≈ 44100 bytes/s
                duration_s = round(size / 44100, 2)

            return {
                "audio_path": audio_path or "",
                "duration_s": duration_s,
                "success": bool(audio_path),
            }
        except Exception as exc:
            log.error(f"[TTSGeneratorNode] Error: {exc}")
            return {"audio_path": "", "duration_s": 0.0, "success": False}
