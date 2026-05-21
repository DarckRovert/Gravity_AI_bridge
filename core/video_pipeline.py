
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
"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  GRAVITY AI â€” VIDEO STUDIO PIPELINE V15.0 PRO CINEMATIC EDITION                  â•‘
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
import re
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
REMOTION_FPS       = 30  # FPS fijo de las composiciones Remotion (Root.tsx)
DEFAULT_BGM_VOLUME = 0.1   # volumen relativo de la música de fondo (0.0-1.0)

# ── Generadores de BGM locales (sin internet) ─────────────────────────────────
# Ruido marrón/rosa con filtros paso-bajo para crear "rumble" cinemático (drone ambient)
BGM_GENERATORS: dict[str, str] = {
    "epico":        "anoisesrc=color=brown:r=44100:a=0.5,lowpass=f=120,chorus=0.5:0.9:50:0.4:0.25:2",
    "documental":   "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=300",
    "synthwave":    "anoisesrc=color=brown:r=44100:a=0.4,lowpass=f=400,tremolo=f=4:d=0.5",
    "jazz":         "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=250",
    "cinematic":    "anoisesrc=color=brown:r=44100:a=0.6,lowpass=f=80,aecho=0.8:0.88:60:0.4",
    "publicitario": "anoisesrc=color=pink:r=44100:a=0.3,lowpass=f=350,tremolo=f=2:d=0.3",
    "heroico":      "anoisesrc=color=brown:r=44100:a=0.5,lowpass=f=100",
    "ambient":      "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=150",
    "tension":      "anoisesrc=color=brown:r=44100:a=0.4,lowpass=f=60",
    "triste":       "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=200",
    "misterio":     "anoisesrc=color=brown:r=44100:a=0.3,lowpass=f=90",
    "alegre":       "anoisesrc=color=pink:r=44100:a=0.25,lowpass=f=400",
    "lofi_beats":   "anoisesrc=color=pink:r=44100:a=0.2,lowpass=f=250",
    "corporativo":  "anoisesrc=color=pink:r=44100:a=0.15,lowpass=f=300",
    "ninguna":      "anullsrc=r=44100:cl=stereo"
}

_branding_cache = None
def _get_branding_config() -> dict:
    global _branding_cache
    if _branding_cache is None:
        try:
            import yaml
            with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                _branding_cache = (yaml.safe_load(f) or {}).get("branding", {})
        except Exception:
            _branding_cache = {}
    return _branding_cache


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
_db_initialized = False

# Cache de voces SAPI (TTL 300s) — evita enumerar COM en cada polling del dashboard
_voices_cache: list[dict] = []
_voices_cache_ts: float   = 0.0
_VOICES_CACHE_TTL: float  = 300.0   # segundos

# Timeout de conexion SQLite (WAL mode activo en _init_db)
DB_CONNECT_TIMEOUT: int = 15


# ── Base de datos ─────────────────────────────────────────────────────────────

