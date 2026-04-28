"""
Patch 7: Agregar BGM publicitario
"""
import re

PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "rb") as f:
    content = f.read().decode("utf-8", errors="replace")

# The string to append
pub_bgm = '''
    "publicitario": (
        "0.25*sin(196*2*PI*t)+0.2*sin(246.94*2*PI*t)+"
        "0.15*sin(293.66*2*PI*t)+0.1*sin(392*2*PI*t)+"
        "0.05*sin(587.33*2*PI*t)"
    ),
}'''

# Find the end of BGM_GENERATORS
# It ends with:
# "0.07*sin(392*2*PI*t)+0.05*sin(466.16*2*PI*t)"
#     ),
# }

target = '"0.07*sin(392*2*PI*t)+0.05*sin(466.16*2*PI*t)"'
parts = content.split(target)

if len(parts) == 2:
    # replace the closing brace of the dictionary
    end_part = parts[1]
    # find the first '}'
    brace_idx = end_part.find('}')
    if brace_idx != -1:
        new_end = end_part[:brace_idx] + pub_bgm + end_part[brace_idx+1:]
        content = parts[0] + target + new_end
        with open(PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("[OK] BGM parcheado correctamente")
    else:
        print("ERROR: No se encontro la llave }")
else:
    print("ERROR: Target not found or found multiple times.")

