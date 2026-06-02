import sys
import os
import math

sys.path.append('f:/Gravity_AI_bridge')
from core.video.procedural_generator import generate_procedural_video

def main():
    input_audio = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    out_video = os.path.join(out_dir, "Horizonte_de_Eventos_V5_Math_Music_Video.mp4")
    
    try:
        import librosa
        duration = librosa.get_duration(path=input_audio)
        duration_sec = math.ceil(duration)
    except Exception as e:
        print("Error calculando duracion, asumiendo 230 segundos:", e)
        duration_sec = 230
    
    print(f"==================================================")
    print(f"🎬 INICIANDO RENDERIZADO DEL VIDEOCLIP COMPLETO 🎬")
    print(f"==================================================")
    print(f"Audio: {input_audio}")
    print(f"Duración: {duration_sec} segundos (aprox {duration_sec * 24} cuadros)")
    print(f"Motor: V5 Audio-Reactivo (Modo: Odisea Espacial)")
    print(f"Output: {out_video}")
    print(f"==================================================")
    
    prompt = "event horizon space galaxy black hole universe"
    
    try:
        generate_procedural_video(
            prompt=prompt,
            seed=1984,
            w=1280,
            h=720,
            duration_sec=duration_sec,
            fps=24,
            out_mp4=out_video,
            audio_path=input_audio
        )
        print("\n✅ VIDEOCLIP RENDERIZADO COMPLETAMENTE!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ ERROR FATAL DURANTE EL RENDERIZADO: {e}")

if __name__ == '__main__':
    # Necesario en Windows para multiprocessing spawn
    import multiprocessing
    multiprocessing.freeze_support()
    main()
