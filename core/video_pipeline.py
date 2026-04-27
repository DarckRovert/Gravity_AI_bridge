
# -- Mapeo de Emociones a Color Grading Dinámico ------------------------------
EMOTIONAL_GRADES: dict[str, str] = {
    "neutral":   "eq=contrast=1.0:brightness=0.0:saturation=1.0",
    "tension":   "eq=contrast=1.3:brightness=-0.05:saturation=0.8:gamma=0.9,colorbalance=rs=0.1:gs=-0.05:bs=-0.1",
    "nostalgia": "eq=contrast=0.9:brightness=0.05:saturation=0.7:gamma=1.1,colorbalance=rs=0.1:gs=0.05:bs=-0.1",
    "euforia":   "eq=contrast=1.2:brightness=0.02:saturation=1.6:gamma=1.0,colorbalance=rs=0.05:gs=0.05:bs=0.1",
    "misterio":  "eq=contrast=1.4:brightness=-0.1:saturation=0.5:gamma=0.8,colorbalance=rs=-0.1:gs=-0.1:bs=0.2",
    "calidez":   "eq=contrast=1.1:brightness=0.03:saturation=1.3:gamma=1.05,colorbalance=rs=0.15:gs=0.05:bs=-0.1",
    "frio":      "eq=contrast=1.1:brightness=-0.02:saturation=0.9:gamma=0.95,colorbalance=rs=-0.2:gs=-0.1:bs=0.3",
    "accion":    "eq=contrast=1.3:brightness=0.0:saturation=1.4:gamma=0.9",
}
import re
"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  GRAVITY AI â€” VIDEO STUDIO PIPELINE V10.3 CINEMATIC EDITION                  â•‘
â•‘                                                                              â•‘
â•‘  Motor cinematogrÃ¡fico de Ãºltima generaciÃ³n con:                             â•‘
â•‘    â–¸ Character Consistency Engine â€” ancla visual por escena                  â•‘
â•‘    â–¸ Seed unificada por job â€” coherencia de estilo Pollinations              â•‘
â•‘    â–¸ Selector de voz SAPI â€” elige narrador por ID/nombre                    â•‘
â•‘    â–¸ Estilos cinematogrÃ¡ficos â€” Documental, Anime, Noir, Ã‰pico, etc.        â•‘
â•‘    â–¸ Idioma de narraciÃ³n configurable                                        â•‘
â•‘    â–¸ Transiciones fade entre escenas via ffmpeg                              â•‘
â•‘    â–¸ Soporte de mÃºsica de fondo (pista silenciosa/placeholder)               â•‘
â•‘                                                                              â•‘
â•‘  Flujo completo:                                                             â•‘
â•‘    1. LLM extrae Visual Anchor + genera guiÃ³n con N escenas (JSON)           â•‘
â•‘    2. Pollinations genera imagen por escena (anchor + style + seed/job)      â•‘
â•‘    3. Windows SAPI convierte narraciÃ³n a audio .wav (voz elegida)            â•‘
â•‘    4. ffmpeg ensambla imagen + audio â†’ clip .mp4 por escena (con fade)       â•‘
â•‘    5. ffmpeg concatena todos los clips â†’ video final .mp4                    â•‘
â•‘                                                                              â•‘
â•‘  Prerrequisitos:                                                             â•‘
â•‘    - ffmpeg en _integrations/ffmpeg/ffmpeg.exe                               â•‘
â•‘    - pyttsx3 (pip install pyttsx3)                                           â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

import os
import json
import time
import sqlite3
import threading
import subprocess
import hashlib
import math
from datetime import datetime, timezone
from typing import Optional

from core.logger import log

# â”€â”€ Rutas absolutas del proyecto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_EXE  = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
OUTPUT_DIR  = os.path.join(BASE_DIR, "_videos")
DB_PATH     = os.path.join(BASE_DIR, "_video_queue.sqlite")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# â”€â”€ ParÃ¡metros por defecto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DEFAULT_SCENES     = 6
DEFAULT_IMG_W      = 1216
DEFAULT_IMG_H      = 832
SECONDS_PER_SCENE  = 8
TTS_RATE           = 150
MAX_HISTORY        = 20
FADE_DURATION      = 0.4    # segundos de fade entre escenas
DEFAULT_FPS        = 24
DEFAULT_BGM_VOLUME = 0.1   # volumen relativo de la música de fondo (0.0-1.0)

# ── Generadores de BGM locales (sin internet) ─────────────────────────────────
# Expresiones aevalsrc para ffmpeg: música instrumental sintetizada.
# Formato: canal izquierdo | canal derecho (stereo via aevalsrc=expr:c=stereo)
BGM_GENERATORS: dict[str, str] = {
    # Épico: drone grave + melodía alta + armónicos
    "epico": (
        "0.28*sin(55*2*PI*t)+0.18*sin(110*2*PI*t)+0.12*sin(165*2*PI*t)+"
        "0.08*sin(82.41*2*PI*t)+0.05*sin(220*2*PI*t)+"
        "0.04*sin(329.63*2*PI*t*(1+0.001*sin(0.25*2*PI*t)))"
    ),
    # Documental: pads ambientales suaves, acorde mayor
    "documental": (
        "0.15*sin(220*2*PI*t)+0.12*sin(277.18*2*PI*t)+"
        "0.10*sin(329.63*2*PI*t)+0.07*sin(440*2*PI*t)+"
        "0.05*sin(110*2*PI*t)+0.03*sin(554.37*2*PI*t)"
    ),
    # Synthwave: arpegio 80s con vibrato sutil
    "synthwave": (
        "0.20*sin(130.81*2*PI*t*(1+0.003*sin(4*2*PI*t)))+"
        "0.15*sin(196*2*PI*t*(1+0.002*sin(4*2*PI*t)))+"
        "0.12*sin(261.63*2*PI*t)+0.08*sin(392*2*PI*t)+"
        "0.06*sin(523.25*2*PI*t)"
    ),
    # Jazz: bajo cálido + acorde jazz (7ma)
    "jazz": (
        "0.22*sin(87.31*2*PI*t)+0.15*sin(174.61*2*PI*t)+"
        "0.12*sin(261.63*2*PI*t)+0.09*sin(329.63*2*PI*t)+"
        "0.07*sin(392*2*PI*t)+0.05*sin(466.16*2*PI*t)"
    ),

    "publicitario": (
        "0.25*sin(196*2*PI*t)+0.2*sin(246.94*2*PI*t)+"
        "0.15*sin(293.66*2*PI*t)+0.1*sin(392*2*PI*t)+"
        "0.05*sin(587.33*2*PI*t)"
    ),
}


