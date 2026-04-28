"""
Patch 2 preciso: extrae y reemplaza usando índices de byte exactos
"""
PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8", errors="replace")

# ── Mostrar el bloque de _current_job init ─────────────────────────────────
idx = content.find("_current_job = {")
if idx != -1:
    print(f"=== _current_job = {{ at offset {idx} ===")
    print(repr(content[idx:idx+300]))
    print()

# ── Mostrar el bloque de return en get_queue_status ────────────────────────
idx2 = content.find('"pending_count"')
if idx2 != -1:
    print(f"=== return block at offset {idx2} ===")
    print(repr(content[idx2-20:idx2+400]))
    print()

# ── Mostrar clip_paths.append ──────────────────────────────────────────────
idx3 = content.find("clip_paths.append(clip_path)")
if idx3 != -1:
    print(f"=== clip_paths.append at offset {idx3} ===")
    print(repr(content[idx3:idx3+200]))
