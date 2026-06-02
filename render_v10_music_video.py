import os
import sys

sys.path.append('f:/Gravity_AI_bridge')
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline, generate_color_sequence
from core.video.glsl_renderer_v10 import render_v10_video

def main():
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V10_LOGICA_PBR.mp4")
    
    fps = 24
    w, h = 1280, 720 # Resolución Cinematográfica HD
    
    print("=========================================================")
    print("🎬 INICIANDO MOTOR V10: DIRECTOR'S CUT (LÓGICA PBR) 🎬")
    print("=========================================================")
    
    print("1. Extrayendo Metadatos de Frecuencia Espacial...")
    multiband = extract_multiband_energy(input_audio, fps)
    total_frames = len(multiband['bass'])
    
    if total_frames == 0:
        print("Error al procesar el audio V10.")
        return
        
    duration_sec = total_frames / fps
    print(f"   -> Longitud: {duration_sec:.1f}s ({total_frames} cuadros)")
    
    print("\n2. Secuenciando Narrativa Kinemática...")
    timeline = generate_timeline(multiband, fps)
    for i, scene in enumerate(timeline):
        s_time = scene["start"] / fps
        e_time = scene["end"] / fps
        print(f"   [Acto {i+1}] {s_time:.1f}s - {e_time:.1f}s : {scene['engine'].upper()}")
        
    print("\n3. Calculando Grading de Temperatura...")
    colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)
    
    print("\n4. Generando Render Definitivo (Tracking Espacial + PBR V10)...")
    try:
        render_v10_video(
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
        print("\n✅ VIDEOCLIP V10 (DIRECTOR'S CUT) RENDERIZADO CON ÉXITO!")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL RENDERIZADO V10: {e}")

if __name__ == '__main__':
    main()