# â”€â”€ Estilos cinematogrÃ¡ficos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CINEMA_STYLES: dict[str, dict] = {
    "documental": {
        "label":  "Documental",
        "prefix": "Cinematic documentary, photorealistic, professional lighting, 16:9 landscape, dramatic composition, high detail, award-winning photography",
        "negative": "cartoon, anime, painting, sketch, low quality, blurry",
    },
    "anime": {
        "label":  "Anime",
        "prefix": "Anime style, vibrant colors, high-quality illustration, detailed cel shading, dynamic scene, 16:9 aspect",
        "negative": "photorealistic, 3D render, low quality, blurry, ugly",
    },
    "epico": {
        "label":  "Ã‰pico / Fantasy",
        "prefix": "Epic fantasy artwork, dramatic lighting, cinematic atmosphere, detailed digital painting, heroic composition, 16:9",
        "negative": "modern, mundane, low quality, stock photo",
    },
    "noir": {
        "label":  "Noir / Thriller",
        "prefix": "Film noir, high contrast black and white, moody shadows, 1940s aesthetic, dramatic chiaroscuro, cinematic still, 16:9",
        "negative": "colorful, bright, cheerful, low quality",
    },
    "infantil": {
        "label":  "Infantil / Cuento",
        "prefix": "Children's storybook illustration, cute and colorful, soft warm lighting, friendly characters, Pixar-style, 16:9",
        "negative": "dark, scary, violent, photorealistic, gore",
    },
    "naturaleza": {
        "label":  "Naturaleza / Wildlife",
        "prefix": "National Geographic photography, ultra high resolution, dramatic natural lighting, pristine nature, macro or wide landscape, 16:9",
        "negative": "people, buildings, urban, low quality",
    },
    "cyberpunk": {
        "label":  "Cyberpunk / Sci-Fi",
        "prefix": "Cyberpunk cityscape, neon lights, rain-soaked streets, futuristic dystopia, cinematic composition, ultra-detailed, 16:9",
        "negative": "medieval, nature, low quality, blurry",
    },
    "historico": {
        "label":  "HistÃ³rico / Ã‰pocas",
        "prefix": "Historical epic scene, period-accurate set design, dramatic oil painting style, cinematic lighting, 16:9",
        "negative": "modern, sci-fi, cartoon, low quality",
    },
    "lofi": {
        "label":  "Lo-Fi / Estudiantil",
        "prefix": "Lofi aesthetic, cozy study room, warm pastel colors, rain window, soft grain texture, illustration style, calm atmosphere, 16:9",
        "negative": "dark, scary, violent, photorealistic, high contrast, gore",
    },
    "retro80s": {
        "label":  "Retro 80s / Synth-wave",
        "prefix": "Synthwave retro 1980s aesthetic, neon pink and purple gradients, grid horizon, chrome lettering, vaporwave sunset, cinematic 16:9",
        "negative": "modern minimal, flat design, photography, low quality, blurry",
    },
    "publicitario": {
        "label":  "Publicidad / Comercial",
        "prefix": "High-end commercial photography, ultra sharp, vivid studio lighting, 4k resolution, bright and energetic, modern product advertising, 16:9",
        "negative": "dark, gloomy, low quality, amateur, blurry, messy",
    },
}
DEFAULT_STYLE = "documental"

# -- Color Grades por Estilo (cinematic auto-grading) --------------------------
STYLE_COLOR_GRADES = {
    "documental": "eq=contrast=1.05:brightness=0.02:saturation=0.9",
    "anime":      "eq=contrast=1.1:brightness=0.0:saturation=1.5",
    "epico":      "eq=contrast=1.3:brightness=-0.05:saturation=1.2:gamma=0.9,colorbalance=rs=0.05:gs=-0.02:bs=-0.05",
    "noir":       "eq=contrast=1.4:brightness=-0.1:saturation=0.0:gamma=0.85",
    "infantil":   "eq=contrast=0.95:brightness=0.05:saturation=1.4",
    "naturaleza": "eq=contrast=1.1:brightness=0.03:saturation=1.3,colorbalance=rs=-0.05:gs=0.05:bs=0.0",
    "cyberpunk":  "eq=contrast=1.3:brightness=-0.05:saturation=1.1,colorbalance=rs=-0.1:gs=-0.1:bs=0.3",
    "historico":  "eq=contrast=1.1:brightness=0.02:saturation=0.75:gamma=1.05,colorbalance=rs=0.1:gs=0.05:bs=-0.1",
    "lofi":       "eq=contrast=0.9:brightness=0.05:saturation=0.8:gamma=1.1",
    "retro80s":   "eq=contrast=1.15:brightness=0.0:saturation=1.4,colorbalance=rs=0.05:gs=-0.1:bs=0.15",
    "publicitario": "eq=contrast=1.15:brightness=0.05:saturation=1.2:gamma=1.05",
    "cinematic":  "eq=contrast=1.2:brightness=-0.03:saturation=0.95:gamma=0.95,colorbalance=rs=0.03:gs=0.0:bs=-0.05",
}


# â”€â”€ Estado global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_lock         = threading.Lock()
_current_job  = None
_started      = False


# â”€â”€ Base de datos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            topic           TEXT    NOT NULL,
            n_scenes        INTEGER NOT NULL DEFAULT 6,
            voice_speed     INTEGER NOT NULL DEFAULT 150,
            voice_id        TEXT    NOT NULL DEFAULT '',
            style           TEXT    NOT NULL DEFAULT 'documental',
            narration_lang  TEXT    NOT NULL DEFAULT 'es',
            transitions     INTEGER NOT NULL DEFAULT 1,
            status          TEXT    NOT NULL DEFAULT 'pending',
            progress        INTEGER NOT NULL DEFAULT 0,
            current_step    TEXT,
            output_path     TEXT,
            error           TEXT,
            created_at      TEXT    NOT NULL,
            started_at      TEXT,
            finished_at     TEXT
        )
    """)
    conn.commit()
    # MigraciÃ³n: aÃ±adir columnas nuevas si la tabla ya existÃ­a sin ellas
    existing = {row[1] for row in conn.execute("PRAGMA table_info(video_jobs)").fetchall()}
    migrations = [
        ("voice_id",       "TEXT NOT NULL DEFAULT ''"),
        ("style",          "TEXT NOT NULL DEFAULT 'documental'"),
        ("narration_lang", "TEXT NOT NULL DEFAULT 'es'"),
        ("transitions",    "INTEGER NOT NULL DEFAULT 1"),
        ("resolution",     "TEXT NOT NULL DEFAULT '1024x1024'"),
        ("subtitles",      "INTEGER NOT NULL DEFAULT 1"),
        ("title",          "TEXT NOT NULL DEFAULT ''"),
        ("bgm_type",       "TEXT NOT NULL DEFAULT 'ninguna'"),
        ("quality",        "TEXT NOT NULL DEFAULT 'hd'"),
        ("use_lore",       "INTEGER NOT NULL DEFAULT 1"),
        ("fps",            "INTEGER NOT NULL DEFAULT 24"),
        ("scene_duration", "INTEGER NOT NULL DEFAULT 8"),
        ("duration_mode",  "TEXT NOT NULL DEFAULT 'auto'"),
        ("bgm_volume",     "REAL NOT NULL DEFAULT 0.1"),
        ("codec",          "TEXT NOT NULL DEFAULT 'libx264'"),
        ("ken_burns",      "INTEGER NOT NULL DEFAULT 1"),
        ("intro_card",     "INTEGER NOT NULL DEFAULT 0"),
        ("color_grade",    "TEXT NOT NULL DEFAULT 'auto'"),
        ("thumbnail_path", "TEXT NOT NULL DEFAULT ''"),
    ]
    for col_name, col_def in migrations:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE video_jobs ADD COLUMN {col_name} {col_def}")
    conn.commit()
    conn.close()


def add_job(
    topic: str,
    n_scenes: int       = DEFAULT_SCENES,
    voice_speed: int    = TTS_RATE,
    voice_id: str       = "",
    style: str          = DEFAULT_STYLE,
    narration_lang: str = "es",
    transitions: bool   = True,
    resolution: str     = "1024x1024",
    subtitles: bool     = True,
    title: str          = "",
    bgm_type: str       = "ninguna",
    quality: str        = "hd",
    use_lore: bool      = True,
    fps: int            = DEFAULT_FPS,
    scene_duration: int = SECONDS_PER_SCENE,
    duration_mode: str  = "auto",
    bgm_volume: float   = DEFAULT_BGM_VOLUME,
    codec: str          = "libx264",
    ken_burns: bool     = True,
    intro_card: bool    = False,
    color_grade: str    = "auto",
) -> int:
    """Encola un nuevo trabajo de video. Retorna el ID generado."""
    _init_db()
    if style not in CINEMA_STYLES:
        style = DEFAULT_STYLE
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.execute(
        "INSERT INTO video_jobs "
        "(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, "
        " resolution, subtitles, title, bgm_type, quality, use_lore, fps, scene_duration, "
        " duration_mode, bgm_volume, codec, ken_burns, intro_card, color_grade, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            topic, n_scenes, voice_speed, voice_id, style, narration_lang,
            1 if transitions else 0, resolution, 1 if subtitles else 0,
            title, bgm_type, quality, 1 if use_lore else 0,
            fps, scene_duration, duration_mode, float(bgm_volume), codec,
            1 if ken_burns else 0, 1 if intro_card else 0, color_grade, now
        )
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    log.info(f"[VideoStudio] Job #{job_id} encolado: {title or topic[:60]} | estilo={style} | voz='{voice_id or 'auto'}' | calidad={quality}")
    return job_id


def get_queue_status() -> dict:
    """Estado completo de la cola de video para el dashboard."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending  = [dict(r) for r in conn.execute(
        "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id"
    ).fetchall()]
    
    raw_history = conn.execute(
        "SELECT * FROM video_jobs WHERE status NOT IN ('pending', 'deleted') ORDER BY id DESC LIMIT ?",
        (MAX_HISTORY,)
    ).fetchall()
    
    history = []
    for r in raw_history:
        job_dict = dict(r)
        if job_dict.get('status') in ('done', 'completed') and job_dict.get('output_path'):
            if not os.path.isfile(job_dict['output_path']):
                # Persistir la purga automática en la base de datos
                conn.execute("UPDATE video_jobs SET status='deleted', output_path=NULL WHERE id=?", (job_dict['id'],))
                continue  # No agregarlo al historial visible
        history.append(job_dict)
        
    conn.commit()
    conn.close()

    with _lock:
        current = _current_job

    # Aggregate stats from DB (all-time)
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
    }


