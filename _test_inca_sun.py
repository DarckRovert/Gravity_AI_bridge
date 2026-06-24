import os
import sys

# Asegurar que los imports de core. funcionen
sys.path.insert(0, r"f:\Gravity_AI_bridge")

from core.logger import log
import logging

# Aumentar verbosidad para ver progreso
log.setLevel(logging.INFO)

from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline, generate_color_sequence
from core.video.v13_ai_director import analyze_lyrics_sections
from core.video.glsl_renderer_v13 import render_v13_video
from core.video.subtitle_engine import generate_ass_subtitles


def main():
    audio_path = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Inca Sun.mp3"
    output_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(output_dir, exist_ok=True)

    fps = 24
    print("[1/5] Extrayendo energía multibanda del audio...")
    multiband = extract_multiband_energy(audio_path, fps)
    total_frames = len(multiband.get("bass", []))

    if total_frames == 0:
        print("Error: No se pudo extraer información del audio.")
        return

    print("[2/5] Generando timeline acústico base...")
    timeline = generate_timeline(multiband, fps)
    colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)

    lyrics = """
    [Sección 1]
    The ancient stones of Machu Picchu awake.
    Epic morning mist covering the andes.
    The golden sun rises over the ruins.

    [Sección 2]
    The spirit of the Inca empire breathes again.
    Warriors stand at the edge of the mountains.
    """

    print("[3/5] AI Director: Analizando contexto temático...")
    ai_result = analyze_lyrics_sections(lyrics, total_frames, fps)

    speed_mult_arr = None
    turb_mult_arr = None

    if ai_result and "colorsA" in ai_result:
        colorsA = ai_result["colorsA"]
        colorsB = ai_result["colorsB"]
        speed_mult_arr = ai_result["speed"]
        turb_mult_arr = ai_result["turbulence"]
        if "timeline" in ai_result and len(ai_result["timeline"]) > 0:
            timeline = ai_result["timeline"]

    # FORCE INCA MATH ENGINE
    for sc in timeline:
        sc["engine"] = "inca_math"

    bg_images_horiz = None
    bg_images_vert = None

    # Generar Subtítulos
    print("[3.5/5] Generando Subtítulos (Karaoke) con Whisper...")
    horiz_ass = os.path.join(output_dir, "test_inca_horiz.ass")
    vert_ass = os.path.join(output_dir, "test_inca_vert.ass")

    generate_ass_subtitles(
        audio_path, horiz_ass, tgt_w=1280, tgt_h=720, lyrics_text=lyrics
    )
    generate_ass_subtitles(
        audio_path, vert_ass, tgt_w=720, tgt_h=1280, lyrics_text=lyrics
    )

    out_horiz = os.path.join(output_dir, "Inca_Sun_Horizontal.mp4")
    print(f"Renderizando video: {out_horiz}")
    render_v13_video(
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
        background_images=bg_images_horiz,
        subtitle_file=horiz_ass,
    )

    # VERTICAL
    print("\n[5/5] === RENDER VERTICAL (720x1280) ===")
    print("Skiping AI for vertical format...")
    # bg_images_vert is already defined as [None]

    out_vert = os.path.join(output_dir, "Inca_Sun_Vertical.mp4")
    print(f"Renderizando video vertical: {out_vert}")
    render_v13_video(
        timeline=timeline,
        multiband=multiband,
        colorsA=colorsA,
        colorsB=colorsB,
        w=720,
        h=1280,
        fps=fps,
        out_mp4=out_vert,
        audio_path=audio_path,
        speed_multiplier=speed_mult_arr,
        turbulence=turb_mult_arr,
        background_images=bg_images_vert,
        subtitle_file=vert_ass,
    )

    print("\n=== PROCESO COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
