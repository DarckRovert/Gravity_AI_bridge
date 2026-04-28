"""
Patch 4: _current_job fallback
"""
PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Fallback patch using index
idx = content.find('_current_job = {"id": job_id')
if idx != -1:
    end_idx = content.find('}', idx) + 1
    old_str = content[idx:end_idx]
    
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
    
    content = content[:idx] + new_init + content[end_idx:]
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] _current_job patched via fallback")
else:
    print("[WARN] _current_job NOT found")

import py_compile
try:
    py_compile.compile(PATH, doraise=True)
    print("[SYNTAX OK]")
except Exception as e:
    print(f"[SYNTAX ERROR] {e}")