def cancel_job(job_id: int) -> bool:
    """Cancela un trabajo pendiente. Retorna False si no existe o no estaba pendiente."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = conn.execute(
        "UPDATE video_jobs SET status='cancelled', finished_at=? "
        "WHERE id=? AND status IN ('pending', 'running')",
        (now, job_id)
    ).rowcount
    conn.commit()
    conn.close()
    return rows > 0


def delete_job(job_id: int) -> dict:
    """Elimina un job de la DB y borra sus archivos físicos del disco."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT output_path FROM video_jobs WHERE id=?", (job_id,)).fetchone()
    deleted_files: list[str] = []
    errors: list[str] = []

    if row:
        # Borrar video final
        out_path = row["output_path"]
        if out_path and os.path.isfile(out_path):
            try:
                os.remove(out_path)
                deleted_files.append(out_path)
            except Exception as e:
                errors.append(str(e))
        # Borrar carpeta de trabajo del job (escenas, audios, clips)
        job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
        if os.path.isdir(job_dir):
            import shutil
            try:
                shutil.rmtree(job_dir)
                deleted_files.append(job_dir)
            except Exception as e:
                errors.append(str(e))
        # Marcar en DB como deleted
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn.execute(
            "UPDATE video_jobs SET status='deleted', output_path=NULL, finished_at=? WHERE id=?",
            (now, job_id)
        )
        conn.commit()
    conn.close()
    return {
        "ok": row is not None,
        "deleted_files": deleted_files,
        "errors": errors,
        "job_id": job_id,
    }


# â”€â”€ Voces SAPI disponibles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_available_voices() -> list[dict]:
    """
    Lista TODAS las voces instaladas en el sistema mediante win32com + SAPI directo.
    Detecta voces SAPI5 legacy, OneCore, Neural (Windows 11) y voces de terceros.
    Fallback a pyttsx3 si win32com no está disponible.
    """
    v_list: list[dict] = []
    seen_ids: set[str] = set()

    def _infer_lang(vid: str, name: str) -> str:
        combined = (vid + name).lower()
        if any(t in combined for t in ("es-", "es_", "spanish", "español", "_es", "-es")):
            return "es"
        if any(t in combined for t in ("en-", "en_", "english", "_en", "-en")):
            return "en"
        if any(t in combined for t in ("pt-", "pt_", "portug")):
            return "pt"
        if any(t in combined for t in ("fr-", "fr_", "french", "français")):
            return "fr"
        if any(t in combined for t in ("de-", "de_", "german", "deutsch")):
            return "de"
        return "other"

    # ── Motor primario: win32com SAPI directo ────────────────────────────────
    # Accede a TODAS las voces: SAPI5, OneCore, Neural y voces de terceros.
    if os.name == "nt":
        try:
            import win32com.client
            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            voice_tokens = sapi.GetVoices()
            for i in range(voice_tokens.Count):
                token = voice_tokens.Item(i)
                vid  = token.Id or ""
                name = token.GetDescription() or vid
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    v_list.append({
                        "id":     vid,
                        "name":   name,
                        "lang":   _infer_lang(vid, name),
                        "gender": "unknown",
                        "engine": "sapi",
                    })
            log.info(f"[VideoStudio] win32com SAPI: {len(v_list)} voces detectadas.")
        except Exception as e:
            log.warning(f"[VideoStudio] win32com no disponible ({e}), usando pyttsx3 fallback.")

    # ── Fallback: pyttsx3 ────────────────────────────────────────────────────
    if not v_list:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                vid  = v.id or ""
                name = v.name or vid
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    v_list.append({
                        "id":     vid,
                        "name":   name,
                        "lang":   _infer_lang(vid, name),
                        "gender": v.gender or "unknown",
                        "engine": "pyttsx3",
                    })
            engine.stop()
            log.info(f"[VideoStudio] pyttsx3 fallback: {len(v_list)} voces detectadas.")
        except Exception as e:
            log.warning(f"[VideoStudio] No se pudo listar voces: {e}")

    # ── Complemento: voces OneCore via SpObjectTokenCategory ────────────────
    # Usa la misma API COM que _generate_audio para garantizar IDs idénticos.
    if os.name == "nt":
        try:
            import win32com.client
            onecore_reg_paths = [
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices",
            ]
            for reg_path in onecore_reg_paths:
                try:
                    cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    cat.SetId(reg_path, False)
                    extra_tokens = cat.EnumerateTokens()
                    for i in range(extra_tokens.Count):
                        t = extra_tokens.Item(i)
                        vid  = t.Id or ""
                        name = t.GetDescription() or vid
                        if vid and vid not in seen_ids:
                            seen_ids.add(vid)
                            source = "OneCore" if "OneCore" in reg_path else "SAPI5"
                            v_list.append({
                                "id":     vid,
                                "name":   f"{source}: {name}",
                                "lang":   _infer_lang(vid, name),
                                "gender": "unknown",
                                "engine": "sapi_cat",
                            })
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"[VideoStudio] Error enumerando voces OneCore via SpObjectTokenCategory: {e}")

    if not v_list:
        log.error("[VideoStudio] No se encontró ninguna voz instalada en el sistema.")
    else:
        log.info(f"[VideoStudio] Total voces disponibles: {len(v_list)}")

    return v_list


# â”€â”€ Paso 1: ExtracciÃ³n de Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _extract_visual_anchor(topic: str) -> str:
    """
    Usa el LLM para extraer un descriptor visual conciso y consistente del tema.
    """
    system_prompt = (
        "You are a visual descriptor assistant for AI image generation. "
        "Respond ONLY with a single compact English phrase. No bullet points, no JSON."
    )
    user_prompt = (
        f"Given the story/documentary topic: '{topic}'\n"
        "Extract a VISUAL CHARACTER/SUBJECT ANCHOR — a compact description of the main "
        "subject's permanent visual attributes (species, breed, color, name label if relevant, "
        "distinctive features). This anchor will be prepended to every scene prompt to maintain "
        "visual consistency across all generated images.\n"
        "Example for 'a siamese kitten named Jamon':\n"
        "  → 'siamese kitten with cream and dark brown fur, blue eyes, named Jamon, small and fluffy'\n"
        "Example for 'the history of Ancient Rome':\n"
        "  → 'ancient Roman setting, marble columns, toga-wearing citizens, Latin inscriptions'\n"
        "Respond ONLY with the anchor phrase, nothing else."
    )
    try:
        from core import provider_manager
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No LLM disponible")
        anchor = provider_manager.complete(
            messages,
            model=best_model,
            provider=best_result.name,
            options={"temperature": 0.3, "max_tokens": 80},
        )
        anchor = anchor.strip().strip('"').strip("'")
        for prefix in ("anchor:", "→", "-", "*"):
            if anchor.lower().startswith(prefix):
                anchor = anchor[len(prefix):].strip()
        if len(anchor) > 10:
            log.info(f"[VideoStudio] Visual Anchor extraído: '{anchor[:80]}'")
            return anchor
    except Exception as e:
        log.warning(f"[VideoStudio] LLM anchor fallback ({e}). Usando topic como anchor.")

    return topic[:120]


