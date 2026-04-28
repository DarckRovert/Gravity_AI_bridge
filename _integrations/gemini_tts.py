"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI – GEMINI TTS ENGINE V1.0                                        ║
║  Motor de síntesis de voz premium via Google AI Studio (Gemini)             ║
║  Integrado como motor TIER-2 en el pipeline de Video Studio                 ║
║                                                                              ║
║  Jerarquía:                                                                  ║
║    1. win32com SAPI (offline, local)  ← siempre disponible                  ║
║    2. pyttsx3 (offline, fallback)     ← si win32com falla                   ║
║    3. Gemini TTS (online, premium)    ← si api_key configurada y calidad=4k  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Uso desde video_pipeline.py:
    from _integrations.gemini_tts import synthesize_gemini
    ok = synthesize_gemini(text, output_wav_path, voice="Charon", api_key=key)
"""

import os
import json
import base64
import struct
import urllib.request
import urllib.error
from typing import Optional


# Voces disponibles en Gemini 2.5 Flash TTS
GEMINI_VOICES: dict[str, str] = {
    "Aoede":    "Suave, narrativa, femenina",
    "Charon":   "Grave, autoritaria, masculina",
    "Fenrir":   "Dramática, épica, masculina",
    "Kore":     "Clara, expresiva, femenina",
    "Puck":     "Energética, juvenil, masculina",
    "Leda":     "Cálida, cercana, femenina",
    "Orus":     "Seria, profesional, masculina",
}

GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_API_BASE  = "https://generativelanguage.googleapis.com/v1beta/models"


def _build_wav_header(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bits: int = 16) -> bytes:
    """Construye cabecera WAV válida para datos PCM raw de Gemini."""
    data_size   = len(pcm_data)
    header_size = 44
    file_size   = data_size + header_size - 8

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        file_size,
        b"WAVE",
        b"fmt ",
        16,           # chunk size
        1,            # PCM format
        channels,
        sample_rate,
        sample_rate * channels * (bits // 8),  # byte rate
        channels * (bits // 8),                # block align
        bits,
        b"data",
        data_size,
    )
    return header


def synthesize_gemini(
    text: str,
    output_wav: str,
    voice: str = "Aoede",
    api_key: Optional[str] = None,
    sample_rate: int = 24000,
) -> bool:
    """
    Sintetiza texto a audio WAV usando la API TTS de Google Gemini.

    Args:
        text:        Texto a sintetizar (máximo ~5000 chars por llamada).
        output_wav:  Ruta de destino del archivo .wav resultante.
        voice:       Nombre de la voz Gemini (ver GEMINI_VOICES).
        api_key:     Clave de API de Google AI Studio. Si es None, intenta
                     leer GEMINI_API_KEY del entorno.
        sample_rate: Frecuencia de muestreo del audio (Gemini usa 24000 Hz).

    Returns:
        True si el archivo WAV fue generado exitosamente, False en caso de error.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return False

    if voice not in GEMINI_VOICES:
        voice = "Aoede"

    # Sanitizar texto: eliminar caracteres problemáticos para la API
    clean_text = text.strip()[:5000]
    if not clean_text:
        return False

    url = f"{GEMINI_API_BASE}/{GEMINI_TTS_MODEL}:generateContent?key={key}"

    payload = {
        "contents": [
            {
                "parts": [{"text": clean_text}]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice
                    }
                }
            }
        }
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent":   "GravityAI/12.1",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # Extraer audio base64 de la respuesta
        parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        audio_b64 = None
        for part in parts:
            inline = part.get("inlineData", {})
            if inline.get("mimeType", "").startswith("audio"):
                audio_b64 = inline.get("data")
                break

        if not audio_b64:
            return False

        pcm_data = base64.b64decode(audio_b64)
        wav_data = _build_wav_header(pcm_data, sample_rate=sample_rate) + pcm_data

        os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
        with open(output_wav, "wb") as f:
            f.write(wav_data)

        return os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Gemini TTS HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"Gemini TTS error: {e}")


def list_voices() -> dict[str, str]:
    """Retorna el catálogo de voces Gemini disponibles."""
    return dict(GEMINI_VOICES)


def get_api_key_from_gravity() -> Optional[str]:
    """
    Intenta recuperar la clave de API de Google desde el KeyManager de Gravity.
    Retorna None si no está configurada.
    """
    try:
        import sys
        import os
        gravity_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if gravity_root not in sys.path:
            sys.path.insert(0, gravity_root)
        from core.key_manager import KeyManager
        key = KeyManager.get_key("google")
        return key if key else None
    except Exception:
        return None
