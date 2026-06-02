import os
import sys
import subprocess
import shutil

# Inyectar Gravity en el PATH para acceder a sus módulos internos
sys.path.append('f:/Gravity_AI_bridge')

from core.video.audio_processor import _generate_audio, get_available_voices

# =========================================================
# CONFIGURACIÓN DEL DIRECTOR
# =========================================================
INCLUDE_VOICE = False  # Cambiar a True si quieres el Prólogo Narrado
USE_GEMINI_TTS = True # Si está en True, intentará usar gemini:alloy si hay una API Key, si no, usará SAPI
# =========================================================

def main():
    print("=========================================================")
    print("🎬 GRAVITY AI: CINEMATIC MIXER V13 (THEATRICAL RELEASE) 🎬")
    print(f"   VOZ NARRADA ACTIVA: {INCLUDE_VOICE}")
    print("=========================================================")
    
    out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
    os.makedirs(out_dir, exist_ok=True)
    
    v13_video = os.path.join(out_dir, "Horizonte_de_Eventos_V13_BIOMECHANICS.mp4")
    final_video = os.path.join(out_dir, "Horizonte_de_Eventos_V13_THEATRICAL_CUT.mp4")
    
    if not os.path.isfile(v13_video):
        print(f"❌ No se encontró el video V13 en: {v13_video}")
        print("   Asegúrate de haber renderizado la V13 primero.")
        return
        
    if not INCLUDE_VOICE:
        print("\n[INFO] Narración desactivada. Copiando V13 como THEATRICAL CUT puro...")
        shutil.copyfile(v13_video, final_video)
        print(f"✅ THEATRICAL CUT (SIN VOZ) TERMINADO CON ÉXITO: {final_video}")
        return

    # Si INCLUDE_VOICE es True, continuamos con el pipeline de síntesis
    lines = [
        "En el abismo del espacio profundo, donde el tiempo se fractura y la luz muere... existe una singularidad.",
        "El Horizonte de Eventos.",
        "No hay modelos tridimensionales aquí. Solo luz, esculpida a través de la gravedad y ecuaciones puras.",
        "El Caminante ha despertado."
    ]
    
    print("[1] Configurando Motor TTS...")
    target_voice_id = ""
    
    if USE_GEMINI_TTS:
        print("    Solicitando Gemini TTS Premium (Alloy)...")
        target_voice_id = "gemini:alloy"
    else:
        print("    Buscando voces SAPI neuronales locales...")
        voices = get_available_voices()
        es_voices = [v for v in voices if v['lang'] == 'es']
        if es_voices:
            print(f"    Voz local seleccionada: {es_voices[0]['name']}")
            target_voice_id = es_voices[0]['id']
        
    print("\n[2] Sintetizando Guion (TTS)...")
    wav_files = []
    for i, text in enumerate(lines):
        wav_path = os.path.join(out_dir, f"line_{i}.wav")
        print(f"    Sintetizando línea {i+1}: '{text}'")
        success = _generate_audio(text, wav_path, rate=135, voice_id=target_voice_id)
        if not success:
            print(f"❌ Error al sintetizar la línea {i+1}. (Si usaste Gemini, verifica la API Key).")
            return
        wav_files.append(wav_path)
        
    print("\n[3] Acoplando líneas de voz en el tiempo (FFmpeg Delay)...")
    ffmpeg_exe = r"F:\Gravity_AI_bridge\_integrations\ffmpeg\ffmpeg.exe"
    if not os.path.isfile(ffmpeg_exe):
        ffmpeg_exe = "ffmpeg"
        
    voice_track = os.path.join(out_dir, "prologue_voice.wav")
    delays = [1000, 9000, 14000, 24000]
    
    inputs = []
    filter_complex = ""
    for i, wav in enumerate(wav_files):
        inputs.extend(["-i", wav])
        d = delays[i]
        filter_complex += f"[{i}:a]adelay={d}|{d}[a{i}];"
        
    mix_inputs = "".join([f"[a{i}]" for i in range(len(wav_files))])
    filter_complex += f"{mix_inputs}amix=inputs={len(wav_files)}:dropout_transition=0:normalize=0[aout]"
    
    cmd_merge_voice = [
        ffmpeg_exe, "-y"
    ] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-ac", "2", "-ar", "44100",
        voice_track
    ]
    
    subprocess.run(cmd_merge_voice, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("    Pista de voz ensamblada.")
    
    print("\n[4] Mezclando Música y Voz con el Videoclip V13...")
    
    cmd_final = [
        ffmpeg_exe, "-y",
        "-i", v13_video,
        "-i", voice_track,
        "-filter_complex", "[1:a]volume=1.8[v1];[0:a][v1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        final_video
    ]
    
    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for w in wav_files:
        try: os.remove(w)
        except: pass
    try: os.remove(voice_track)
    except: pass
    
    print(f"\n✅ THEATRICAL CUT (CON VOZ) TERMINADO CON ÉXITO!")
    print(f"   Salida: {final_video}")

if __name__ == '__main__':
    main()