# ── Paso 2: Generación de guión via LLM ──────────────────────────────────────

def _normalize_topic_for_lore(topic: str) -> str:
    """
    Normaliza un topic para búsqueda en el lore:
    - Elimina indicadores de parte/continuación ('parte 2', 'part ii', 'capitulo 3', etc.)
    - Convierte a minúsculas y elimina espacios extra.
    """
    import re
    t = topic.lower().strip()
    # Eliminar sufijos de continuación: "parte 2", "part 2", "capitulo 3", "ep 1", etc.
    t = re.sub(r"\s*(parte|part|capitulo|capítulo|episode|ep|vol|volume|\#)\s*[\divxlc]+\s*$", "", t).strip()
    return t


def _get_lore_context(topic: str, limit_chars: int = 4000) -> str:
    """
    Extrae contexto de lore EXCLUSIVO para el topic dado.
    SOLO devuelve bloques cuyo encabezado coincida con el topic normalizado.
    NO hace fallback al archivo completo para evitar contaminación entre historias.
    """
    lore_path = os.path.join(BASE_DIR, "inputs", "cinematic_lore.txt")
    if not os.path.isfile(lore_path):
        return ""

    try:
        with open(lore_path, "r", encoding="utf-8") as f:
            content = f.read()

        clean_topic = _normalize_topic_for_lore(topic)
        if not clean_topic:
            return ""

        relevant_blocks: list[str] = []
        # Dividir en bloques por marcador de historia
        raw_blocks = content.split("=== HISTORIA:")
        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            # Extraer solo el encabezado (hasta el primer ===)
            end_marker = block.find("===")
            if end_marker == -1:
                header_raw = block.split("\n")[0]
                body = block
            else:
                header_raw = block[:end_marker].strip()
                body = block[end_marker + 3:].strip()

            header_norm = _normalize_topic_for_lore(header_raw)

            # Coincidencia estricta: el topic normalizado debe estar contenido
            # en el encabezado normalizado del bloque (no al revés)
            if clean_topic in header_norm or header_norm in clean_topic:
                relevant_blocks.append(
                    f"=== HISTORIA: {header_raw} ===\n{body}"
                )

        if relevant_blocks:
            context = "\n\n".join(relevant_blocks)
            log.info(
                f"[VideoStudio] Lore: {len(relevant_blocks)} bloque(s) encontrado(s) para '{topic}' "
                f"({len(context)} chars)"
            )
            return context[-limit_chars:]

        # Sin coincidencia → no contaminar con lore de otras historias
        log.info(f"[VideoStudio] Lore: sin historia previa para '{topic}'. Inicio de nueva historia.")
        return ""

    except Exception as e:
        log.warning(f"[VideoStudio] Error leyendo lore: {e}")
        return ""


def _generate_script(topic: str, n_scenes: int, style: str, narration_lang: str, use_lore: bool = True) -> tuple[list[dict], str]:
    """
    Genera guión estructurado incorporando contexto de lore previo.
    """
    style_info     = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    style_prefix   = style_info["prefix"]
    
    lore_context = ""
    if use_lore:
        lore_context = _get_lore_context(topic)
        if lore_context:
            log.info(f"[VideoStudio] Contexto de Lore recuperado ({len(lore_context)} chars)")

    lang_names = {
        "es": "español", "en": "English", "pt": "português",
        "fr": "français", "de": "Deutsch", "it": "italiano",
    }
    lang_label = lang_names.get(narration_lang, "español")

    system_prompt = (
        "Eres un guionista profesional de cine y documentales. "
        "Responde ÚNICAMENTE con JSON válido, sin texto adicional."
    )
    
    user_prompt = (
        f"Crea un guión de {n_scenes} escenas para un video sobre: '{topic}'.\n"
        f"Estilo visual: {style_info['label']} — {style_prefix}\n"
        f"Idioma de narración: {lang_label}\n\n"
    )

    if lore_context:
        user_prompt += (
            "CONTEXTO DE HISTORIAS PREVIAS (Lore):\n"
            "Utiliza esta información para mantener coherencia si este video es una continuación "
            "o parte de un universo ya existente:\n"
            f"{lore_context}\n\n"
        )

    user_prompt += (
        "REGLA CRÍTICA DE CONSISTENCIA VISUAL: El campo 'image_prompt' de CADA escena "
        "DEBE comenzar describiendo al personaje/sujeto principal con los MISMOS atributos visuales "
        "(raza, color, rasgos físicos, nombre) en todas las escenas. Nunca omitas estos atributos.\n\n"
        "Responde con este JSON exacto (sin ningún texto antes o después):\n"
        "[\n"
        "  {\n"
        '    "title": "Título corto de la escena",\n'
        '    "character_anchor": "Descripción compacta en inglés del sujeto principal con atributos físicos fijos",\n'
        '    "image_prompt": "Descripción visual detallada en inglés. DEBE incluir el character_anchor al inicio.",\n'
        f'    "narration": "Texto de narración en {lang_label} para esta escena (2-4 oraciones)."\n'
        "  }\n"
        "]\n"
        f"Genera exactamente {n_scenes} escenas. Solo JSON, nada más."
    )

    try:
        from core import provider_manager
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No hay proveedor LLM activo")

        log.info(f"[VideoStudio] Usando '{best_result.name}/{best_model}' para guión")
        content = provider_manager.complete(
            messages, model=best_model, provider=best_result.name,
            options={"temperature": 0.7}
        )

        content = content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.startswith("json"): content = content[4:]
        content = content.strip()

        start = content.find("[")
        end   = content.rfind("]") + 1
        if start != -1 and end > start:
            content = content[start:end]

        scenes = json.loads(content)
        if isinstance(scenes, list) and len(scenes) > 0:
            anchor = ""
            for sc in scenes:
                ca = sc.get("character_anchor", "").strip()
                if ca and len(ca) > 5:
                    anchor = ca
                    break
            if not anchor:
                anchor = _extract_visual_anchor(topic)
            return scenes[:n_scenes], anchor

        raise ValueError("LLM no devolvió lista JSON válida")

    except Exception as e:
        log.warning(f"[VideoStudio] LLM no disponible ({e}). Fallback.")

    anchor = _extract_visual_anchor(topic)
    scenes = [
        {
            "title": f"Escena {i+1}: {topic}",
            "character_anchor": anchor,
            "image_prompt": f"{anchor}, cinematic scene {i+1}, {style_prefix}, high detail",
            "narration": f"Esta es la escena {i+1} sobre {topic}."
        }
        for i in range(n_scenes)
    ]
    return scenes, anchor

# ── Paso 3: Generación de imagen con consistencia ──────────────────────────

