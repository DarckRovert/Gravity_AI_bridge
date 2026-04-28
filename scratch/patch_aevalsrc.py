"""
patch_aevalsrc.py — Parche quirúrgico para video_pipeline.py
Corrige 3 bugs críticos en la generación y mezcla de BGM con ffmpeg 62+:

  BUG-1: _ensure_bgm usa aevalsrc con s= (deprecado → Error ffmpeg 62+)
         FIX: reemplazar por sample_rate=

  BUG-2: _concatenate_clips usa aevalsrc con r= (inválido → "Option not found")
         FIX: reemplazar por anullsrc con channel_layout=stereo:sample_rate=44100

  BUG-3: asplit innecesario produce stream [bgm_side] sin consumir
         FIX: eliminar el asplit, pasar [1:a] directamente al sidechaincompress

Opera a nivel de bytes para evitar corrupción por líneas \\r\\r\\r\\n.
"""

import re

TARGET = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(TARGET, "rb") as f:
    raw = f.read()

original_size = len(raw)

# ── BUG-1: _ensure_bgm — s=44100 → sample_rate=44100 ─────────────────────────
# Patrón: aevalsrc=EXPR:c=stereo:s=44100:d=
old1 = b":c=stereo:s=44100:d="
new1 = b":c=stereo:sample_rate=44100:d="
count1 = raw.count(old1)
raw = raw.replace(old1, new1)
print(f"[BUG-1] Reemplazos de ':c=stereo:s=44100:d=': {count1}")

# ── BUG-2 + BUG-3: filter_complex concat con aevalsrc+asplit ─────────────────
# Buscar el bloque de filter_str completo (puede tener \r\n o \r\r\r\n entre líneas)
# Usamos el texto más único posible para localizar con exactitud.
old2 = (
    b"aevalsrc=0:c=stereo:r=44100:d=0.001[silence];"
)
new2 = (
    b"anullsrc=channel_layout=stereo:sample_rate=44100[silence];"
)
count2 = raw.count(old2)
raw = raw.replace(old2, new2)
print(f"[BUG-2] Reemplazos de aevalsrc→anullsrc en filter_complex: {count2}")

# BUG-3: eliminar el asplit innecesario y reencadenar correctamente
# Línea original:   f"[1:a]asplit[bgm_orig][bgm_side];"
# + siguiente:      f"[bgm_orig][narr]sidechaincompress..."
# → reemplazar por: f"[narr][1:a]sidechaincompress..."
old3 = b"[1:a]asplit[bgm_orig][bgm_side];"
# El siguiente segmento que consume bgm_orig
old3b = b"[bgm_orig][narr]sidechaincompress"
new3b = b"[narr][1:a]sidechaincompress"

# Primero eliminar la línea del asplit (reemplazar con vacío preservando el separador)
# Detectamos el separador exacto que usa ffmpeg filter_complex
# La cadena en el archivo es una f-string con concatenación:
#   f"[1:a]asplit[bgm_orig][bgm_side];\"\n"
# En bytes puede tener cualquier combo de \r\n
# Estrategia: eliminar la ocurrencia exacta incluyendo el separador de línea virtual

count3 = raw.count(old3)
if count3 > 0:
    # Eliminar el segmento "[1:a]asplit[bgm_orig][bgm_side];" de la f-string
    # En el archivo está rodeado de comillas de f-string y concatenación
    # Basta con eliminarlo + reemplazar bgm_orig→[1:a] en sidechaincompress
    raw = raw.replace(old3, b"")
    print(f"[BUG-3a] Eliminaciones de asplit: {count3}")
else:
    print("[BUG-3a] No se encontró asplit (ya corregido o patrón distinto)")

count3b = raw.count(old3b)
if count3b > 0:
    raw = raw.replace(old3b, new3b)
    print(f"[BUG-3b] Reemplazos bgm_orig→[1:a] en sidechaincompress: {count3b}")
else:
    print("[BUG-3b] No se encontró [bgm_orig][narr]sidechaincompress")

# ── Verificación final ────────────────────────────────────────────────────────
if b"aevalsrc=0:c=stereo:r=" in raw:
    print("[ERROR] Aún quedan instancias de r= en aevalsrc — parche incompleto")
else:
    print("[OK] No quedan instancias de r= en aevalsrc")

if b":c=stereo:s=44100" in raw:
    print("[ERROR] Aún quedan instancias de s= en aevalsrc — parche incompleto")
else:
    print("[OK] No quedan instancias de s= en aevalsrc")

if b"[bgm_side]" in raw:
    print("[WARN] Aún existe [bgm_side] en el archivo (revisar manualmente)")
else:
    print("[OK] [bgm_side] eliminado correctamente")

# ── Escribir resultado ────────────────────────────────────────────────────────
with open(TARGET, "wb") as f:
    f.write(raw)

print(f"\nParche aplicado. Tamaño original: {original_size} bytes | Nuevo: {len(raw)} bytes")
print("Listo. Reinicia el servidor Gravity para que tome efecto.")
