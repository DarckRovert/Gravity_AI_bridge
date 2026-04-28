path = r"F:\Gravity_AI_bridge\api\routes\mixin_post.py"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

# La linea 625 (index 624) es la corrupta - reemplazarla con el cierre correcto
# La linea 624 (index 623) es: '                    "intro_card": intro_card,\n'
# La linea 625 (index 624) es la duplicada que debe ser '                }).encode())\n'

target_idx = 624  # 0-indexed (linea 625)
old_line = lines[target_idx]

if 'body = json.dumps' in old_line and 'Video encolado' in old_line:
    lines[target_idx] = '                }).encode())\n'
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Linea {target_idx+1} corregida:")
    print(f"  Antes: {repr(old_line[:60])}")
    print(f"  Despues: {repr(lines[target_idx])}")
else:
    print(f"Linea {target_idx+1} no es la esperada: {repr(old_line[:80])}")
    # Buscar la linea correcta
    for i, line in enumerate(lines):
        if 'body = json.dumps' in line and 'Video encolado' in line:
            print(f"Encontrada en linea {i+1}: {repr(line[:60])}")
