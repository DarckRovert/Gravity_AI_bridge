import os
import sys

sys.path.append('f:/Gravity_AI_bridge')
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline, generate_color_sequence
from core.video.glsl_renderer_v8 import render_v8_video

def main():
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V8_MAESTRIA.mp4")
    
    fps = 24
    w, h = 1280, 720 # Resolución mantenida en HD para sostener el cálculo de Normales (Mandelbulb)
    
    print("=========================================================")
    print("💎 INICIANDO MOTOR V8: MAESTRÍA VISUAL (PBR & CROSSFADE) 💎")
    print("=========================================================")
    
    print("1. Extrayendo acústica Estéreo y Multi-Banda...")
    multiband = extract_multiband_energy(input_audio, fps)
    total_frames = len(multiband['bass'])
    
    if total_frames == 0:
        print("Error al procesar el audio V8.")
        return
        
    duration_sec = total_frames / fps
    print(f"   -> Duración: {duration_sec:.1f}s ({total_frames} cuadros)")
    
    print("\n2. Director IA asignando Shaders y Transiciones...")
    timeline = generate_timeline(multiband, fps)
    for i, scene in enumerate(timeline):
        s_time = scene["start"] / fps
        e_time = scene["end"] / fps
        print(f"   [Secuencia {i+1}] {s_time:.1f}s - {e_time:.1f}s : {scene['engine'].upper()}")
        
    print("\n3. Calculando Paletas de Color Dinámicas (Color Grading)...")
    colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)
    
    print("\n4. Lanzando GPU Multi-Pass...")
    try:
        render_v8_video(
            timeline=timeline,
            multiband=multiband,
            colorsA=colorsA,
            colorsB=colorsB,
            w=w,
            h=h,
            fps=fps,
            out_mp4=out_video,
            audio_path=input_audio
        )
        print("\n✅ VIDEOCLIP V8 MAESTRÍA GENERADO EXITOSAMENTE!")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL RENDERIZADO V8: {e}")

if __name__ == '__main__':
    main()
