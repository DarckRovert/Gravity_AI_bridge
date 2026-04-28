"""
audit_pipeline.py - Auditoría completa del estado de video_pipeline.py
"""
import ast, sys
sys.stdout.reconfigure(encoding='utf-8')

TARGET = r"F:\Gravity_AI_bridge\core\video_pipeline.py"
with open(TARGET, "rb") as f:
    raw = f.read()

src = raw.replace(b'\r\r\r\n', b'\n').replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n').replace(b'\r', b'\n')
real_lines = src.split(b'\n')
print(f"Bytes: {len(raw)}")
print(f"Lineas normalizadas: {len(real_lines)}")

checks = [
    ("BUG-1 s=44100 ELIMINADO",         b':c=stereo:s=44100:d=' not in raw),
    ("BUG-2 r=44100 ELIMINADO",         b':c=stereo:r=44100' not in raw),
    ("BUG-3 bgm_side ELIMINADO",        b'[bgm_side]' not in raw),
    ("FIX sample_rate=44100",           b'sample_rate=44100' in raw),
    ("FIX anullsrc presente",           b'anullsrc=channel_layout=stereo' in raw),
    ("FIX [narr][1:a]sidechain",        b'[narr][1:a]sidechaincompress' in raw),
    ("_assemble_clip completa",         b'fade=t=out:st=' in raw),
    ("_create_title_card completa",     b'Intro card generada' in raw),
    ("_extract_thumbnail presente",     b'_extract_thumbnail' in raw),
    ("_ensure_bgm abspath fix",         b'abspath(bgm_path)' in raw),
    ("bgm_publicitario en BGM_GENERATORS", b'"publicitario"' in raw),
    ("estilo publicitario en CINEMA_STYLES", b'Publicidad / Comercial' in raw),
]

# Syntax check
syntax_ok = True
try:
    ast.parse(src)
except SyntaxError as e:
    syntax_ok = False
    print(f"  SYNTAX ERROR linea {e.lineno}: {e.msg}")
checks.append(("SYNTAX OK", syntax_ok))

all_ok = all(r for _, r in checks)
for name, ok in checks:
    tag = "OK  " if ok else "FAIL"
    print(f"  [{tag}] {name}")

print()
print("ESTADO GLOBAL:", "CORRECTO" if all_ok else "HAY PROBLEMAS")
print()

# Localizar funciones clave
fns = [
    b"def _ensure_bgm",
    b"def _concatenate_clips",
    b"def _assemble_clip",
    b"def _create_title_card",
    b"def _extract_thumbnail",
    b"def _process_job",
    b"def _worker_loop",
    b"def start(",
]
print("Funciones detectadas (linea normalizada):")
for fn in fns:
    idx = src.find(fn)
    if idx >= 0:
        lineno = src[:idx].count(b'\n') + 1
        print(f"  {fn.decode():<35} -> linea {lineno}")
    else:
        print(f"  {fn.decode():<35} -> NO ENCONTRADA")

print()
# Mostrar el filter_complex actual
fc_idx = src.find(b"anullsrc=channel_layout=stereo")
if fc_idx >= 0:
    snippet = src[max(0,fc_idx-20):fc_idx+200]
    print("filter_complex BGM actual:")
    for l in snippet.split(b'\n'):
        if l.strip():
            print(" ", l.decode('utf-8', errors='replace'))
