import os
import sys

sys.path.insert(0, r"f:\Gravity_AI_bridge")

from core.logger import log
import logging

log.setLevel(logging.INFO)

from core.video.audio_analyzer import extract_multiband_energy  # noqa: E402
from core.video.timeline_director import generate_timeline, generate_color_sequence  # noqa: E402
from core.video.v13_ai_director import analyze_lyrics_sections  # noqa: E402
from core.video.glsl_compute_renderer_v14 import render_v14_compute_video  # noqa: E402
from core.video.subtitle_engine import generate_ass_subtitles  # noqa: E402


def main():
    audio_path = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Frecuencias Fantasma.wav"
    output_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(output_dir, exist_ok=True)

    fps = 24
    print("[1/4] Extrayendo energía multibanda del audio...")
    multiband = extract_multiband_energy(audio_path, fps)
    total_frames = len(multiband.get("bass", []))

    print("[2/4] Generando timeline acústico base...")
    timeline = generate_timeline(multiband, fps)
    colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)

    print("[2.5/4] Generando Subtítulos (Karaoke) y Extrayendo Letras con Whisper...")
    horiz_ass = os.path.join(output_dir, "test_peru_horiz.ass")
    # Genera subtítulos y recupera el texto real
    _, real_lyrics = generate_ass_subtitles(
        audio_path, horiz_ass, tgt_w=1280, tgt_h=720, lyrics_text=None
    )

    print("[3/4] AI Director: Analizando contexto temático de las letras extraídas...")
    print(f"      -> Letras detectadas: {real_lyrics[:100]}...")
    ai_result = analyze_lyrics_sections(real_lyrics, total_frames, fps)

    speed_mult_arr = None
    turb_mult_arr = None

    if ai_result and "colorsA" in ai_result:
        colorsA = ai_result["colorsA"]
        colorsB = ai_result["colorsB"]
        speed_mult_arr = ai_result["speed"]
        turb_mult_arr = ai_result["turbulence"]
        if "timeline" in ai_result and len(ai_result["timeline"]) > 0:
            timeline = ai_result["timeline"]

    # AI DIRECTOR TOMA EL CONTROL AHORA. Se remueve la regla de forzar inca_math para todas las escenas.
    # Los motores (space_odyssey, neon_fluid, inca_math, etc) se transicionarán dinámicamente según la letra.

    out_horiz = os.path.join(output_dir, "Frecuencias_Fantasma_V4.mp4")
    print(f"Renderizando video V14 (Compute Shaders): {out_horiz}")
    render_v14_compute_video(
        timeline=timeline,
        multiband=multiband,
        colorsA=colorsA,
        colorsB=colorsB,
        w=1280,
        h=720,
        fps=fps,
        out_mp4=out_horiz,
        audio_path=audio_path,
        speed_multiplier=speed_mult_arr,
        turbulence=turb_mult_arr,
        background_images=None,
        subtitle_file=horiz_ass,
    )

    print("\n=== PROCESO COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
