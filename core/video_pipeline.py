"""
GRAVITY AI — VIDEO STUDIO PIPELINE BRIDGE V15.1 PRO
Capa de compatibilidad total hacia atrás (Bridge) que redirige todas las llamadas
y accesos a constantes al nuevo paquete modularizado `/core/video/`.
"""

import sys
import types
import os
import re
import json
import sqlite3
import threading
import subprocess
import hashlib
import math
from datetime import datetime, timezone
from typing import Optional

from core import video as _video

# Importaciones explícitas para herramientas de análisis estático, linters e IDEs
from core.video import (
    add_job,
    get_queue_status,
    cancel_job,
    delete_job,
    start,
    get_video_url,
    get_available_voices,
    CINEMA_STYLES,
    DEFAULT_STYLE,
    EMOTIONAL_GRADES,
    STYLE_COLOR_GRADES,
    BGM_GENERATORS,
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
    _init_db,
    _update_job,
    _check_cancelled,
    _process_job,
    _worker_loop,
    _infer_lang,
    _generate_audio,
    _ensure_bgm,
    _extract_visual_anchor,
    _get_scene_visual_context,
    _normalize_topic_for_lore,
    _get_lore_context,
    _generate_script,
    _get_branding_config,
    _generate_scene_image,
    _create_placeholder_image,
    _kenburns_vf,
    _create_title_card,
    _extract_thumbnail,
    _assemble_clip,
    _concatenate_clips
)

class _VideoPipelineBridge(types.ModuleType):
    """
    Proxy dinámico a nivel de módulo que delega todas las consultas y escrituras
    al paquete `core.video` y sus submódulos para garantizar 100% de compatibilidad en caliente.
    """
    def __init__(self):
        super().__init__("core.video_pipeline")
        
    def __getattribute__(self, name):
        # Interceptar variables dinámicas de ejecución mutables para evitar que monkeypatch oculte el valor real
        if name in ("_started", "_current_job", "_db_initialized", "_lock"):
            try:
                from core.video import pipeline
                return getattr(pipeline, name)
            except Exception:
                pass
        return super().__getattribute__(name)

    def __getattr__(self, name):
        # 1. Si son variables dinámicas mutables de ejecución, delegar a core.video.pipeline
        if name in ("_started", "_current_job", "_db_initialized", "_lock"):
            try:
                from core.video import pipeline
                return getattr(pipeline, name)
            except Exception:
                pass
                
        # 2. Intentar buscar en los globals del bridge (ej. librerías de sistema como os, re, sqlite3)
        if name in globals():
            return globals()[name]
            
        # 3. Delegar al paquete unificado core.video
        try:
            return getattr(_video, name)
        except AttributeError:
            pass
            
        # 4. Fallback de resolución al submódulo pipeline directamente
        try:
            from core.video import pipeline
            if hasattr(pipeline, name):
                return getattr(pipeline, name)
        except Exception:
            pass
            
        raise AttributeError(f"module 'core.video_pipeline' has no attribute '{name}'")
        
    def __setattr__(self, name, value):
        # Asignar en el bridge localmente para compatibilidad con hasattr()
        super().__setattr__(name, value)
        if name in globals():
            globals()[name] = value
            
        # Propagar dinámicamente a todos los submódulos para asegurar que los monkeypatches de test funcionen
        for sub in ["pipeline", "audio_processor", "script_builder", "renderer"]:
            try:
                mod_name = f"core.video.{sub}"
                if mod_name in sys.modules:
                    mod = sys.modules[mod_name]
                    setattr(mod, name, value)
            except Exception:
                pass

# Instanciar el proxy de módulo
sys.modules[__name__] = _VideoPipelineBridge()