def _generate_scene_image(
    prompt: str,
    scene_idx: int,
    job_id: int,
    job_seed: int,
    style: str,
    resolution: str = "1024x1024",
) -> Optional[str]:
    """
    Genera imagen de una escena con consistencia visual garantizada.
    - Usa seed derivada del job_id para coherencia de estilo entre escenas.
    - Aplica el estilo cinematogrÃ¡fico como prefijo.
    Motor primario: Pollinations.ai
    Motor fallback: Fooocus
    """
    job_dir    = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    out_path   = os.path.join(job_dir, f"scene_{scene_idx:02d}_image.png")
    os.makedirs(job_dir, exist_ok=True)

    style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    negative     = style_info.get("negative", "")
    # Seed por escena: base del job + offset de escena â†’ consistencia relativa
    scene_seed   = (job_seed + scene_idx * 7) % 2147483647

    # â”€â”€ Motor 1: Pollinations.ai â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Extraer resolucion
    w, h = DEFAULT_IMG_W, DEFAULT_IMG_H
    if "x" in resolution:
        parts = resolution.split("x")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            w, h = int(parts[0]), int(parts[1])

    try:
        from tools.pollinations_generator import generate as poll_gen
        result = poll_gen(
            prompt          = prompt,
            output_path     = out_path,
            width           = w,
            height          = h,
            seed            = scene_seed,
            enhance         = False,   # desactivado para mayor fidelidad al prompt exacto
            negative_prompt = negative,
        )
        if result.get("success") and os.path.isfile(out_path):
            log.info(f"[VideoStudio] [Pollinations] Escena {scene_idx}: {os.path.basename(out_path)} (seed={scene_seed})")
            return out_path
        else:
            log.warning(f"[VideoStudio] [Pollinations] FallÃ³ escena {scene_idx}: {result.get('error')}")
    except Exception as e:
        log.warning(f"[VideoStudio] [Pollinations] Exception escena {scene_idx}: {e}")

    # â”€â”€ Motor 2: Fooocus (fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        from tools.fooocus_client import trigger_gradio_generation, health_check
        if health_check().get("online"):
            result = trigger_gradio_generation(
                prompt       = prompt,
                performance  = "Speed",
                aspect_ratio = f"{w}*{h}",
            )
            if result.get("success") and result.get("images"):
                img_src = result["images"][0]
                if os.path.isfile(img_src):
                    import shutil
                    shutil.copy2(img_src, out_path)
                    log.info(f"[VideoStudio] [Fooocus] Escena {scene_idx}: {os.path.basename(out_path)}")
                    return out_path
        else:
            log.info("[VideoStudio] Fooocus offline â€” saltando fallback.")
    except Exception as e:
        log.warning(f"[VideoStudio] [Fooocus] Exception escena {scene_idx}: {e}")

    return None


# â”€â”€ Paso 4: Text-to-Speech â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _generate_audio(
    text: str,
    output_wav: str,
    rate: int     = TTS_RATE,
    voice_id: str = "",
) -> bool:
    """
    Convierte texto a audio WAV usando Windows SAPI.
    Motor primario: win32com SAPI directo (soporta TODAS las voces: SAPI5, OneCore, Neural).
    Motor secundario: pyttsx3 (solo voces SAPI5 legacy).
    Selección de voz: exacta por ID > substring de ID/nombre > español automático > primera disponible.
    """
    # ── Motor primario: win32com SAPI (SAPI5 + OneCore + Neural) ─────────────
    if os.name == "nt":
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()

            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            file_stream = win32com.client.Dispatch("SAPI.SpFileStream")

            # ── Construir lista completa: SAPI5 + OneCore via SpObjectTokenCategory ──
            token_list: list = []
            seen_tok_ids: set[str] = set()

            # SAPI5 estándar
            voice_tokens = sapi.GetVoices()
            for i in range(voice_tokens.Count):
                t = voice_tokens.Item(i)
                token_list.append(t)
                seen_tok_ids.add((t.Id or "").lower())

            # OneCore y Neural via SpObjectTokenCategory (mismos IDs que la lista de voces del frontend)
            _onecore_paths = [
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices",
            ]
            for _reg_path in _onecore_paths:
                try:
                    cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    cat.SetId(_reg_path, False)
                    extra = cat.EnumerateTokens()
                    for i in range(extra.Count):
                        t = extra.Item(i)
                        if (t.Id or "").lower() not in seen_tok_ids:
                            token_list.append(t)
                            seen_tok_ids.add((t.Id or "").lower())
                except Exception:
                    pass

            selected_token = None

            # Prioridad 1: coincidencia exacta o substring del voice_id
            if voice_id:
                vid_lower = voice_id.lower()
                for tok in token_list:
                    tok_id   = (tok.Id or "").lower()
                    tok_name = (tok.GetDescription() or "").lower()
                    if vid_lower == tok_id or vid_lower in tok_id or tok_id in vid_lower or vid_lower in tok_name:
                        selected_token = tok
                        log.info(f"[VideoStudio] TTS (win32com) voz seleccionada: {tok.GetDescription()} | ID: {tok.Id}")
                        break

            # Prioridad 2: voz española automática
            if not selected_token:
                es_markers = ("es-", "es_", "spanish", "español", "_es", "-es", "esES", "esMX")
                for tok in token_list:
                    combined = ((tok.Id or "") + (tok.GetDescription() or "")).lower()
                    if any(m.lower() in combined for m in es_markers):
                        selected_token = tok
                        log.info(f"[VideoStudio] TTS (win32com) voz española auto: {tok.GetDescription()}")
                        break

            # Prioridad 3: primera voz disponible
            if not selected_token and token_list:
                selected_token = token_list[0]
                log.warning(f"[VideoStudio] TTS (win32com) primera voz disponible: {selected_token.GetDescription()}")

            if selected_token:
                sapi.Voice = selected_token
                # Mapeo lineal: 100 WPM → -5, 150 WPM → 0, 200 WPM → 5, 250 WPM → 10
                sapi.Rate  = max(-10, min(10, int((rate - 150) / 10)))

                os.makedirs(os.path.dirname(output_wav), exist_ok=True)
                file_stream.Open(output_wav, 3)  # SSFMCreateForWrite = 3
                sapi.AudioOutputStream = file_stream
                sapi.Speak(text)
                file_stream.Close()

                ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
                if ok:
                    size_kb = os.path.getsize(output_wav) // 1024
                    log.info(f"[VideoStudio] Audio (win32com): {os.path.basename(output_wav)} ({size_kb} KB)")
                    pythoncom.CoUninitialize()
                    return ok

            pythoncom.CoUninitialize()
        except Exception as e:
            log.warning(f"[VideoStudio] win32com TTS falló ({e}), usando pyttsx3 fallback.")

    # ── Motor secundario: pyttsx3 ────────────────────────────────────────────
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        voices = engine.getProperty("voices")

        selected = None

        if voice_id:
            vid_lower = voice_id.lower()
            selected  = next(
                (v for v in voices if
                 vid_lower in (v.id or "").lower() or
                 vid_lower in (v.name or "").lower()),
                None
            )
            if selected:
                log.info(f"[VideoStudio] TTS (pyttsx3) voz seleccionada: {selected.name}")

        if not selected:
            selected = next(
                (v for v in voices if
                 any(t in (v.id or "").lower()   for t in ("es-", "es_", "spanish", "español")) or
                 any(t in (v.name or "").lower() for t in ("spanish", "español", "helena", "sabina", "pablo", "laura", "jorge"))
                ),
                None
            )
            if selected:
                log.info(f"[VideoStudio] TTS (pyttsx3) voz española auto: {selected.name}")

        if not selected and voices:
            selected = voices[0]
            log.warning(f"[VideoStudio] TTS (pyttsx3) primera voz disponible: {selected.name}")

        if not selected:
            log.error("[VideoStudio] No hay voces SAPI disponibles.")
            engine.stop()
            return False

        engine.setProperty("voice", selected.id)
        engine.save_to_file(text, output_wav)
        engine.runAndWait()
        engine.stop()

        ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
        if ok:
            size_kb = os.path.getsize(output_wav) // 1024
            log.info(f"[VideoStudio] Audio (pyttsx3): {os.path.basename(output_wav)} ({size_kb} KB)")
        return ok
    except Exception as e:
        log.error(f"[VideoStudio] Error TTS pyttsx3: {e}")
        return False


