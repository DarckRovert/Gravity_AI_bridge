import os
import sys

sys.path.append('f:/Gravity_AI_bridge')
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline
from core.video.glsl_renderer_v7 import render_v7_video
from core.video.procedural_generator import _get_palette

def main():
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V7_NEXTGEN.mp4")
    
    fps = 24
    # Para la demoscene usaremos 1920x1080 si lo soporta el GPU, probemos 1280x720 para garantizar framerate
    w, h = 1280, 720
    
    print("=========================================================")
    print("🔥 INICIANDO MOTOR V7 NEXT-GEN (RAYMARCHING VOLUMÉTRICO) 🔥")
    print("=========================================================")
    print("1. Extrayendo acústica Estéreo y Multi-Banda (Oído 3D)...")
    
    # Esto ahora devuelve 'pan' también
    multiband = extract_multiband_energy(input_audio, fps)
    total_frames = len(multiband['bass'])
    
    if total_frames == 0:
        print("Error al procesar el audio V7.")
        return
        
    duration_sec = total_frames / fps
    print(f"   -> Duración: {duration_sec:.1f}s ({total_frames} cuadros)")
    
    print("\n2. Director IA asignando Shaders Volumétricos a la pista...")
    timeline = generate_timeline(multiband, fps)
    for i, scene in enumerate(timeline):
        s_time = scene["start"] / fps
        e_time = scene["end"] / fps
        print(f"   [Secuencia {i+1}] {s_time:.1f}s - {e_time:.1f}s : {scene['engine'].upper()}")
        
    print("\n3. Lanzando GPU Multi-Pass (Geometría -> Post-Procesado)...")
    
    # Paleta oscura, cyber, cinematográfica
    palette = _get_palette("cyber neon dark red city epic")
    
    try:
        render_v7_video(
            timeline=timeline,
            multiband=multiband,
            w=w,
            h=h,
            fps=fps,
            out_mp4=out_video,
            audio_path=input_audio,
            palette=palette
        )
        print("\n✅ VIDEOCLIP V7 NEXT-GEN GENERADO EXITOSAMENTE!")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL RENDERIZADO V7: {e}")

if __name__ == '__main__':
    main()
