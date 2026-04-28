"""
Patch 3: Handle \r\r\r\n and patch exactly
"""
PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "rb") as f:
    content = f.read().decode("utf-8", errors="replace")

# Replace all \r\n, \r\r\n, \r\r\r\n with \n to standardize for processing
import re
normalized_content = re.sub(r'\r+\n', '\n', content)

# Patch 1: _current_job init
old_init = '''_current_job = {"id": job_id, "topic": topic, "progress": 0,
                        "current_step": "Generando guión..."}'''

new_init = '''_current_job = {
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

if old_init in normalized_content:
    normalized_content = normalized_content.replace(old_init, new_init, 1)
    print("[OK] _current_job init patched")
else:
    print("[WARN] _current_job init NOT patched")

# Patch 2: clip_paths.append
old_clip = '''clip_paths.append(clip_path)
            else:
                raise RuntimeError(f"Error al ensamblar el clip de la escena {scene_num}.")'''

new_clip = '''clip_paths.append(clip_path)
                with _lock:
                    if _current_job and scene_num not in _current_job.get("scenes_done", []):
                        _current_job.setdefault("scenes_done", []).append(scene_num)
            else:
                raise RuntimeError(f"Error al ensamblar el clip de la escena {scene_num}.")'''

if old_clip in normalized_content:
    normalized_content = normalized_content.replace(old_clip, new_clip, 1)
    print("[OK] clip_paths.append patched")
else:
    print("[WARN] clip_paths.append NOT patched")


# Patch 3: return block in get_queue_status
old_return = '''return {
        "pending_count": len(pending),
        "pending_jobs":  pending,
        "current_job":   current,
        "history":       history,
        "ffmpeg_ok":     os.path.isfile(FFMPEG_EXE),
        "styles":        {k: v["label"] for k, v in CINEMA_STYLES.items()},
    }'''

new_return = '''# Aggregate stats from DB (all-time)
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

if old_return in normalized_content:
    normalized_content = normalized_content.replace(old_return, new_return, 1)
    print("[OK] get_queue_status return patched")
else:
    print("[WARN] get_queue_status return NOT patched")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(normalized_content)

print("Patch complete. Verifying syntax...")
import py_compile
try:
    py_compile.compile(PATH, doraise=True)
    print("[SYNTAX OK]")
except Exception as e:
    print(f"[SYNTAX ERROR] {e}")