def _init_db() -> None:
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
    conn.execute("PRAGMA journal_mode=WAL")  # Permite lecturas concurrentes sin bloqueos
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
        ("ken_burns",         "INTEGER NOT NULL DEFAULT 1"),
        ("intro_card",        "INTEGER NOT NULL DEFAULT 0"),
        ("color_grade",       "TEXT NOT NULL DEFAULT 'auto'"),
        ("thumbnail_path",    "TEXT NOT NULL DEFAULT ''"),
        ("animation_effect",  "TEXT NOT NULL DEFAULT 'auto'"),
        ("animation_level",   "INTEGER NOT NULL DEFAULT 1"),
        # ── YouTube monetización
        ("youtube_video_id",  "TEXT NOT NULL DEFAULT ''"),
        ("youtube_url",       "TEXT NOT NULL DEFAULT ''"),
        ("uploaded_at",       "TEXT NOT NULL DEFAULT ''"),
        ("upload_status",     "TEXT NOT NULL DEFAULT 'pending'"),
        ("shorts_path",       "TEXT NOT NULL DEFAULT ''"),
        ("shorts_video_id",   "TEXT NOT NULL DEFAULT ''"),
        ("seo_tags",          "TEXT NOT NULL DEFAULT ''"),
        ("seo_description",   "TEXT NOT NULL DEFAULT ''"),
        # ── Multi-canal
        ("niche_id",          "TEXT NOT NULL DEFAULT ''"),
        ("cloned_from",       "INTEGER NOT NULL DEFAULT 0"),
        ("clone_lang",        "TEXT NOT NULL DEFAULT ''"),
    ]
    for col_name, col_def in migrations:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE video_jobs ADD COLUMN {col_name} {col_def}")
    conn.commit()

    # ── Crash Recovery: jobs atascados en 'running' de sesiones anteriores ──────
    # Si el servidor murió mientras procesaba un job, lo resetea a 'failed'
    # para que no bloquee la cola en el próximo arranque.
    try:
        stuck = conn.execute(
            "SELECT COUNT(*) FROM video_jobs WHERE status='running'"
        ).fetchone()[0]
        if stuck > 0:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            conn.execute(
                "UPDATE video_jobs SET status='failed', "
                "error='Proceso interrumpido por reinicio del servidor', "
                "finished_at=? WHERE status='running'",
                (now_iso,)
            )
            conn.commit()
            log.warning(f"[VideoStudio] Crash recovery: {stuck} job(s) en 'running' reseteados a 'failed'.")
    except Exception as _cr_e:
        log.debug(f"[VideoStudio] Crash recovery skip: {_cr_e}")

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
    ken_burns: bool        = True,
    intro_card: bool       = False,
    color_grade: str       = "auto",
    animation_effect: str  = "auto",
    animation_level: int   = 1,
    niche_id: str          = "",
) -> int:
    """Encola un nuevo trabajo de video. Retorna el ID generado."""
    _init_db()
    
    # Inyectar default animation_level desde config si no fue forzado explícitamente a algo distinto de 1
    if animation_level == 1:
        try:
            import yaml
            with open(os.path.join(BASE_DIR, 'config.yaml'), 'r', encoding='utf-8') as _fc:
                _cfg_c = yaml.safe_load(_fc) or {}
                animation_level = int(_cfg_c.get('comfyui', {}).get('animation_level', 1))
        except Exception:
            pass

    if style not in CINEMA_STYLES:
        style = DEFAULT_STYLE
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
    cur  = conn.execute(
        "INSERT INTO video_jobs "
        "(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, "
        " resolution, subtitles, title, bgm_type, quality, use_lore, fps, scene_duration, "
        " duration_mode, bgm_volume, codec, ken_burns, intro_card, color_grade, "
        " animation_effect, animation_level, niche_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            topic, n_scenes, voice_speed, voice_id, style, narration_lang,
            1 if transitions else 0, resolution, 1 if subtitles else 0,
            title, bgm_type, quality, 1 if use_lore else 0,
            fps, scene_duration, duration_mode, float(bgm_volume), codec,
            1 if ken_burns else 0, 1 if intro_card else 0, color_grade,
            animation_effect, int(animation_level), niche_id, now
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
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
    conn.row_factory = sqlite3.Row
    pending  = [dict(r) for r in conn.execute(
        "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id"
    ).fetchall()]
    
    raw_history = conn.execute(
        "SELECT * FROM video_jobs WHERE status NOT IN ('pending', 'deleted') ORDER BY id DESC LIMIT ?",
        (MAX_HISTORY,)
    ).fetchall()
    conn.close()

    # Purga: jobs done cuyo archivo físico ya no existe.
    # FIX: conexión separada para el UPDATE — evita OperationalError cuando
    # la primera conexión todavía retiene el cursor del fetchall en memoria.
    history = []
    purge_ids: list[int] = []
    for r in raw_history:
        job_dict = dict(r)
        if job_dict.get('status') in ('done', 'completed') and job_dict.get('output_path'):
            if not os.path.isfile(job_dict['output_path']):
                purge_ids.append(job_dict['id'])
                continue
        history.append(job_dict)

    if purge_ids:
        try:
            _pc = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
            for _pid in purge_ids:
                _pc.execute("UPDATE video_jobs SET status='deleted', output_path=NULL WHERE id=?", (_pid,))
            _pc.commit()
            _pc.close()
        except Exception as _pe:
            log.debug(f"[VideoStudio] Purge batch error: {_pe}")

    with _lock:
        current = _current_job

    # Aggregate stats from DB (all-time)
    try:
        _sc = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
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
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
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
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
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
    Cache con TTL de 300s — evita enumerar COM en cada polling del dashboard.
    """
    global _voices_cache, _voices_cache_ts
    now_ts = time.time()
    if _voices_cache and (now_ts - _voices_cache_ts) < _VOICES_CACHE_TTL:
        return list(_voices_cache)

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
            import pythoncom
            pythoncom.CoInitialize()
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
            import pythoncom
            pythoncom.CoInitialize()
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

    # Actualizar cache — próximas llamadas dentro de 300s no re-enumeran SAPI
    _voices_cache    = list(v_list)
    _voices_cache_ts = time.time()
    return v_list


# â”€â”€ Paso 1: ExtracciÃ³n de Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _extract_visual_anchor(topic: str) -> str:
    """
    Usa el LLM para extraer un descriptor visual conciso y consistente del tema.
    """
    system_prompt = (
        "You are an expert visual director and prompt engineer for AI image generation. "
        "Respond ONLY with a single compact English phrase. No bullet points, no JSON."
    )
    user_prompt = (
        f"Given the story/documentary/ad topic or web content: '{topic}'\n"
        "Extract a VISUAL CHARACTER/SUBJECT ANCHOR — a compact description of the main "
        "subject's permanent visual attributes (e.g., specific setting, brand colors, "
        "character features, or main product). This anchor will be prepended to every scene prompt to maintain "
        "visual consistency across all generated images.\n"
        "If the input contains EXTRACTED WEB CONTENT, deduce the core product or business (e.g., 'a vibrant Mexican food stall with neon signs', 'a sleek modern tech office').\n"
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


def _get_scene_visual_context(image_path: str) -> str:
    """
    Extrae tags visuales de la escena N-1 para mantener consistencia visual en la escena N
    utilizando WD14 Tagger via ComfyUI.
    """
    try:
        from _integrations.comfy_client import ComfyUIClient
        client = ComfyUIClient()
        if not client.is_online():
            return ""

        workflow_path = os.path.join(BASE_DIR, "_integrations", "workflow_img2prompt.json")
        if not os.path.exists(workflow_path):
            return ""

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # Actualizar ruta de imagen (el nodo LoadImage en ComfyUI lee archivos locales si se le da ruta absoluta o los copia a input)
        # Nota: LoadImage en ComfyUI portable usualmente requiere que la imagen esté en la carpeta 'input'. 
        # Para forzar ruta absoluta se puede usar LoadImage absolute path custom node, pero para evitar dependencias,
        # copiaremos la imagen al dir input de ComfyUI.
        import shutil
        input_dir = os.path.join(BASE_DIR, "_integrations", "ComfyUI_windows_portable", "ComfyUI", "input")
        if not os.path.exists(input_dir):
            os.makedirs(input_dir, exist_ok=True)
        img_name = f"img2prompt_{os.path.basename(image_path)}"
        shutil.copy2(image_path, os.path.join(input_dir, img_name))
        
        workflow["1"]["inputs"]["image"] = img_name

        prompt_id = client.queue_prompt(workflow)
        
        # Esperar finalización (timeout corto, si el tagger tarda más de 30s fallamos rápido)
        elapsed = 0
        while elapsed < 30:
            tags = client.extract_tags(prompt_id)
            if tags:
                try: os.remove(os.path.join(input_dir, img_name))
                except: pass
                # El tagger de pysssss devuelve a veces una lista de tags unidos por comas en el primer elemento
                if len(tags) == 1 and isinstance(tags[0], str):
                    return tags[0]
                return ", ".join(tags)
            time.sleep(2)
            elapsed += 2
            
    except Exception as e:
        log.debug(f"[VideoStudio] Error en img2prompt (ComfyUI offline/Tagger fail): {e}")
    return ""


# ── Paso 2: Generación de guión via LLM ──────────────────────────────────────

def _normalize_topic_for_lore(topic: str) -> str:
    """
    Normaliza un topic para búsqueda en el lore:
    - Elimina indicadores de parte/continuación ('parte 2', 'part ii', 'capitulo 3', etc.)
    - Convierte a minúsculas y elimina espacios extra.
    """

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

            # Coincidencia estricta y segura para evitar cruce de lores:
            if not header_norm or len(header_norm) < 4:
                continue

            match = False
            if clean_topic == header_norm:
                match = True
            elif len(clean_topic) >= 5 and len(header_norm) >= 5:
                # Contención mutua estricta
                if clean_topic in header_norm or header_norm in clean_topic:
                    match = True

            if match:
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


def _generate_script(topic: str, n_scenes: int, style: str, narration_lang: str, use_lore: bool = True) -> tuple[list[dict], str, str]:
    """
    Genera guión estructurado incorporando contexto de lore previo y un título global.
    """
    original_topic = topic
    urls = re.findall(r'(https?://\S+)', topic)
    scraped_successfully = False
    
    if urls:
        try:
            from core.firecrawl_scraper import scrape_url
            for url in urls[:1]:
                if "youtube.com" in url or "youtu.be" in url:
                    log.info("[VideoStudio] URL de YouTube detectada. Obteniendo título oficial vía oEmbed para enlazar lore...")
                    try:
                        import requests
                        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                        res = requests.get(oembed_url, timeout=5)
                        if res.status_code == 200:
                            yt_data = res.json()
                            yt_title = yt_data.get("title", "")
                            if yt_title:
                                topic = topic.replace(url, f"{yt_title}")
                                original_topic = topic # Actualizar para que _get_lore_context lo encuentre
                                log.info(f"[VideoStudio] Título de YouTube recuperado: '{yt_title}'")
                                # No seteamos scraped_successfully = True para forzar que DuckDuckGo investigue el título
                    except Exception as yt_e:
                        log.warning(f"[VideoStudio] Error obteniendo oEmbed de YouTube: {yt_e}")
                    break
                    
                log.info(f"[VideoStudio] URL detectada en topic. Raspando: {url}")
                # Leemos api_key de config.yaml temporalmente
                api_key = ""
                try:
                    import yaml
                    with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                        api_key = cfg.get("firecrawl_api_key", "")
                except Exception as _cfg_e:
                    log.debug(f"[VideoStudio] No se pudo leer firecrawl_api_key: {_cfg_e}")
                
                scrape_res = scrape_url(url, api_key=api_key)
                if scrape_res.get("ok"):
                    scraped_text = scrape_res.get("content", "")[:4000]
                    topic = topic.replace(url, f"[{url} - CONTENIDO WEB EXTRAÍDO:\n{scraped_text}\n]")
                    log.info("[VideoStudio] URL Raspada e inyectada con éxito en el guion.")
                    scraped_successfully = True
        except Exception as e:
            log.warning(f"[VideoStudio] Error raspando URL: {e}")
            
    if not scraped_successfully:
        # Auto-investigación inteligente (conocimiento previo) o fallback para YouTube
        try:
            from core.web_search import search_and_scrape
            log.info(f"[VideoStudio] Investigando en internet sobre: '{original_topic[:50]}' para nutrir el guion...")
            knowledge = search_and_scrape(original_topic, max_results=2)
            if knowledge:
                topic = f"{topic}\n\n[CONOCIMIENTO OBTENIDO DE INTERNET PARA CONTEXTO Y PRECISIÓN:\n{knowledge}\n]"
                log.info("[VideoStudio] Conocimiento inyectado exitosamente en el guion.")
        except Exception as e:
            log.warning(f"[VideoStudio] Error en auto-investigación web: {e}")

        # Análisis de mercado y competidores (Hack 4)
        try:
            from core.market_researcher import analyze_competitors
            competitor_brief = analyze_competitors(original_topic)
            if competitor_brief:
                topic = f"{topic}{competitor_brief}"
        except Exception as e:
            log.warning(f"[VideoStudio] Error en análisis de mercado: {e}")
    style_info     = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    style_prefix   = style_info["prefix"]
    
    lore_context = ""
    if use_lore:
        lore_context = _get_lore_context(original_topic)
        if lore_context:
            log.info(f"[VideoStudio] Contexto de Lore recuperado ({len(lore_context)} chars)")

    lang_names = {
        "es": "español", "en": "English", "pt": "português",
        "fr": "français", "de": "Deutsch", "it": "italiano",
    }
    lang_label = lang_names.get(narration_lang, "español")

    system_prompt = (
        "Eres un director creativo y guionista profesional de cine, documentales y publicidad. "
        "Tu objetivo es crear narrativas visuales y auditivas que cautiven al espectador. "
        "Responde ÚNICAMENTE con JSON válido, sin texto adicional."
    )
    
    user_prompt = (
        f"Crea un guión de {n_scenes} escenas para un video sobre el siguiente tema o contenido: '{topic}'.\n"
        "Si detectas CONOCIMIENTO OBTENIDO DE INTERNET, compórtate como un investigador experto: utiliza la "
        "información factual, datos precisos y contexto proporcionado para hacer que el guion sea "
        "veraz, rico en detalles y sumamente informativo sin perder el tono narrativo.\n"
        "Si detectas CONTENIDO WEB EXTRAÍDO (por URL directa), compórtate como un experto publicista: analiza "
        "los servicios, productos o menú ofrecidos y diseña un guión altamente persuasivo.\n"
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
        "REGLA CRÍTICA DE NARRACIÓN: El campo 'narration' DEBE contener ÚNICAMENTE lo que dirá el "
        "locutor en voz en off. DEBE ser una historia fluida o un texto publicitario atrapante. "
        "PROHIBIDO incluir metadatos como 'Escena 1', 'Imagen:', 'Título:', o direcciones de cámara. "
        "Solo el diálogo hablado puro y continuo.\n\n"
        "Responde con este JSON exacto (sin ningún texto antes o después):\n"
        "{\n"
        '  "video_title": "Un título global creativo, comercial y atractivo para todo el video",\n'
        '  "scenes": [\n'
        "    {\n"
        '      "title": "Título de escena MUY CORTO",\n'
        '      "character_anchor": "Descripción compacta en inglés del sujeto principal con atributos físicos fijos",\n'
        '      "image_prompt": "Descripción visual detallada en inglés. DEBE incluir el character_anchor al inicio.",\n'
        f'      "narration": "Texto de narración en {lang_label} para esta escena (2-4 oraciones)."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        f"Genera exactamente {n_scenes} escenas dentro del array 'scenes'. Solo JSON, nada más."
    )

    try:
        from core import provider_manager
        from core.multi_agent import PipelineStep, run_pipeline
        import yaml
        
        # Leer configuración de Multi-Agentes
        writer_prov, writer_mod = None, None
        audit_prov, audit_mod = None, None
        
        try:
            with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                ar = cfg.get("agent_routing", {})
                if ar.get("coder"):
                    writer_prov = ar["coder"].get("provider")
                    writer_mod = ar["coder"].get("model")
                if ar.get("auditor"):
                    audit_prov = ar["auditor"].get("provider")
                    audit_mod = ar["auditor"].get("model")
        except Exception:
            pass
            
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No hay proveedor LLM activo")
            
        writer_prov = writer_prov or best_result.name
        writer_mod = writer_mod if writer_mod and writer_mod != "auto" else best_model
        
        audit_prov = audit_prov or best_result.name
        audit_mod = audit_mod if audit_mod and audit_mod != "auto" else best_model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        
        log.info(f"[VideoStudio] Iniciando pipeline Multi-Agente para el guion (Escritor: {writer_prov}, Auditor: {audit_prov})...")
        
        steps = [
            PipelineStep(provider=writer_prov, model=writer_mod),
            PipelineStep(provider=audit_prov, model=audit_mod, role="Actúa como un Auditor Experto en Retención de Audiencia. Revisa el JSON anterior. Mejora los ganchos emocionales de la narración en los primeros 5 segundos. Asegúrate de que los image_prompts sean extremadamente cinemáticos y consistentes. Devuelve ÚNICAMENTE EL JSON CORREGIDO, sin explicaciones ni markdown text. Solo JSON puro.")
        ]
        
        content = run_pipeline(steps=steps, initial_messages=messages, options={"temperature": 0.7})

        content = content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.startswith("json"): content = content[4:]
        content = content.strip()

        start = content.find("{")
        end   = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]

        data = json.loads(content)
        scenes = data.get("scenes", [])
        generated_title = data.get("video_title", original_topic[:60])
        
        if isinstance(scenes, list) and len(scenes) > 0:
            anchor = ""
            for sc in scenes:
                ca = sc.get("character_anchor", "").strip()
                if ca and len(ca) > 5:
                    anchor = ca
                    break
            if not anchor:
                anchor = _extract_visual_anchor(topic)
            return scenes[:n_scenes], anchor, generated_title

        raise ValueError("LLM no devolvió lista JSON válida en 'scenes'")

    except Exception as e:
        log.warning(f"[VideoStudio] LLM no disponible ({e}). Fallback con escenas gen\u00e9ricas.")

    # Fallback sin LLM: narraciones descriptivas y rotativas para TTS profesional
    anchor = topic[:120]
    _fallback_narrations = [
        f"En este fascinante recorrido por {original_topic[:60]}, descubriremos aspectos que transformarán tu perspectiva sobre el mundo.",
        f"El tema de {original_topic[:60]} esconde secretos que pocos conocen. Prepárate para una exploración profunda y reveladora.",
        f"Cada detalle de {original_topic[:60]} nos acerca más a comprender fenómenos que moldean nuestra realidad cotidiana.",
        f"La historia detrás de {original_topic[:60]} es más extraordinaria de lo que imaginas. Acompáñanos en este viaje único.",
        f"Analizamos en detalle {original_topic[:60]} con datos precisos y perspectivas que cambiarán tu forma de ver este tema.",
        f"Concluimos nuestra exploración de {original_topic[:60]} con las conclusiones más importantes y lo que significa para el futuro.",
    ]
    scenes = [
        {
            "title":            f"Capítulo {i+1}",
            "character_anchor": anchor,
            "image_prompt":     f"{anchor}, cinematic scene {i+1}, {style_prefix}, high detail, dramatic lighting",
            "narration":        _fallback_narrations[i % len(_fallback_narrations)],
            "mood":             "neutral",
        }
        for i in range(n_scenes)
    ]
    return scenes, anchor, original_topic[:60]

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

    # ── Motor 2: Fooocus (fallback local) ──────────────────────────────────────
    # NOTA: ComfyUI como generador de imagen fija fue eliminado (construía workflow
    # pero nunca llamaba queue_prompt → overhead de red sin resultado).
    # ComfyUI sigue disponible como animador via animation_engine L2.

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
    # ── Intercept: Gemini TTS explícito ──────────────────────────────────────
    if voice_id.startswith("gemini:"):
        gemini_voice = voice_id.split(":", 1)[1]
        try:
            import sys as _sys
            _int_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_integrations")
            if _int_dir not in _sys.path:
                _sys.path.insert(0, _int_dir)
            from gemini_tts import synthesize_gemini, get_api_key_from_gravity
            gemini_key = get_api_key_from_gravity()
            if gemini_key:
                log.info(f"[VideoStudio] TTS Gemini: Generando voz premium '{gemini_voice}'.")
                ok = synthesize_gemini(text, output_wav, voice=gemini_voice, api_key=gemini_key)
                if ok:
                    size_kb = os.path.getsize(output_wav) // 1024
                    log.info(f"[VideoStudio] Audio (Gemini TTS): {os.path.basename(output_wav)} ({size_kb} KB)")
                    return True
                else:
                    log.warning("[VideoStudio] Gemini TTS falló. Intentando fallback SAPI.")
            else:
                log.warning("[VideoStudio] Gemini TTS solicitado pero no hay API key. Intentando fallback SAPI.")
        except Exception as e:
            log.warning(f"[VideoStudio] TTS Gemini error: {e}")

    # ── Motor primario: win32com SAPI (SAPI5 + OneCore + Neural) ─────────────
    if os.name == "nt":
        try:
            import win32com.client
            import pythoncom
            # CoInitialize: solo llamar CoUninitialize si *nosotros* inicializamos el apartment.
            # RPC_E_CHANGED_MODE (0x80010106 / -2147417850) significa que el apartment
            # ya fue inicializado por otro hilo — en ese caso NO hacer CoUninitialize
            # para no desbalancear el contador de referencias COM.
            _co_initialized_by_us = False
            try:
                pythoncom.CoInitialize()
                _co_initialized_by_us = True
            except Exception as _co_err:
                _co_hresult = getattr(_co_err, 'hresult', None) or (getattr(_co_err, 'args', [None]) or [None])[0]
                # 0x80010106 = RPC_E_CHANGED_MODE — ya inicializado, no hacemos nada
                if _co_hresult not in (0x80010106, -2147417850):
                    raise

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
                # Mapeo suavizado: 150 WPM → 0, 180 WPM → 1, 200 WPM → 2, 250 WPM → 4
                sapi.Rate  = max(-10, min(10, int((rate - 150) / 25)))

                os.makedirs(os.path.dirname(output_wav), exist_ok=True)
                file_stream.Open(output_wav, 3)  # SSFMCreateForWrite = 3
                sapi.AudioOutputStream = file_stream
                sapi.Speak(text)
                file_stream.Close()

                ok = os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
                if ok:
                    size_kb = os.path.getsize(output_wav) // 1024
                    log.info(f"[VideoStudio] Audio (win32com): {os.path.basename(output_wav)} ({size_kb} KB)")
                    # Normalizar sample rate: SAPI puede generar a 8/16/24 kHz según la voz.
                    # Sin normalización, FFmpeg embebe esa frecuencia en el clip AAC y
                    # el audio se reproduce acelerado en el video final.
                    _wav_normalized = output_wav + ".norm.wav"
                    try:
                        _nr = subprocess.run(
                            [
                                FFMPEG_EXE, "-y", "-i", output_wav,
                                "-ar", "44100", "-ac", "2", "-sample_fmt", "s16",
                                _wav_normalized,
                            ],
                            capture_output=True, timeout=30,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        if _nr.returncode == 0 and os.path.isfile(_wav_normalized):
                            os.replace(_wav_normalized, output_wav)
                            log.info(f"[VideoStudio] WAV normalizado a 44100Hz: {os.path.basename(output_wav)}")
                        else:
                            log.warning("[VideoStudio] Normalización WAV falló, usando WAV nativo de SAPI.")
                            if os.path.isfile(_wav_normalized):
                                os.remove(_wav_normalized)
                    except Exception as _ne:
                        log.warning(f"[VideoStudio] Normalización WAV excepción: {_ne}")
                    if _co_initialized_by_us:
                        pythoncom.CoUninitialize()
                    return True

            if _co_initialized_by_us:
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
            # Normalizar sample rate: pyttsx3 hereda la frecuencia nativa de la voz SAPI.
            _wav_normalized = output_wav + ".norm.wav"
            try:
                _nr = subprocess.run(
                    [
                        FFMPEG_EXE, "-y", "-i", output_wav,
                        "-ar", "44100", "-ac", "2", "-sample_fmt", "s16",
                        _wav_normalized,
                    ],
                    capture_output=True, timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if _nr.returncode == 0 and os.path.isfile(_wav_normalized):
                    os.replace(_wav_normalized, output_wav)
                    log.info(f"[VideoStudio] WAV normalizado a 44100Hz (pyttsx3): {os.path.basename(output_wav)}")
                else:
                    log.warning("[VideoStudio] Normalización WAV (pyttsx3) falló, usando WAV nativo.")
                    if os.path.isfile(_wav_normalized):
                        os.remove(_wav_normalized)
            except Exception as _ne:
                log.warning(f"[VideoStudio] Normalización WAV (pyttsx3) excepción: {_ne}")
        return ok
    except Exception as e:
        log.error(f"[VideoStudio] Error TTS pyttsx3: {e}")

    # ── Motor Tier-3: Gemini TTS (online, premium, solo si API key configurada) ─
    try:
        import sys as _sys
        _integrations_dir = os.path.join(BASE_DIR, "_integrations")
        if _integrations_dir not in _sys.path:
            _sys.path.insert(0, _integrations_dir)
        from gemini_tts import synthesize_gemini, get_api_key_from_gravity
        gemini_key = get_api_key_from_gravity()
        if gemini_key:
            log.info("[VideoStudio] TTS Gemini: intentando síntesis premium (motor local no disponible).")
            ok = synthesize_gemini(text, output_wav, api_key=gemini_key)
            if ok:
                size_kb = os.path.getsize(output_wav) // 1024
                log.info(f"[VideoStudio] Audio (Gemini TTS): {os.path.basename(output_wav)} ({size_kb} KB)")
                return True
    except Exception as e:
        log.warning(f"[VideoStudio] TTS Gemini error: {e}")

    return False


# â”€â”€ Paso 5: Ensamblado por escena con fade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


# -- Ken Burns: delegado al animation_engine (compatibilidad legacy) ----------

def _kenburns_vf(clip_dur: float, fps: int, w: int, h: int, scene_idx: int) -> str:
    """Wrapper legacy → delega a animation_engine para compatibilidad."""
    from core.animation_engine import build_animation_vf
    return build_animation_vf("kenburns", clip_dur, fps, w, h, scene_idx)


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
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration),
        "-c:v", codec, "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
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
    animation_effect: str = "kenburns",
) -> bool:
    """
    Combina imagen + audio en clip mp4.
    AÃ±ade fade-in / fade-out si fade=True y audio tiene duraciÃ³n detectable.
    """
    if not os.path.isfile(FFMPEG_EXE):
        log.error(f"[VideoStudio] ffmpeg no encontrado en {FFMPEG_EXE}")
        return False

    try:
        # Detectar si el input es un video (L2 ComfyUI) o imagen estática (L0/L1)
        _input_is_video = image_path.lower().endswith((".mp4", ".webm", ".mov", ".avi"))
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

        # ── Filtro de animación: animation_engine gestiona ken_burns y efectos ──
        # FIX BUG ARQUITECTÓNICO: animation_effect recibido directamente como parámetro
        # (eliminado el hack de atributo-en-función que tenía race condition).
        from core.animation_engine import build_animation_vf

        if ken_burns:
            animation_vf = build_animation_vf(animation_effect, clip_dur, fps, w_val, h_val, scene_idx)
        else:
            animation_vf = (
                f"scale={w_val}:{h_val}:force_original_aspect_ratio=decrease,"
                f"pad={w_val}:{h_val}:(ow-iw)/2:(oh-ih)/2:black,fps={fps}"
            )

        vf_parts = [animation_vf]

        if color_grade:
            vf_parts.append(color_grade)

        # VFX de grano de película sutil para cohesión visual
        vf_parts.append("noise=alls=7:allf=t+u")

        if subtitles and text:
            def fmt_time(s: float) -> str:
                ms = int((s % 1) * 1000)
                m, s_int = divmod(int(s), 60)
                _h, _m = divmod(m, 60)
                return f"{_h:02d}:{_m:02d}:{s_int:02d},{ms:03d}"

            srt_dir = os.path.dirname(output_mp4)
            scene_name = os.path.splitext(os.path.basename(image_path))[0]
            srt_path = os.path.join(srt_dir, f"{scene_name}.srt")
            with open(srt_path, "w", encoding="utf-8") as srt_f:
                srt_f.write(f"1\n00:00:00,000 --> {fmt_time(clip_dur)}\n{text}\n")

            safe_srt = srt_path.replace('\\', '/').replace(':', '\\:')
            vf_parts.append(f"subtitles='{safe_srt}':force_style='FontSize=26,PrimaryColour=&H0000FFFF,BorderStyle=1,Outline=3,Shadow=2,Bold=1,Alignment=2,MarginV=35'")

        # -- Cinematic Scene Title Overlay --
        if scene_title:
            safe_t = scene_title.replace("'", "").replace(":", "").replace("%", "")[:40].upper()
            draw_t = (
                f"drawtext=text='{safe_t}':fontcolor=white@0.7:fontsize={h_val//22}:"
                f"x=50:y=h-100:fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
                f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,3.5),1,if(lt(t,4.2),1-(t-3.5)/0.7,0)))'"
            )
            vf_parts.append(draw_t)

        # -- Watermark / Branding --
        try:
            _wcfg = _get_branding_config()
            if _wcfg.get("watermark_enabled", True):
                _wtext   = _wcfg.get("watermark_text", "@DarckRovert").replace("'", "").replace(":", "").replace("%", "")
                _wopacity = float(_wcfg.get("watermark_opacity", 0.55))
                _wsize   = max(16, h_val // 38)
                _wmark   = (
                    f"drawtext=text='{_wtext}':fontcolor=white@{_wopacity:.2f}:fontsize={_wsize}:"
                    f"x=w-tw-18:y=h-th-18:fontfile='C\\:/Windows/Fonts/arial.ttf'"
                )
                vf_parts.append(_wmark)
        except Exception:
            pass  # Config opcional — si falla, no bloquea el clip

        if fade and fade_d > 0:
            vf_parts.append(f"fade=t=in:st=0:d={fade_d}")
            vf_parts.append(f"fade=t=out:st={fade_out_t:.3f}:d={fade_d}")
        vf = ",".join(vf_parts)


        if has_audio:
            if _input_is_video:
                # Input es MP4 (ComfyUI L2): usar -stream_loop para repetir si necesario
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-stream_loop", "-1", "-i", image_path,
                    "-i", audio_path,
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-ac", "2",
                ]
            else:
                # Input es imagen estática: NO usar -loop 1 si el filtro es zoompan
                if "zoompan" in vf:
                    cmd = [
                        FFMPEG_EXE, "-y",
                        "-i", image_path,
                        "-i", audio_path,
                        "-c:v", codec, "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-ar", "44100", "-ac", "2",
                    ]
                else:
                    cmd = [
                        FFMPEG_EXE, "-y",
                        "-loop", "1", "-i", image_path,
                        "-i", audio_path,
                        "-c:v", codec, "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-ar", "44100", "-ac", "2",
                    ]

            # Ajuste matemático de audio (atempo) si el modo es manual
            if duration_mode == "manual" and audio_dur > 0:
                raw_tempo = audio_dur / clip_dur
                # Evitar distorsión extrema: limitamos la ralentización a 0.85x y aceleración a 1.25x.
                # Si el audio es más corto, FFmpeg dejará silencio natural al final.
                # Si es mucho más largo, será cortado por el -t, lo cual es el comportamiento esperado en manual.
                tempo = max(0.85, min(raw_tempo, 1.25))

                if abs(tempo - 1.0) > 0.05:
                    cmd.extend(["-filter:a", f"atempo={tempo:.4f}"])
                    log.info(f"[VideoStudio] Alineación de audio limitada: raw_tempo={raw_tempo:.2f} -> atempo={tempo:.4f}")

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
            if _input_is_video:
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-stream_loop", "-1", "-i", image_path,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-t", str(scene_duration),
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "128k",
                    "-vf", vf,
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_mp4,
                ]
            else:
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-loop", "1", "-i", image_path,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-t", str(scene_duration),
                    "-c:v", codec, "-preset", "fast",
                    "-c:a", "aac", "-b:a", "128k",
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
    # Genera BGM instrumental con ffmpeg usando los nuevos generadores de ruido cinemático
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
    
    # Asegurar que el audio sea estéreo (anoisesrc genera mono por defecto)
    if "anoisesrc" in expr:
        filtergraph = f"{expr},aformat=channel_layouts=stereo"
    else:
        filtergraph = expr
        
    fade_out_st = dur - 4
    cmd = [
        FFMPEG_EXE, '-y',
        '-f', 'lavfi', '-i', filtergraph,
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


def _concatenate_clips(clip_paths: list[str], output_mp4: str, bgm_type: str = "ninguna", bgm_volume: float = 0.1, codec: str = "libx264", resolution: str = "1024x1024") -> bool:
    """
    Concatena clips en el video final.
    Estrategia de 3 capas:
      1. Re-encode completo con normalización A/V + BGM mix.
      2. Fallback: stream-copy simple (sin re-encode).
      3. Fallback final: pre-normalizar cada clip individualmente, luego concat.
    """
    if not clip_paths:
        return False

    # Un solo clip: copiar directamente
    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_mp4)
        return True

    # Validar que todos los clips existen antes de empezar
    missing = [p for p in clip_paths if not os.path.isfile(p) or os.path.getsize(p) == 0]
    if missing:
        log.error(f"[VideoStudio] Clips faltantes o vacíos: {[os.path.basename(m) for m in missing]}")
        clip_paths = [p for p in clip_paths if os.path.isfile(p) and os.path.getsize(p) > 0]
        if not clip_paths:
            return False

    dyn_timeout = 120 + len(clip_paths) * 90

    def _write_list(path: str, clips: list[str]) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            for cp in clips:
                # FFmpeg concat demuxer requiere barras hacia adelante en Windows
                safe = cp.replace("\\", "/")
                fh.write(f"file '{safe}'\n")

    def _cleanup(path: str) -> None:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    list_file = output_mp4 + ".list.txt"

    # ── BGM ──────────────────────────────────────────────────────────────────
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bgm_path = os.path.join(base_dir, "inputs", f"bgm_{bgm_type.lower()}.mp3")
    if bgm_type != "ninguna" and not (os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096):
        _ensure_bgm(bgm_type, bgm_path)
    has_bgm = bgm_type != "ninguna" and os.path.isfile(bgm_path) and os.path.getsize(bgm_path) > 4096

    # ══ CAPA 1: Re-encode completo con normalización A/V ════════════════════
    try:
        _write_list(list_file, clip_paths)

        if has_bgm:
            # FIX CRÍTICO: No usar -f concat y -filter_complex en el mismo comando.
            # El concat demuxer genera gaps de PTS en AAC que amix comprime, causando
            # que TODA la pista de audio se acelere (efecto ardilla).
            # Paso 1: Concatenar todo sin BGM.
            temp_concat = output_mp4 + ".temp.mp4"
            cmd_concat = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart",
                temp_concat,
            ]
            r_concat = subprocess.run(cmd_concat, capture_output=True, timeout=dyn_timeout, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if r_concat.returncode == 0 and os.path.isfile(temp_concat):
                # Paso 2: Mezclar BGM
                filter_str = (
                    f"[0:a]aresample=44100,volume=1.2,asplit[sc][narr];"
                    f"[1:a]aresample=44100,volume={bgm_volume:.3f}[bgm];"
                    f"[bgm][sc]sidechaincompress=threshold=0.03:ratio=5:level_sc=0.8:attack=20:release=500[bgm_duck];"
                    f"[narr][bgm_duck]amix=inputs=2:duration=first:dropout_transition=2,volume=1.8[aout]"
                )
                cmd = [
                    FFMPEG_EXE, "-y",
                    "-i", temp_concat,
                    "-stream_loop", "-1", "-i", bgm_path,
                    "-filter_complex", filter_str,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",  # Copiar video ya codificado, ahorra mucho tiempo
                    "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-ac", "2",
                    "-movflags", "+faststart",
                    output_mp4,
                ]
                log.info(f"[VideoStudio] [L1] Concat {len(clip_paths)} clips + BGM ({bgm_type}) -> {os.path.basename(output_mp4)}")
            else:
                log.error(f"[VideoStudio] [L1] Falló pre-concat: {r_concat.stderr.decode(errors='replace')[-400:]}")
                cmd = None # Para que caiga al fallback
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart",
                output_mp4,
            ]
            log.info(f"[VideoStudio] [L1] Concat {len(clip_paths)} clips -> {os.path.basename(output_mp4)}")

        if cmd:
            r1 = subprocess.run(cmd, capture_output=True, timeout=dyn_timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)
        if has_bgm and 'temp_concat' in locals():
            _cleanup(temp_concat)

        if r1.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final: {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        err1 = r1.stderr.decode(errors="replace")[-600:]
        log.error(f"[VideoStudio] [L1] Falló: {err1}")

    except Exception as e1:
        log.error(f"[VideoStudio] [L1] Excepción: {e1}")
        _cleanup(list_file)

    # ══ CAPA 2: Stream-copy (sin re-encode, más rápido y permisivo) ══════════
    try:
        _write_list(list_file, clip_paths)
        cmd2 = [
            FFMPEG_EXE, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_mp4,
        ]
        log.info("[VideoStudio] [L2] Reintentando con stream-copy...")
        r2 = subprocess.run(cmd2, capture_output=True, timeout=dyn_timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)

        if r2.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final (stream-copy): {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        err2 = r2.stderr.decode(errors="replace")[-400:]
        log.error(f"[VideoStudio] [L2] Falló: {err2}")

    except Exception as e2:
        log.error(f"[VideoStudio] [L2] Excepción: {e2}")
        _cleanup(list_file)

    # ══ CAPA 3: Pre-normalizar cada clip → luego concat ═════════════════════
    log.info("[VideoStudio] [L3] Pre-normalizando clips individualmente...")
    norm_dir = os.path.join(os.path.dirname(output_mp4), "_norm_tmp")
    os.makedirs(norm_dir, exist_ok=True)
    norm_clips: list[str] = []

    try:
        for idx, cp in enumerate(clip_paths):
            norm_out = os.path.join(norm_dir, f"norm_{idx:03d}.mp4")
            ref_w, ref_h = DEFAULT_IMG_W, DEFAULT_IMG_H
            if "x" in resolution:
                parts = resolution.split("x")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    ref_w, ref_h = int(parts[0]), int(parts[1])
            cmd_norm = [
                FFMPEG_EXE, "-y",
                "-i", cp,
                "-vf", f"scale={ref_w}:{ref_h}:force_original_aspect_ratio=decrease,pad={ref_w}:{ref_h}:(ow-iw)/2:(oh-ih)/2:black,fps={DEFAULT_FPS}",
                "-af", "aresample=44100",
                "-c:v", codec, "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-ar", "44100", "-ac", "2",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                norm_out,
            ]
            rn = subprocess.run(cmd_norm, capture_output=True, timeout=180,
                                creationflags=subprocess.CREATE_NO_WINDOW)
            if rn.returncode == 0 and os.path.isfile(norm_out) and os.path.getsize(norm_out) > 0:
                norm_clips.append(norm_out)
            else:
                log.warning(f"[VideoStudio] [L3] No se pudo normalizar clip {idx}: {os.path.basename(cp)}")
                norm_clips.append(cp)

        if not norm_clips:
            log.error("[VideoStudio] [L3] Sin clips para concatenar tras normalización.")
            return False

        _write_list(list_file, norm_clips)
        cmd3 = [
            FFMPEG_EXE, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", codec, "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart",
            output_mp4,
        ]
        log.info(f"[VideoStudio] [L3] Concat post-normalización ({len(norm_clips)} clips)...")
        r3 = subprocess.run(cmd3, capture_output=True, timeout=dyn_timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        _cleanup(list_file)

        if r3.returncode == 0 and os.path.isfile(output_mp4) and os.path.getsize(output_mp4) > 0:
            log.info(f"[VideoStudio] Video final (L3): {os.path.basename(output_mp4)} ({os.path.getsize(output_mp4)/1048576:.1f} MB)")
            return True

        log.error(f"[VideoStudio] [L3] Falló: {r3.stderr.decode(errors='replace')[-400:]}")

    except Exception as e3:
        log.error(f"[VideoStudio] [L3] Excepción: {e3}")
        _cleanup(list_file)
    finally:
        try:
            import shutil as _sh
            _sh.rmtree(norm_dir, ignore_errors=True)
        except Exception:
            pass

    log.error("[VideoStudio] Las 3 capas de concatenación fallaron. Job marcado como fallido.")
    return False


# â”€â”€ Actualizador de estado en DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _update_job(job_id: int, **kwargs) -> None:
    valid  = {"status", "progress", "current_step", "output_path",
              "error", "started_at", "finished_at", "thumbnail_path", "title"}
    fields = {k: v for k, v in kwargs.items() if k in valid}
    if not fields:
        return
    sql    = "UPDATE video_jobs SET " + ", ".join(f"{k}=?" for k in fields)
    sql   += " WHERE id=?"
    values = list(fields.values()) + [job_id]
    conn   = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(sql, values)
    conn.commit()
    conn.close()


def _check_cancelled(job_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
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
    ken_burns: bool        = True,
    intro_card: bool       = False,
    color_grade: str       = "auto",
    animation_effect: str  = "auto",
    animation_level: int   = 1,
) -> None:
    """
    Pipeline completo con Character Consistency Engine + Motor de Animación (MAI).
    """
    global _current_job

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _update_job(job_id, status="running", started_at=now, progress=0,
                current_step="Generando guiÃ³n con el LLM...")
    with _lock:
        _current_job = {
            "id":               job_id,
            "topic":            topic,
            "title":            title or topic[:60],
            "style":            style,
            "total_scenes":     n_scenes,
            "current_scene":    0,
            "scenes_done":      [],
            "current_step":     "Generando guión con el LLM...",
            "progress":         0,
            "animation_effect": animation_effect,
            "animation_level":  animation_level,
        }

    job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    # Seed base del job: determinista por job_id + topic â†’ coherencia visual
    job_seed = int(hashlib.md5(f"{job_id}:{topic}".encode()).hexdigest()[:8], 16) % 2147483647

    try:
        _check_cancelled(job_id)
        # â”€â”€ PASO 1: GuiÃ³n + Visual Anchor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        scenes, visual_anchor, generated_title = _generate_script(topic, n_scenes, style, narration_lang, use_lore)
        if not scenes:
            raise RuntimeError("El LLM no devolviÃ³ escenas vÃ¡lidas.")

        if not title and generated_title:
            title = generated_title
            _update_job(job_id, title=title)
            with _lock:
                if _current_job:
                    _current_job["title"] = title

        style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
        style_prefix = style_info["prefix"]
        log.info(f"[VideoStudio] Visual Anchor del job #{job_id}: '{visual_anchor[:80]}'")

        # -- Grading de color efectivo
        effective_grade = STYLE_COLOR_GRADES.get(style, '') if color_grade == 'auto' else (color_grade if color_grade != 'none' else '')

        # -- Efecto de animación efectivo (resuelto por el MAI)
        from core.animation_engine import resolve_effect as _resolve_effect
        effective_animation = _resolve_effect(style, animation_effect)

        total_steps = n_scenes * 3 + 1
        step        = 0
        clip_paths: list[str] = []
        scenes_payload = []
        scenes_payload = []

        # -- Intro card opcional
        if intro_card:
            intro_path = os.path.join(job_dir, 'intro_card.mp4')
            w_ic, h_ic = DEFAULT_IMG_W, DEFAULT_IMG_H
            if 'x' in resolution:
                _p = resolution.split('x')
                if len(_p) == 2 and _p[0].isdigit() and _p[1].isdigit():
                    w_ic, h_ic = int(_p[0]), int(_p[1])
            if _create_title_card(title or "Video Promocional", style_info.get("label", "Cinema Studio"), intro_path, w_ic, h_ic, fps, 3.5, codec):
                clip_paths.insert(0, intro_path)

        previous_scene_image = None

        for i, scene in enumerate(scenes):
            scene_num   = i + 1
            scene_title = scene.get("title", f"Escena {scene_num}")
            narration   = scene.get("narration", "")

            # ── Extraer contexto visual de la escena anterior (si existe) ──
            scene_visual_context = ""
            if previous_scene_image:
                scene_visual_context = _get_scene_visual_context(previous_scene_image)

            # ── Construir prompt con anchor garantizado ──
            raw_prompt      = scene.get("image_prompt", topic)
            if scene_visual_context:
                raw_prompt = f"{scene_visual_context}, {raw_prompt}"
                
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

            previous_scene_image = img_path

            # ── PASO 3: TTS ──────────────────────────────────────────────
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

            # -- L2: Intentar animación via ComfyUI si animation_level >= 2 --
            _animated_src = img_path
            if animation_level >= 2:
                from core.animation_engine import animate_with_comfyui
                _anim_mp4 = animate_with_comfyui(
                    image_path=img_path,
                    job_id=job_id,
                    scene_idx=scene_num,
                    fps=min(fps, 8),   # ComfyUI limitado en CPU
                    frames=16,
                    output_dir=job_dir,
                )
                if _anim_mp4:
                    _animated_src = _anim_mp4
                    log.info(f"[VideoStudio] [MAI-L2] Escena {scene_num}: animación ComfyUI → {os.path.basename(_anim_mp4)}")
                else:
                    log.info(f"[VideoStudio] [MAI-L2] ComfyUI no disponible. Fallback a L1 ({effective_animation}).")

            # --- START REMOTION SCENE GATHERING ---
            # REMOTION_FPS es distinto de fps (el fps de FFmpeg/clips).
            # Remotion siempre renderiza a 30fps (Root.tsx). El cálculo de
            # durationInFrames DEBE usar REMOTION_FPS o los subtítulos desincronizarán.
            _dur_frames = int(scene_duration * REMOTION_FPS)
            _words = []
            if audio_ok and os.path.isfile(audio_path):
                import subprocess
                try:
                    probe = subprocess.run([FFMPEG_EXE, '-i', audio_path], capture_output=True, text=True, errors='replace')
                    _dur = float(scene_duration)
                    for l in probe.stderr.splitlines():
                        if 'Duration:' in l:
                            t = l.split('Duration:')[1].split(',')[0].strip()
                            h, m, s = t.split(':')
                            _dur = int(h) * 3600 + int(m) * 60 + float(s)
                            break
                    _dur_frames = int(_dur * REMOTION_FPS)

                    if subtitles:
                        from core.whisper_engine import WhisperEngine
                        _we = WhisperEngine(model_size="base")
                        _words = _we.extract_words(audio_path, language=narration_lang[:2])
                except Exception as e:
                    log.warning(f"[VideoStudio] Error calculando tiempos para {audio_path}: {e}")

            scenes_payload.append({
                "imagePath": _animated_src,
                "audioPath": audio_path if audio_ok else "",
                "durationInFrames": _dur_frames,
                "words": _words
            })
            with _lock:
                if _current_job and scene_num not in _current_job.get('scenes_done', []):
                    _current_job.setdefault('scenes_done', []).append(scene_num)
            # --- END REMOTION SCENE GATHERING ---

        # ── PASO 5: Video final ──────────────────────────────────────
        _update_job(job_id, progress=95, current_step="Renderizando video principal con Remotion...")
        with _lock:
            if _current_job:
                _current_job["progress"] = 95
                _current_job["current_step"] = "Renderizando video principal..."

        ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        final_path = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_{ts}.mp4")

        # Renderizar main video con Remotion
        total_duration_frames = sum(s.get("durationInFrames", 150) for s in scenes_payload)
        main_video_rendered = False
        try:
            from core.remotion_engine import RemotionEngine
            r_engine = RemotionEngine()
            long_props = {
                "scenes": scenes_payload,
                "durationInFrames": total_duration_frames
            }
            output_name = f"main_long_{job_id}_{ts}"
            main_rendered_path = r_engine.render_composition("LongTemplate", output_name, long_props)
            if main_rendered_path and os.path.isfile(main_rendered_path):
                clip_paths.append(main_rendered_path)
                main_video_rendered = True
        except Exception as rem_e:
            # Persistir stderr real en la DB para diagnóstico
            _update_job(job_id, error=str(rem_e)[:1000])
            log.error(f"[VideoStudio] Error en Remotion LongTemplate: {rem_e}")

        # Si el render principal tuvo éxito, decidir cómo producir el archivo final:
        # 1. Si hay intro_card O hay BGM → necesitamos _concatenate_clips (ffmpeg)
        # 2. Si NO hay intro_card Y bgm_type=='ninguna' → el MP4 de Remotion ES el final, solo copiar
        if main_video_rendered:
            intro_clips = [p for p in clip_paths if p != main_rendered_path]
            needs_concat = bool(intro_clips) or bgm_type != "ninguna"
            if needs_concat:
                if _concatenate_clips(clip_paths, final_path, bgm_type, bgm_volume, codec, resolution):
                    pass  # final_path escrito por _concatenate_clips
                else:
                    # Fallback: usar solo el video Remotion sin BGM si concat falla
                    import shutil
                    shutil.copy2(main_rendered_path, final_path)
                    log.warning(f"[VideoStudio] Fallback: video sin BGM/intro (concat falló).")
            else:
                # Sin intro_card y sin BGM: el output de Remotion es el archivo final directamente
                import shutil
                shutil.copy2(main_rendered_path, final_path)
            render_ok = os.path.isfile(final_path) and os.path.getsize(final_path) > 0
        else:
            render_ok = False

        if render_ok:
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _update_job(job_id, status="done", progress=100,
                        current_step="Completado", output_path=final_path,
                        finished_at=now)
            with _lock:
                if _current_job:
                    _current_job["progress"] = 100
                    _current_job["current_step"] = "Completado"
            log.info(f"[VideoStudio] Job #{job_id} completado -> {final_path}")
            # -- Thumbnail
            thumb_path = os.path.join(OUTPUT_DIR, f'thumb_{job_id}.jpg')
            if _extract_thumbnail(final_path, thumb_path):
                _update_job(job_id, thumbnail_path=thumb_path)
                log.info(f'[VideoStudio] Thumbnail: {os.path.basename(thumb_path)}')

            # ── Guardar script.json para Language Cloner ─────────────────────
            try:
                script_json_path = os.path.join(job_dir, "script.json")
                with open(script_json_path, "w", encoding="utf-8") as _sf:
                    json.dump(scenes, _sf, ensure_ascii=False, indent=2)
            except Exception as _sj_e:
                log.warning(f"[VideoStudio] Error guardando script.json: {_sj_e}")

            # ── Construir niche_id y lang desde el scheduler state ────────────
            _niche_id = ""
            _niche_lang = "es"
            try:
                from core import content_scheduler as _cs
                _niche_id = _cs._state.get("last_niche", "")
                # Leer lang desde niches.json para el niche activo
                _niche_data = _cs._load_niches()
                for _n in _niche_data.get("niches", []):
                    if _n.get("id") == _niche_id:
                        _niche_lang = _n.get("lang", "es")
                        break
            except Exception:
                pass

            # ── Generar Activos Sociales (Hack 3: Multiplicación de Contenido) ──
            try:
                from core.social_assets_generator import generate_social_assets
                social_output_path = os.path.join(job_dir, "social_assets.txt")
                generate_social_assets(
                    job_id=job_id,
                    script_path=script_json_path,
                    output_path=social_output_path,
                    lang=_niche_lang
                )
            except Exception as _sa_e:
                log.warning(f"[VideoStudio] Error generando activos sociales: {_sa_e}")

            # ── YouTube Auto-Upload (inyecta afiliados + registra en revenue) ─

            # ── Social Distribution (TikTok / Instagram Reels) ────────────────
            try:
                _shorts_path = final_path.replace('.mp4', '_short.mp4')
                
                # 1. Remotion Shorts Generator
                try:
                    log.info("[VideoStudio] Iniciando generación de Short interactivo con Remotion y Whisper...")
                    from core.whisper_engine import WhisperEngine
                    from core.remotion_engine import RemotionEngine
                    import subprocess
                    
                    temp_short_src = final_path.replace('.mp4', '_temp_short.mp4')
                    subprocess.run([
                        FFMPEG_EXE, '-y', '-i', final_path, 
                        '-t', '59', '-c:v', 'copy', '-c:a', 'copy', temp_short_src
                    ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    probe = subprocess.run([FFMPEG_EXE, '-i', temp_short_src], capture_output=True, text=True, errors='replace')
                    dur = 59
                    for l in probe.stderr.splitlines():
                        if 'Duration:' in l:
                            t = l.split('Duration:')[1].split(',')[0].strip()
                            h, m, s = t.split(':')
                            dur = int(h) * 3600 + int(m) * 60 + float(s)
                            break
                    duration_frames = int(dur * REMOTION_FPS)
                    
                    w_engine = WhisperEngine(model_size="base")
                    words_data = w_engine.extract_words(temp_short_src, language=narration_lang[:2])
                    
                    r_engine = RemotionEngine()
                    props = {"videoPath": temp_short_src, "words": words_data, "durationInFrames": duration_frames}
                    
                    output_name = os.path.basename(_shorts_path).replace('.mp4', '')
                    rendered_mp4 = r_engine.render_composition("ShortTemplate", output_name, props)
                    
                    if os.path.isfile(rendered_mp4):
                        import shutil
                        shutil.move(rendered_mp4, _shorts_path)
                        log.info(f"[VideoStudio] Short generado exitosamente: {_shorts_path}")
                        
                    try:
                        os.remove(temp_short_src)
                    except:
                        pass
                except Exception as rem_e:
                    log.error(f"[VideoStudio] Error generando Short con Remotion: {rem_e}")

                # 2. YouTube Upload (Long + Short)
                try:
                    from core.youtube_uploader import upload_job_async
                    upload_job_async(
                        job_id     = job_id,
                        video_path = final_path,
                        title      = title or topic[:100],
                        thumb_path = thumb_path if os.path.isfile(thumb_path) else "",
                        niche_id   = _niche_id,
                        lang       = _niche_lang,
                    )
                except Exception as _yt_e:
                    log.warning(f"[VideoStudio] YouTube upload dispatch error: {_yt_e}")

                # 3. Social Distribution (TikTok / Instagram)
                from core.tiktok_uploader import distribute_short_async
                if os.path.isfile(_shorts_path):
                    distribute_short_async(
                        job_id      = job_id,
                        shorts_path = _shorts_path,
                        title       = title or topic[:100],
                    )

            except Exception as _tt_e:
                log.warning(f"[VideoStudio] Social distribution error: {_tt_e}")


            # ── Language Cloner: clonar en idiomas adicionales ────────────────
            try:
                from core.language_cloner import clone_job_async, get_enabled_languages
                if get_enabled_languages():
                    clone_job_async(source_job_id=job_id)
            except Exception as _lc_e:
                log.warning(f"[VideoStudio] Language cloner dispatch error: {_lc_e}")

            if use_lore:
                try:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    inputs_dir = os.path.join(base_dir, "inputs")
                    os.makedirs(inputs_dir, exist_ok=True)
                    lore_path = os.path.join(inputs_dir, "cinematic_lore.txt")
                    with open(lore_path, "a", encoding="utf-8") as f:
                        # Guardar siempre referenciado al topic original para encadenado seguro
                        safe_title = topic if len(topic) < 100 and not topic.startswith("http") else (title or "Historia_Generada")
                        f.write(f"\n\n=== HISTORIA: {safe_title} ===\n")
                        for s in scenes:
                            f.write(f"Escena: {s.get('title', '')}\n")
                            f.write(f"Narración: {s.get('narration', '')}\n")
                except Exception as e:
                    log.warning(f"[VideoStudio] Error guardando lore: {e}")
        else:
            raise RuntimeError(f"Remotion render falló. Verifica los logs de RemotionEngine para detalles.")

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
            conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
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
                    ken_burns        = bool(row["ken_burns"]         if "ken_burns"         in keys else 1),
                    intro_card       = bool(row["intro_card"]        if "intro_card"        in keys else 0),
                    color_grade      = row["color_grade"]            if "color_grade"       in keys else "auto",
                    animation_effect = row["animation_effect"]       if "animation_effect"  in keys else "auto",
                    animation_level  = int(row["animation_level"])   if "animation_level"   in keys else 1,
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
    log.info("[VideoStudio] Worker daemon iniciado (Gravity Studio ULTRA V15.0 PRO - Audio Ducking & VFX Active).")


# â”€â”€ API pÃºblica â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_video_url(output_path: str) -> str:
    """Convierte ruta absoluta en URL relativa para descarga."""
    if not output_path:
        return ""
    fname = os.path.basename(output_path)
    return f"/v1/video/download?file={fname}"