# â”€â”€ Paso 5: Ensamblado por escena con fade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


# -- Ken Burns: zoom+pan cinematico sobre imagen estatica ---------------------

def _kenburns_vf(clip_dur: float, fps: int, w: int, h: int, scene_idx: int) -> str:
    """Genera filtro zoompan alterno: escena par=zoom-in, impar=zoom-out+pan."""
    total_frames = max(1, int(clip_dur * fps))
    if scene_idx % 2 == 0:
        z  = "'min(zoom+0.0008,1.18)'"
        x  = "'iw/2-(iw/zoom/2)'"
        y  = "'ih/2-(ih/zoom/2)'"
    else:
        z  = "'if(eq(on,1),1.18,max(zoom-0.0008,1.0))'"
        x  = "'iw/2-(iw/zoom/2)+(iw*0.03*on/" + str(total_frames) + ")'"
        y  = "'ih/2-(ih/zoom/2)'"
    return (
        'zoompan=z=' + z + ':d=' + str(total_frames) +
        ':x=' + x + ':y=' + y +
        ':s=' + str(w) + 'x' + str(h) + ':fps=' + str(fps)
    )


# -- Title card: intro animado con drawtext -----------------------------------

def _create_title_card(
    title: str,
    subtitle: str,
    output_mp4: str,
    w: int,
    h: int,
    fps: int,
    duration: float,
    codec: str,
) -> bool:
    """Genera un clip de intro con titulo y subtitulo sobre fondo negro."""
    if not os.path.isfile(FFMPEG_EXE):
        return False
    import re as _re
    safe_title    = _re.sub(r"[:'%]", '', title)[:60]
    safe_subtitle = _re.sub(r"[:'%]", '', subtitle)[:80]
    vf = (
        "color=c=black:s=" + str(w) + "x" + str(h) + ":d=" + str(duration) + "[bg];"
        "[bg]drawtext=fontsize=" + str(max(24, h // 20)) + ":fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-40"
        ":text='" + safe_title + "':alpha='if(lt(t,0.5),t/0.5,if(gt(t," + str(duration - 0.5) + "),(1-(t-" + str(duration - 0.5) + ")/0.5),1))',"
        "drawtext=fontsize=" + str(max(14, h // 35)) + ":fontcolor=0xAAAAAA:x=(w-text_w)/2:y=(h-text_h)/2+40"
        ":text='" + safe_subtitle + "':alpha='if(lt(t,0.8),t/0.8,if(gt(t," + str(duration - 0.5) + "),(1-(t-" + str(duration - 0.5) + ")/0.5),1))'"
    )
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi", "-i", vf,
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        ok = r.returncode == 0 and os.path.isfile(output_mp4)
        if ok:
            log.info("[VideoStudio] Intro card generada: " + os.path.basename(output_mp4))
        else:
            log.warning("[VideoStudio] Intro card fallida: " + r.stderr.decode(errors="replace")[-200:])
        return ok
    except Exception as e:
        log.warning("[VideoStudio] Intro card excepcion: " + str(e))
        return False


# -- Thumbnail: extraer frame destacado del video final ----------------------

def _extract_thumbnail(video_path: str, output_jpg: str, at_sec: float = 3.0) -> bool:
    """Extrae un frame del video como thumbnail JPEG."""
    if not os.path.isfile(video_path) or not os.path.isfile(FFMPEG_EXE):
        return False
    cmd = [
        FFMPEG_EXE, "-y",
        "-ss", str(at_sec),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "3",
        output_jpg,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        return r.returncode == 0 and os.path.isfile(output_jpg)
    except Exception:
        return False

def _assemble_clip(
    image_path: str,
    audio_path: str,
    output_mp4: str,
    fade: bool = True,
    resolution: str = "1024x1024",
    text: str = "",
    subtitles: bool = True,
    fps: int = DEFAULT_FPS,
    scene_duration: int = SECONDS_PER_SCENE,
    duration_mode: str = "auto",
    codec: str = "libx264",
    ken_burns: bool = True,
    color_grade: str = "",
    scene_idx: int = 0,
    scene_title: str = "",
) -> bool:
    """
    Combina imagen + audio en clip mp4.
    AÃ±ade fade-in / fade-out si fade=True y audio tiene duraciÃ³n detectable.
    """
    if not os.path.isfile(FFMPEG_EXE):
        log.error(f"[VideoStudio] ffmpeg no encontrado en {FFMPEG_EXE}")
        return False

    try:
        has_audio = audio_path and os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0

        # Detectar duración del audio para calcular fade-out offset
        audio_dur = SECONDS_PER_SCENE
        if has_audio:
            try:
                probe = subprocess.run(
                    [FFMPEG_EXE, "-i", audio_path],
                    capture_output=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in probe.stderr.decode(errors="replace").splitlines():
                    if "Duration:" in line:
                        t = line.split("Duration:")[1].split(",")[0].strip()
                        h, m, s = t.split(":")
                        audio_dur = int(h)*3600 + int(m)*60 + float(s)
                        break
            except Exception:
                pass

        if duration_mode == "manual":
            clip_dur = float(scene_duration)
        else:
            clip_dur = audio_dur + 0.5 if has_audio else float(scene_duration)
        fade_d     = min(FADE_DURATION, clip_dur / 3) if fade else 0.0
        fade_out_t = max(0, clip_dur - fade_d)

        # Extraer resolucion
        w_val, h_val = DEFAULT_IMG_W, DEFAULT_IMG_H
        if "x" in resolution:
            parts = resolution.split("x")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                w_val, h_val = int(parts[0]), int(parts[1])

        # Filtro de video con fade
        if ken_burns and not (subtitles and text):
            # Ken Burns: zoompan (no compatible con subtitles en misma cadena)
            vf_parts = [_kenburns_vf(clip_dur, fps, w_val, h_val, scene_idx)]
        else:
            vf_parts = [
                f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease",
                f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black",
                f"fps={fps}",
            ]
        if color_grade:
            vf_parts.append(color_grade)

        # VFX de grano de pelicula sutil para cohesion visual
        vf_parts.append("noise=alls=7:allf=t+u")

        if subtitles and text:
            def fmt_time(s: float) -> str:
                ms = int((s % 1) * 1000)
                m, s_int = divmod(int(s), 60)
                _h, _m = divmod(m, 60)
                return f"{_h:02d}:{_m:02d}:{s_int:02d},{ms:03d}"

            job_dir = os.path.dirname(image_path)
            scene_name = os.path.splitext(os.path.basename(image_path))[0]
            srt_path = os.path.join(job_dir, f"{scene_name}.srt")
            with open(srt_path, "w", encoding="utf-8") as srt_f:
                srt_f.write(f"1\n00:00:00,000 --> {fmt_time(clip_dur)}\n{text}\n")

            safe_srt = srt_path.replace('\\', '/').replace(':', '\\:')
            vf_parts.append(f"subtitles='{safe_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=20'")

        # -- Cinematic Scene Title Overlay --
        if scene_title:
            safe_t = scene_title.replace("'", "").replace(":", "").replace("%", "")[:40].upper()
            draw_t = (
                f"drawtext=text='{safe_t}':fontcolor=white@0.7:fontsize={h_val//22}:"
                f"x=50:y=h-100:fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
                f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,3.5),1,if(lt(t,4.2),1-(t-3.5)/0.7,0)))'"
            )
            vf_parts.append(draw_t)

        if fade and fade_d > 0:
            vf_parts.append(f"fade=t=in:st=0:d={fade_d}")
            vf_parts.append(f"fade=t=out:st={fade_out_t:.3f}:d={fade_d}")
        vf = ",".join(vf_parts)

        if has_audio:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-i",  audio_path,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k"
            ]
            if duration_mode == "manual":
                cmd.extend(["-t", str(scene_duration)])
            else:
                cmd.append("-shortest")

            cmd.extend([
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ])
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(scene_duration),
                "-c:v", codec, "-preset", "fast",
                "-vf", vf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_mp4,
            ]

        result = subprocess.run(
            cmd, capture_output=True, timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and os.path.isfile(output_mp4):
            log.info(f"[VideoStudio] Clip: {os.path.basename(output_mp4)}")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-400:]
            log.error(f"[VideoStudio] ffmpeg error clip: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error ensamblando clip: {e}")
        return False


# -- Paso 6: Concatenacion final ------------------------------------------


# -- BGM local: generacion instrumental sin internet ----------------------

def _ensure_bgm(bgm_type: str, bgm_path: str) -> bool:
    # Genera BGM instrumental con ffmpeg aevalsrc. Sin internet. Cache en inputs/.
    if os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096:
        return True
    if bgm_type not in BGM_GENERATORS:
        log.warning('[VideoStudio] BGM tipo desconocido: ' + bgm_type)
        return False
    if not os.path.isfile(FFMPEG_EXE):
        log.error('[VideoStudio] ffmpeg no encontrado para generar BGM.')
        return False
    parent_dir = os.path.dirname(os.path.abspath(bgm_path))
    os.makedirs(parent_dir, exist_ok=True)
    dur = 600
    expr = BGM_GENERATORS[bgm_type]
    aevalsrc_arg = expr + ':c=stereo:sample_rate=44100:d=' + str(dur)
    fade_out_st = dur - 4
    cmd = [
        FFMPEG_EXE, '-y',
        '-f', 'lavfi', '-i', 'aevalsrc=' + aevalsrc_arg,
        '-af', 'volume=0.45,afade=t=in:st=0:d=4,afade=t=out:st=' + str(fade_out_st) + ':d=4',
        '-ar', '44100', '-ac', '2',
        '-c:a', 'libmp3lame', '-b:a', '128k',
        '-t', str(dur),
        bgm_path,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096:
            size_kb = os.path.getsize(bgm_path) // 1024
            log.info('[VideoStudio] BGM generado localmente (' + str(size_kb) + ' KB): ' + os.path.basename(bgm_path))
            return True
        err = result.stderr.decode(errors='replace')[-400:]
        log.error('[VideoStudio] Error generando BGM ' + bgm_type + ': ' + err)
        return False
    except Exception as e:
        log.error('[VideoStudio] Excepcion generando BGM: ' + str(e))
        return False


def _concatenate_clips(clip_paths: list[str], output_mp4: str, bgm_type: str = "ninguna", bgm_volume: float = 0.1, codec: str = "libx264") -> bool:
    """Concatena todos los clips en el video final."""
    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_mp4)
        return True

    try:
        list_file = output_mp4 + ".list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                safe = cp.replace("'", "'\\''")
                f.write(f"file '{safe}'\n")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bgm_path = os.path.join(base_dir, "inputs", f"bgm_{bgm_type.lower()}.mp3")
        
        if bgm_type != "ninguna" and not (os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096):
            _ensure_bgm(bgm_type, bgm_path)
        has_bgm = bgm_type != "ninguna" and os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096
        
        if has_bgm:
            # anullsrc garantiza que el stream de video concatenado siempre tiene audio,
            # incluso si algún clip individual no tiene stream de audio (p.ej. sin TTS).
            # Flujo:
            #   [0:v] → video concatenado tal cual
            #   [0:a] → audio del concat (puede tener huecos) → se parchea con anullsrc
            #   [bgm] → música de fondo con volumen ajustado
            #   amix mezcla narración + bgm
            # Audio Ducking: La música (input 1) baja automáticamente cuando hay voz (input 0)
            # Threshold=0.1: Sensibilidad al habla | Ratio=5: Nivel de reducción | Attack/Release: Suavidad
            filter_str = (
                f"anullsrc=channel_layout=stereo:sample_rate=44100[silence];"
                f"[0:a][silence]amix=inputs=2:duration=longest[narr];"
                f""
                f"[narr][1:a]sidechaincompress=threshold=0.1:ratio=5:attack=200:release=1000[bgm_ducked];"
                f"[bgm_ducked]volume={bgm_volume}[bgm_final];"
                f"[narr][bgm_final]amix=inputs=2:duration=first:dropout_transition=3[a]"
            )
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-stream_loop", "-1", "-i", bgm_path,
                "-filter_complex", filter_str,
                "-map", "0:v", "-map", "[a]",
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] Concatenando {len(clip_paths)} clips con MIX MUSICAL ({bgm_type}) -> {os.path.basename(output_mp4)}")
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] Concatenando {len(clip_paths)} clips simples -> {os.path.basename(output_mp4)}")
        
        result = subprocess.run(
            cmd, capture_output=True, timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        try:
            os.remove(list_file)
        except Exception:
            pass

        if result.returncode == 0 and os.path.isfile(output_mp4):
            size_mb = os.path.getsize(output_mp4) / 1024 / 1024
            log.info(f"[VideoStudio] Video final: {os.path.basename(output_mp4)} ({size_mb:.1f} MB)")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-400:]
            log.error(f"[VideoStudio] ConcatenaciÃ³n fallida: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error concatenando: {e}")
        return False


