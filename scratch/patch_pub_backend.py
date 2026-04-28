"""
Patch 6: Agregar soporte para Publicidad a video_pipeline.py
"""
import re

PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "rb") as f:
    content = f.read().decode("utf-8", errors="replace")

# 1. Agregar a CINEMA_STYLES
# Buscar el final de retro80s
marker_retro = '''"retro80s": {
        "label":  "Retro 80s / Synth-wave",
        "prefix": "Synthwave retro 1980s aesthetic, neon pink and purple gradients, grid horizon, chrome lettering, vaporwave sunset, cinematic 16:9",
        "negative": "modern minimal, flat design, photography, low quality, blurry",
    },'''
# Intento regex por saltos de linea locos
pattern_retro = re.compile(r'"retro80s":\s*\{[^}]+\},')

# Insert pub
pub_style = '''
    "publicitario": {
        "label":  "Publicidad / Comercial",
        "prefix": "High-end commercial photography, ultra sharp, vivid studio lighting, 4k resolution, bright and energetic, modern product advertising, 16:9",
        "negative": "dark, gloomy, low quality, amateur, blurry, messy",
    },'''

# 2. Agregar a STYLE_COLOR_GRADES
pattern_scg = re.compile(r'"retro80s":\s*"[^"]+",')
pub_scg = '\n    "publicitario": "eq=contrast=1.15:brightness=0.05:saturation=1.2:gamma=1.05",'

# 3. Agregar a BGM_GENERATORS
pattern_bgm = re.compile(r'"jazz":\s*\([^)]+\),')
pub_bgm = '''
    "publicitario": (
        "0.25*sin(196*2*PI*t)+0.2*sin(246.94*2*PI*t)+"
        "0.15*sin(293.66*2*PI*t)+0.1*sin(392*2*PI*t)+"
        "0.05*sin(587.33*2*PI*t)"
    ),'''

# Apply replacements
def patch_pattern(content, pattern, extra_code):
    match = pattern.search(content)
    if match:
        original = match.group(0)
        return content[:match.end()] + extra_code + content[match.end():]
    return content

content = patch_pattern(content, pattern_retro, pub_style)
content = patch_pattern(content, pattern_scg, pub_scg)
content = patch_pattern(content, pattern_bgm, pub_bgm)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] video_pipeline.py parcheado para Publicidad")

import py_compile
try:
    py_compile.compile(PATH, doraise=True)
    print("[SYNTAX OK]")
except Exception as e:
    print(f"[SYNTAX ERROR] {e}")
