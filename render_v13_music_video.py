import os
import sys

sys.path.append('f:/Gravity_AI_bridge')
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline, generate_color_sequence
from core.video.glsl_renderer_v13 import render_v13_video

def main():
    print("==================================================")
    print(" V13 ENGINE: BIOMECHANICS & PERFECT KINEMATICS    ")
    print("==================================================")
    
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V13_BIOMECHANICS.mp4")
    
    fps = 24
    width = 1280
    height = 720
    
    print("\n1. Analizando Audio...")
    multiband = extract_multiband_energy(input_audio, fps)
    total_frames = len(multiband['bass'])
    
    if total_frames == 0:
        print("Error al procesar el audio.")
        return
        
    print("\n2. Creando Línea de Tiempo...")
    timeline = generate_timeline(multiband, fps)
    
    print("\n3. Generando Paleta de Color (Espacio Profundo)...")
    colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)
            
    print("\n4. Iniciando Render V13 GPU (Shader Biomecánico)...")
    render_v13_video(
        timeline=timeline, 
        multiband=multiband, 
        colorsA=colorsA, 
        colorsB=colorsB, 
        w=width, 
        h=height, 
        fps=fps, 
        out_mp4=out_video, 
        audio_path=input_audio
    )
    print("\n✅ V13 FINALIZADO")

if __name__ == '__main__':
    main()
