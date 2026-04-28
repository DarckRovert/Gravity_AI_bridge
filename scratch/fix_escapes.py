import re

path = r'F:\Gravity_AI_bridge\core\video_pipeline.py'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    src = f.read()

# Reemplazar las líneas con escape sequences inválidas en _create_title_card
src = re.sub(
    r"safe_title\s*=\s*title\.replace\(.*?\)\[:60\]",
    "safe_title    = re.sub(r\"[:'%]\", '', title)[:60]",
    src, count=1, flags=re.DOTALL
)
src = re.sub(
    r"safe_subtitle\s*=\s*subtitle\.replace\(.*?\)\[:80\]",
    "safe_subtitle = re.sub(r\"[:'%]\", '', subtitle)[:80]",
    src, count=1, flags=re.DOTALL
)

# Asegurarse de que re está importado (ya está al inicio del archivo normalmente)
if "import re" not in src[:500]:
    src = "import re\n" + src

with open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK: escapes corregidos con re.sub")
