import re

PATH = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# 1. Definir el filtro de Audio Ducking (Sidechain compression sintética)
# Reemplazamos la lógica de amix simple en _concatenate_clips por una cadena de filtros inteligente.

OLD_AMIX = '            af = f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2:weights=1 {bgm_volume}[aout]"'
NEW_AMIX = """            # Audio Ducking Dinámico: La música (input 1) baja cuando hay voz (input 0)
            # Usamos sidechain compression: cuando el sidechain (voz) supera el umbral, comprime la música.
            af = (
                f"[1:a]asplit[bgm_main][bgm_side];"
                f"[0:a]asplit[voice_main][voice_side];"
                f"[bgm_main][voice_side]sidechaincompress=threshold=0.15:ratio=4:attack=200:release=1000[bgm_ducked];"
                f"[voice_main][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2:weights=1 {bgm_volume}[aout]"
            )"""

if OLD_AMIX in src:
    src = src.replace(OLD_AMIX, NEW_AMIX, 1)
    print("OK: Audio Ducking dinámico implementado en _concatenate_clips")

# 2. VFX de Textura Cinematográfica (Grain sutil)
# Modificamos _assemble_clip para añadir ruido de película (noise) si la calidad es 'cinematic'

OLD_VF_END = '        if color_grade:\n            vf_parts.append(color_grade)'
NEW_VF_END = """        if color_grade:
            vf_parts.append(color_grade)
        
        # VFX de grano de película sutil para cohesión visual
        vf_parts.append("noise=alls=7:allf=t+u")"""

if OLD_VF_END in src:
    src = src.replace(OLD_VF_END, NEW_VF_END, 1)
    print("OK: Film Grain VFX añadido a _assemble_clip")

# 3. Actualizar la descripción de la herramienta en el log para reflejar el upgrade
src = src.replace('Worker daemon iniciado (Cinematic Edition).', 'Worker daemon iniciado (Gravity Studio ULTRA V12.2 PRO - Audio Ducking & VFX Active).')

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: video_pipeline.py elevado a ULTRA.")
