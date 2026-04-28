import re

path = r"F:\Gravity_AI_bridge\api\routes\mixin_post.py"
with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# La linea corrupta contiene ambas: el cierre correcto y una linea extra duplicada
# Buscar el patron exacto
bad = (
    '                    "intro_card": intro_card,\r\n'
    '                 body = json.dumps({"ok": True, "job_id": job_id, "message": f"Video encolado (job #{job_id}). Estimado: ~{int(n_scenes * 4.5)} min.", "n_scenes": n_scenes, "style": style, "voice_id": voice_id or "auto", "fps": fps, "codec": codec, "ken_burns": ken_burns, "intro_card": intro_card}).encode())\r\n'
)

good = (
    '                    "intro_card": intro_card,\r\n'
    '                }).encode())\r\n'
)

if bad in content:
    content = content.replace(bad, good, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Linea corrupta corregida")
else:
    # Intento alternativo sin \r\n
    bad2 = bad.replace('\r\n', '\n')
    good2 = good.replace('\r\n', '\n')
    if bad2 in content:
        content = content.replace(bad2, good2, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Linea corrupta corregida (LF)")
    else:
        print("Patron no encontrado - buscando manualmente...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'body = json.dumps' in line and 'intro_card' in line and 'Video encolado' in line:
                print(f"Linea {i+1}: {repr(line[:80])}")
        # Mostrar rango de lineas 610-630
        for i, line in enumerate(lines[610:630], start=611):
            print(f"L{i}: {repr(line)}")
