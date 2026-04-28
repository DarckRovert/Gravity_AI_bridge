"""
Patch 5: Reemplazar "step" por "current_step" en memoria
"""
PATH = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Reemplazar asignaciones en memoria a _current_job
content = content.replace(
    '_current_job["step"]     = f"Escena {scene_num}/{n_scenes}: imagen..."',
    '_current_job["current_step"] = f"[{scene_num}/{n_scenes}] Generando imagen..."\n                    _current_job["current_scene"] = scene_num'
)

content = content.replace(
    '_current_job["step"]     = f"Escena {scene_num}/{n_scenes}: audio..."',
    '_current_job["current_step"] = f"[{scene_num}/{n_scenes}] Generando audio..."\n                    _current_job["current_scene"] = scene_num'
)

content = content.replace(
    '_current_job["step"]     = f"Escena {scene_num}/{n_scenes}: clip..."',
    '_current_job["current_step"] = f"[{scene_num}/{n_scenes}] Ensamblando clip..."\n                    _current_job["current_scene"] = scene_num'
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] _current_job memory steps patched")
