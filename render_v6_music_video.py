import os
import sys
import math

sys.path.append('f:/Gravity_AI_bridge')
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline
from core.video.glsl_renderer import render_v6_video
from core.video.procedural_generator import _get_palette

def main():
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V6_MASTERPIECE.mp4")
    
    fps = 24
    w, h = 1280, 720
    
    print("==================================================")
    print("🚀 INICIANDO RENDERIZADO V6 GPU (GRADO INDUSTRIAL) 🚀")
    print("==================================================")
    print("1. Extrayendo curvas espectrales Multi-Banda...")
    multiband = extract_multiband_energy(input_audio, fps)
    total_frames = len(multiband['bass'])
    
    if total_frames == 0:
        print("Error al procesar el audio.")
        return
        
    duration_sec = total_frames / fps
    print(f"   -> Duración: {duration_sec:.1f}s ({total_frames} cuadros)")
    
    print("\n2. Director IA analizando la estructura de la canción...")
    timeline = generate_timeline(multiband, fps)
    for i, scene in enumerate(timeline):
        s_time = scene["start"] / fps
        e_time = scene["end"] / fps
        print(f"   [Escena {i+1}] {s_time:.1f}s - {e_time:.1f}s : Motor {scene['engine'].upper()}")
        
    print("\n3. Lanzando GPU GLSL Shaders en tiempo real...")
    
    # Elegimos una paleta épica (synthwave gold/cyber)
    palette = _get_palette("cyber gold epic neon city space")
    
    try:
        render_v6_video(
            timeline=timeline,
            multiband=multiband,
            w=w,
            h=h,
            fps=fps,
            out_mp4=out_video,
            audio_path=input_audio,
            palette=palette
        )
        print("\n✅ VIDEOCLIP V6 MASTERPIECE GENERADO EXITOSAMENTE!")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL RENDERIZADO GPU: {e}")

if __name__ == '__main__':
    main()
