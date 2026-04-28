import re

PATH = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# 1. Mapa de Emociones a Filtros FFmpeg
MOOD_FILTERS = """
# -- Mapeo de Emociones a Color Grading Dinámico ------------------------------
EMOTIONAL_GRADES: dict[str, str] = {
    "neutral":   "eq=contrast=1.0:brightness=0.0:saturation=1.0",
    "tension":   "eq=contrast=1.3:brightness=-0.05:saturation=0.8:gamma=0.9,colorbalance=rs=0.1:gs=-0.05:bs=-0.1",
    "nostalgia": "eq=contrast=0.9:brightness=0.05:saturation=0.7:gamma=1.1,colorbalance=rs=0.1:gs=0.05:bs=-0.1",
    "euforia":   "eq=contrast=1.2:brightness=0.02:saturation=1.6:gamma=1.0,colorbalance=rs=0.05:gs=0.05:bs=0.1",
    "misterio":  "eq=contrast=1.4:brightness=-0.1:saturation=0.5:gamma=0.8,colorbalance=rs=-0.1:gs=-0.1:bs=0.2",
    "calidez":   "eq=contrast=1.1:brightness=0.03:saturation=1.3:gamma=1.05,colorbalance=rs=0.15:gs=0.05:bs=-0.1",
    "frio":      "eq=contrast=1.1:brightness=-0.02:saturation=0.9:gamma=0.95,colorbalance=rs=-0.2:gs=-0.1:bs=0.3",
    "accion":    "eq=contrast=1.3:brightness=0.0:saturation=1.4:gamma=0.9",
}
"""

# Insertar después de STYLE_COLOR_GRADES
if 'EMOTIONAL_GRADES' not in src:
    marker = 'STYLE_COLOR_GRADES: dict[str, str] ='
    idx = src.find('}', src.find(marker)) + 1
    src = src[:idx] + MOOD_FILTERS + src[idx:]

# 2. Actualizar el Prompt del LLM en _generate_script para pedir el mood
OLD_PROMPT = 'Devuelve un JSON con una lista de escenas. Cada escena debe tener: "title", "narration", "image_prompt".'
NEW_PROMPT = 'Devuelve un JSON con una lista de escenas. Cada escena debe tener: "title", "narration", "image_prompt", "mood" (elige uno entre: neutral, tension, nostalgia, euforia, misterio, calidez, frio, accion).'
src = src.replace(OLD_PROMPT, NEW_PROMPT, 1)

# 3. Aplicar el mood en _process_job
# Buscamos donde se calcula _cgrade y lo extendemos
OLD_CGRADE = "            _cgrade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')"
NEW_CGRADE = """            # Color Grading Emocional Combinado
            base_grade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')
            scene_mood = scene.get("mood", "neutral").lower()
            mood_grade = EMOTIONAL_GRADES.get(scene_mood, "")
            _cgrade    = f"{base_grade},{mood_grade}" if base_grade and mood_grade else (base_grade or mood_grade)"""

src = src.replace(OLD_CGRADE, NEW_CGRADE, 1)

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE: IA de Emociones implementada en el pipeline.")