# â”€â”€ Actualizador de estado en DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _update_job(job_id: int, **kwargs) -> None:
    valid  = {"status", "progress", "current_step", "output_path",
              "error", "started_at", "finished_at", "thumbnail_path"}
    fields = {k: v for k, v in kwargs.items() if k in valid}
    if not fields:
        return
    sql    = "UPDATE video_jobs SET " + ", ".join(f"{k}=?" for k in fields)
    sql   += " WHERE id=?"
    values = list(fields.values()) + [job_id]
    conn   = sqlite3.connect(DB_PATH)
    conn.execute(sql, values)
    conn.commit()
    conn.close()


def _check_cancelled(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    status = conn.execute("SELECT status FROM video_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    if status and status[0] == 'cancelled':
        raise RuntimeError("Proceso cancelado por el usuario.")

# â”€â”€ Worker principal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _process_job(
    job_id: int,
    topic: str,
    n_scenes: int,
    voice_speed: int,
    voice_id: str,
    style: str,
    narration_lang: str,
    transitions: bool,
    resolution: str,
    subtitles: bool,
    title: str = "",
    bgm_type: str = "ninguna",
    quality: str = "hd",
    use_lore: bool = True,
    fps: int = DEFAULT_FPS,
    scene_duration: int = SECONDS_PER_SCENE,
    duration_mode: str = "auto",
    bgm_volume: float = DEFAULT_BGM_VOLUME,
    codec: str = "libx264",
    ken_burns: bool = True,
    intro_card: bool = False,
    color_grade: str = "auto",
) -> None:
    """
    Pipeline completo con Character Consistency Engine.
    """
    global _current_job

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _update_job(job_id, status="running", started_at=now, progress=0,
                current_step="Generando guiÃ³n con el LLM...")
    with _lock:
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
        }

    job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    # Seed base del job: determinista por job_id + topic â†’ coherencia visual
    job_seed = int(hashlib.md5(f"{job_id}:{topic}".encode()).hexdigest()[:8], 16) % 2147483647

    try:
        _check_cancelled(job_id)
        # â”€â”€ PASO 1: GuiÃ³n + Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        scenes, visual_anchor = _generate_script(topic, n_scenes, style, narration_lang, use_lore)
        if not scenes:
            raise RuntimeError("El LLM no devolviÃ³ escenas vÃ¡lidas.")

        style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
        style_prefix = style_info["prefix"]
        log.info(f"[VideoStudio] Visual Anchor del job #{job_id}: '{visual_anchor[:80]}'")

        # -- Grading de color efectivo
        effective_grade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')

        total_steps = n_scenes * 3 + 1
        step        = 0
        clip_paths: list[str] = []

        # -- Intro card opcional
        if intro_card:
            intro_path = os.path.join(job_dir, 'intro_card.mp4')
            w_ic, h_ic = DEFAULT_IMG_W, DEFAULT_IMG_H
            if 'x' in resolution:
                _p = resolution.split('x')
                if len(_p) == 2 and _p[0].isdigit() and _p[1].isdigit():
                    w_ic, h_ic = int(_p[0]), int(_p[1])
            if _create_title_card(title or topic[:50], style_prefix[:60], intro_path, w_ic, h_ic, fps, 3.5, codec):
                clip_paths.insert(0, intro_path)

        for i, scene in enumerate(scenes):
            scene_num   = i + 1
            scene_title = scene.get("title", f"Escena {scene_num}")
            narration   = scene.get("narration", "")

            # â”€â”€ Construir prompt con anchor garantizado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            raw_prompt      = scene.get("image_prompt", topic)
            anchored_prompt = (
                f"{visual_anchor}, {raw_prompt}, {style_prefix}"
                if visual_anchor.lower() not in raw_prompt.lower()
                else f"{raw_prompt}, {style_prefix}"
            )
            # Truncar a 450 chars para evitar encode overflows en Pollinations
            anchored_prompt = anchored_prompt[:450]

            # â”€â”€ PASO 2: Imagen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            _check_cancelled(job_id)
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando imagen: {scene_title[:40]}")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["current_step"] = f"[{scene_num}/{n_scenes}] Generando imagen..."
                    _current_job["current_scene"] = scene_num

            img_path = _generate_scene_image(anchored_prompt, scene_num, job_id, job_seed, style, resolution)

            if not img_path:
                placeholder = os.path.join(job_dir, f"scene_{scene_num:02d}_placeholder.png")
                _create_placeholder_image(scene_title, placeholder)
                img_path = placeholder

            # â”€â”€ PASO 3: TTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            _check_cancelled(job_id)
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando audio: {scene_title[:40]}")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["current_step"] = f"[{scene_num}/{n_scenes}] Generando audio..."
                    _current_job["current_scene"] = scene_num

            audio_path = os.path.join(job_dir, f"scene_{scene_num:02d}_audio.wav")
            audio_ok   = _generate_audio(narration, audio_path, voice_speed, voice_id) if narration else False

            # â”€â”€ PASO 4: Clip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            _check_cancelled(job_id)
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Ensamblando clip...")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["current_step"] = f"[{scene_num}/{n_scenes}] Ensamblando clip..."
                    _current_job["current_scene"] = scene_num

            clip_path = os.path.join(job_dir, f"scene_{scene_num:02d}_clip.mp4")
            # Color Grading Emocional Combinado
            base_grade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')
            scene_mood = scene.get("mood", "neutral").lower()
            mood_grade = EMOTIONAL_GRADES.get(scene_mood, "")
            _cgrade    = f"{base_grade},{mood_grade}" if base_grade and mood_grade else (base_grade or mood_grade)
            if _assemble_clip(img_path, audio_path if audio_ok else None, clip_path, fade=transitions, resolution=resolution, text=narration, subtitles=subtitles, fps=fps, scene_duration=scene_duration, duration_mode=duration_mode, codec=codec, ken_burns=ken_burns, color_grade=_cgrade, scene_idx=scene_num, scene_title=scene_title):
                clip_paths.append(clip_path)
                with _lock:
                    if _current_job and scene_num not in _current_job.get("scenes_done", []):
                        _current_job.setdefault("scenes_done", []).append(scene_num)
            else:
                raise RuntimeError(f"Error al ensamblar el clip de la escena {scene_num}.")

        # â”€â”€ PASO 5: Video final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _update_job(job_id, progress=95, current_step="Concatenando clips en video final...")
        with _lock:
            if _current_job:
                _current_job["progress"] = 95
                _current_job["current_step"] = "Concatenando video final..."

        ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        final_path = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_{ts}.mp4")

        if clip_paths and _concatenate_clips(clip_paths, final_path, bgm_type, bgm_volume, codec):
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _update_job(job_id, status="done", progress=100,
                        current_step="Completado", output_path=final_path,
                        finished_at=now)
            log.info(f"[VideoStudio] Job #{job_id} completado -> {final_path}")
            # -- Thumbnail
            thumb_path = os.path.join(OUTPUT_DIR, f'thumb_{job_id}.jpg')
            if _extract_thumbnail(final_path, thumb_path):
                _update_job(job_id, thumbnail_path=thumb_path)
                log.info(f'[VideoStudio] Thumbnail: {os.path.basename(thumb_path)}')
            
            if use_lore:
                try:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    inputs_dir = os.path.join(base_dir, "inputs")
                    os.makedirs(inputs_dir, exist_ok=True)
                    lore_path = os.path.join(inputs_dir, "cinematic_lore.txt")
                    with open(lore_path, "a", encoding="utf-8") as f:
                        f.write(f"\n\n=== HISTORIA: {title or topic} ===\n")
                        for s in scenes:
                            f.write(f"Escena: {s.get('title', '')}\n")
                            f.write(f"Narración: {s.get('narration', '')}\n")
                except Exception as e:
                    log.warning(f"[VideoStudio] Error guardando lore: {e}")
        else:
            raise RuntimeError("No se pudieron generar clips.")

    except Exception as e:
        if str(e) == "Proceso cancelado por el usuario.":
            log.info(f"[VideoStudio] Job #{job_id} detenido exitosamente por cancelación.")
        else:
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _update_job(job_id, status="failed", error=str(e), finished_at=now,
                        current_step="Error")
            log.error(f"[VideoStudio] Job #{job_id} falló: {e}")
    finally:
        with _lock:
            _current_job = None


