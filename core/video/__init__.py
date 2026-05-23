import subprocess
import os

# Asegurar compatibilidad multiplataforma en subprocesos Unix (Linux/macOS)
if not hasattr(subprocess, "CREATE_NO_WINDOW"):
    setattr(subprocess, "CREATE_NO_WINDOW", 0)

from core.video.pipeline import (
    add_job,
    get_queue_status,
    cancel_job,
    delete_job,
    _init_db,
    _update_job,
    _check_cancelled,
    _process_job,
    _worker_loop,
    start,
    get_video_url,
    BASE_DIR,
    OUTPUT_DIR,
    DB_PATH,
    FFMPEG_EXE,
    DEFAULT_SCENES,
    DEFAULT_IMG_W,
    DEFAULT_IMG_H,
    SECONDS_PER_SCENE,
    TTS_RATE,
    MAX_HISTORY,
    FADE_DURATION,
    DEFAULT_FPS,
    REMOTION_FPS,
    DEFAULT_BGM_VOLUME,
    DB_CONNECT_TIMEOUT,
    EMOTIONAL_GRADES,
    STYLE_COLOR_GRADES
)

from core.video.audio_processor import (
    _infer_lang,
    get_available_voices,
    _generate_audio,
    _ensure_bgm,
    BGM_GENERATORS
)

from core.video.script_builder import (
    _extract_visual_anchor,
    _get_scene_visual_context,
    _normalize_topic_for_lore,
    _get_lore_context,
    _generate_script,
    CINEMA_STYLES,
    DEFAULT_STYLE
)

from core.video.renderer import (
    _get_branding_config,
    _generate_scene_image,
    _create_placeholder_image,
    _kenburns_vf,
    _create_title_card,
    _extract_thumbnail,
    _assemble_clip,
    _concatenate_clips
)

__all__ = [
    "add_job",
    "get_queue_status",
    "cancel_job",
    "delete_job",
    "start",
    "get_video_url",
    "get_available_voices",
    "CINEMA_STYLES",
    "DEFAULT_STYLE",
    "EMOTIONAL_GRADES",
    "STYLE_COLOR_GRADES",
    "BGM_GENERATORS",
    "BASE_DIR",
    "OUTPUT_DIR",
    "DB_PATH",
    "FFMPEG_EXE",
    "DEFAULT_SCENES",
    "DEFAULT_IMG_W",
    "DEFAULT_IMG_H",
    "SECONDS_PER_SCENE",
    "TTS_RATE",
    "MAX_HISTORY",
    "FADE_DURATION",
    "DEFAULT_FPS",
    "REMOTION_FPS",
    "DEFAULT_BGM_VOLUME",
    "DB_CONNECT_TIMEOUT",
    "_init_db",
    "_update_job",
    "_check_cancelled",
    "_process_job",
    "_worker_loop",
    "_infer_lang",
    "_generate_audio",
    "_ensure_bgm",
    "_extract_visual_anchor",
    "_get_scene_visual_context",
    "_normalize_topic_for_lore",
    "_get_lore_context",
    "_generate_script",
    "_get_branding_config",
    "_generate_scene_image",
    "_create_placeholder_image",
    "_kenburns_vf",
    "_create_title_card",
    "_extract_thumbnail",
    "_assemble_clip",
    "_concatenate_clips"
]
