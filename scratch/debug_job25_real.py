import sys
import sqlite3
sys.path.append(r'F:\Gravity_AI_bridge')
from core.video_pipeline import DB_PATH, _process_job, DEFAULT_STYLE, DEFAULT_FPS, SECONDS_PER_SCENE, DEFAULT_BGM_VOLUME

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM video_jobs WHERE id=25").fetchone()

if row:
    keys = row.keys()
    try:
        _process_job(
            job_id         = row["id"],
            topic          = row["topic"],
            n_scenes       = row["n_scenes"],
            voice_speed    = row["voice_speed"],
            voice_id       = row["voice_id"]        if "voice_id"        in keys else "",
            style          = row["style"]           if "style"           in keys else DEFAULT_STYLE,
            narration_lang = row["narration_lang"]  if "narration_lang"  in keys else "es",
            transitions    = bool(row["transitions"] if "transitions"    in keys else 1),
            resolution     = row["resolution"]      if "resolution"      in keys else "1024x1024",
            subtitles      = bool(row["subtitles"]  if "subtitles"       in keys else 1),
            title          = row["title"]            if "title"           in keys else "",
            bgm_type       = row["bgm_type"]         if "bgm_type"        in keys else "ninguna",
            quality        = row["quality"]          if "quality"         in keys else "hd",
            use_lore       = bool(row["use_lore"]    if "use_lore"        in keys else 1),
            fps            = int(row["fps"])          if "fps"             in keys else DEFAULT_FPS,
            scene_duration = int(row["scene_duration"]) if "scene_duration" in keys else SECONDS_PER_SCENE,
            duration_mode  = row["duration_mode"]      if "duration_mode"  in keys else "auto",
            bgm_volume     = float(row["bgm_volume"]) if "bgm_volume"     in keys else DEFAULT_BGM_VOLUME,
            codec          = row["codec"]             if "codec"           in keys else "libx264",
            ken_burns      = bool(row["ken_burns"]    if "ken_burns"       in keys else 1),
            intro_card     = bool(row["intro_card"]   if "intro_card"      in keys else 0),
            color_grade    = row["color_grade"]       if "color_grade"     in keys else "auto",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