# â”€â”€ Imagen de marcador â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _create_placeholder_image(text: str, output_path: str) -> None:
    """Genera imagen negra con texto usando Pillow como placeholder."""
    try:
        from PIL import Image, ImageDraw
        img  = Image.new("RGB", (DEFAULT_IMG_W, DEFAULT_IMG_H), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        draw.text((DEFAULT_IMG_W // 2, DEFAULT_IMG_H // 2),
                  text[:80], fill=(100, 100, 140), anchor="mm")
        img.save(output_path, "PNG")
    except Exception:
        with open(output_path, "wb") as f:
            f.write(bytes([
                0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,
                0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,
                0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
                0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
                0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,
                0x54,0x08,0xD7,0x63,0xF8,0xCF,0xC0,0x00,
                0x00,0x00,0x02,0x00,0x01,0xE2,0x21,0xBC,
                0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,
                0x44,0xAE,0x42,0x60,0x82,
            ]))


# â”€â”€ Worker daemon â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _worker_loop() -> None:
    """Loop daemon: toma el siguiente job pendiente y lo procesa."""
    _init_db()
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            row  = conn.execute(
                "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id LIMIT 1"
            ).fetchone()
            conn.close()

            if row:
                keys = row.keys()
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
            else:
                time.sleep(5)

        except Exception as e:
            log.error(f"[VideoStudio] Error en worker loop: {e}")
            time.sleep(10)


def start() -> None:
    """Inicia el worker daemon de video si no estaba ya corriendo."""
    global _started
    if _started:
        return
    _started = True
    _init_db()
    t = threading.Thread(target=_worker_loop, name="GravityVideoWorker", daemon=True)
    t.start()
    log.info("[VideoStudio] Worker daemon iniciado (Gravity Studio ULTRA V12.1 - Audio Ducking & VFX Active).")


# â”€â”€ API pÃºblica â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_video_url(output_path: str) -> str:
    """Convierte ruta absoluta en URL relativa para descarga."""
    if not output_path:
        return ""
    fname = os.path.basename(output_path)
    return f"/v1/video/download?file={fname}"

