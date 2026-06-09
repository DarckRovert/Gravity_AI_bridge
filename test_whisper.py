import sys
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# Add core to path
sys.path.append(r"f:\Gravity_AI_bridge")

from core.video.subtitle_engine import generate_ass_subtitles

audio_path = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Inca Sun.mp3"
lyrics = """
[Intro]
Fuego
"""

try:
    print("Iniciando prueba de Whisper (descargara el modelo medium si no existe)...")
    generate_ass_subtitles(audio_path, "test_subs.ass", lyrics_text=lyrics)
    print("Prueba completada con exito.")
except Exception as e:
    print("CRASH EN WHISPER:", e)
    import traceback
    traceback.print_exc()
