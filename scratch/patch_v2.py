"""
Patch: Fix _current_job keys + add stats to get_queue_status()
"""
import os, re

PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "rb") as f:
    content = f.read().decode("utf-8", errors="replace")

# ── Fix 1: _current_job usa 'step' pero el frontend espera 'current_step'
# Reemplazar la inicializacion de _current_job en _process_job
old_init = '''with _lock:
        _current_job = {"id": job_id, "topic": topic, "progress": 0,
                        "step": "Generando guión..."}'''

new_init = '''with _lock:
        _current_job = {
            "id":            job_id,
            "topic":         topic,
            "title":         title or topic[:60],
            "style":         style,
            "total_scenes":  n_scenes,
            "current_scene": 0,
            "scenes_done":   [],
            "current_step":  "Generando guión con el LLM...",
            "progress":      0,
        }'''

if old_init in content:
    content = content.replace(old_init, new_init, 1)
    print("[OK] _current_job init fixed")
else:
    print("[WARN] _current_job init not found - searching...")
    idx = content.find('"step": "Generando guión...')
    print(f"  'step' key at byte: {idx}")
    if idx != -1:
        # Show context
        print(repr(content[idx-200:idx+80]))

# ── Fix 2: Actualizar current_scene en cada iteracion de escena
# Buscar el patron de actualizacion por escena (imagen step)
old_img_update = '''"step": f"Escena {scene_num}/{n_scenes}: imagen..."'''
new_img_update = '''"current_step": f"[{scene_num}/{n_scenes}] Generando imagen...",
                    "current_scene": scene_num,
                    "progress":      pct,'''

if old_img_update in content:
    # Reemplazar todas las ocurrencias de 'step' en _current_job updates
    content = content.replace(
        '"step":     f"Escena {scene_num}/{n_scenes}: imagen..."',
        '"current_step": f"[{scene_num}/{n_scenes}] Generando imagen...", "current_scene": scene_num,'
    )
    content = content.replace(
        '"step":     f"Escena {scene_num}/{n_scenes}: audio..."',
        '"current_step": f"[{scene_num}/{n_scenes}] Generando audio...", "current_scene": scene_num,'
    )
    content = content.replace(
        '"step":     f"Escena {scene_num}/{n_scenes}: clip..."',
        '"current_step": f"[{scene_num}/{n_scenes}] Ensamblando clip...", "current_scene": scene_num,'
    )
    print("[OK] per-scene step keys fixed")
else:
    # Generic replace all remaining 'step' keys in _current_job updates
    count = content.count('"step":')
    print(f"[INFO] Found {count} 'step' key(s) - replacing with 'current_step'")
    content = content.replace('"step":', '"current_step":')
    print("[OK] all 'step' -> 'current_step' replaced")

# ── Fix 3: Agregar 'scenes_done' append al completar cada clip
old_clip_append = '''clip_paths.append(clip_path)
            else:
                raise RuntimeError(f"Error al ensamblar el clip de la escena {scene_num}.")'''

new_clip_append = '''clip_paths.append(clip_path)
                with _lock:
                    if _current_job and scene_num not in _current_job.get("scenes_done", []):
                        _current_job.setdefault("scenes_done", []).append(scene_num)
            else:
                raise RuntimeError(f"Error al ensamblar el clip de la escena {scene_num}.")'''

if old_clip_append in content:
    content = content.replace(old_clip_append, new_clip_append, 1)
    print("[OK] scenes_done tracking added")
else:
    print("[WARN] clip_paths.append pattern not found")

# ── Fix 4: Add stats to get_queue_status() return value
old_return = '''    return {
        "pending_count": len(pending),
        "pending_jobs":  pending,
        "current_job":   current,
        "history":       history,
        "ffmpeg_ok":     os.path.isfile(FFMPEG_EXE),
        "styles":        {k: v["label"] for k, v in CINEMA_STYLES.items()},
    }'''

new_return = '''    # Aggregate stats from DB (all-time)
    try:
        _sc = sqlite3.connect(DB_PATH)
        _row = _sc.execute(
            "SELECT COUNT(*) total, "
            "SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) completed, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) failed, "
            "SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) cancelled, "
            "SUM(CASE WHEN status='deleted' THEN 1 ELSE 0 END) deleted "
            "FROM video_jobs"
        ).fetchone()
        _styles_raw = _sc.execute(
            "SELECT style, COUNT(*) cnt FROM video_jobs WHERE status='done' GROUP BY style ORDER BY cnt DESC"
        ).fetchall()
        _sc.close()
        _agg = {
            "total": _row[0] or 0, "completed": _row[1] or 0,
            "failed": _row[2] or 0, "cancelled": _row[3] or 0, "deleted": _row[4] or 0,
        }
        _styles_dist = {r[0]: r[1] for r in _styles_raw}
    except Exception:
        _agg = {"total": 0, "completed": 0, "failed": 0, "cancelled": 0, "deleted": 0}
        _styles_dist = {}

    return {
        "pending_count": len(pending),
        "pending_jobs":  pending,
        "current_job":   current,
        "history":       history,
        "ffmpeg_ok":     os.path.isfile(FFMPEG_EXE),
        "styles":        {k: v["label"] for k, v in CINEMA_STYLES.items()},
        "aggregate":     _agg,
        "styles_dist":   _styles_dist,
    }'''

if old_return in content:
    content = content.replace(old_return, new_return, 1)
    print("[OK] stats aggregate added to get_queue_status()")
else:
    print("[WARN] return block not found exactly")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("\n[DONE] video_pipeline.py patched.")

import py_compile
try:
    py_compile.compile(PATH, doraise=True)
    print("[SYNTAX OK]")
except py_compile.PyCompileError as e:
    print(f"[SYNTAX ERROR] {e}")
