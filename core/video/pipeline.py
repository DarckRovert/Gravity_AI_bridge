import os
import re
import json
import sqlite3
import hashlib
import threading
import time
from datetime import datetime, timezone

from core.logger import log
from core.video.audio_processor import _generate_audio, get_available_voices, BGM_GENERATORS
from core.video.script_builder import _generate_script, _get_scene_visual_context, CINEMA_STYLES, DEFAULT_STYLE
from core.video.renderer import (
    _generate_scene_image, _create_placeholder_image, _create_title_card,
    _extract_thumbnail, _assemble_clip, _concatenate_clips
)
from core.video.audio_analyzer import extract_multiband_energy
from core.video.timeline_director import generate_timeline, generate_color_sequence
from core.video.glsl_renderer_v13 import render_v13_video

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "_videos")
DB_PATH = os.path.join(BASE_DIR, "_video_queue.sqlite")
FFMPEG_EXE = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")

DEFAULT_SCENES = 6
DEFAULT_IMG_W = 1216
DEFAULT_IMG_H = 832
SECONDS_PER_SCENE = 8
TTS_RATE = 150
MAX_HISTORY = 20
FADE_DURATION = 0.4
DEFAULT_FPS = 24
REMOTION_FPS = 30
DEFAULT_BGM_VOLUME = 0.1
DB_CONNECT_TIMEOUT = 15

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

_lock = threading.RLock()
_db_lock = threading.RLock()
_current_job = None
_started = False
_db_initialized = False

def _init_db() -> None:
    """Inicializa de forma atómica y thread-safe la base de datos SQLite y ejecuta migraciones."""
    global _db_initialized
    with _db_lock:
        if _db_initialized:
            return
        _db_initialized = True
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
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
                ("youtube_video_id",  "TEXT NOT NULL DEFAULT ''"),
                ("youtube_url",       "TEXT NOT NULL DEFAULT ''"),
                ("uploaded_at",       "TEXT NOT NULL DEFAULT ''"),
                ("upload_status",     "TEXT NOT NULL DEFAULT 'pending'"),
                ("shorts_path",       "TEXT NOT NULL DEFAULT ''"),
                ("shorts_video_id",   "TEXT NOT NULL DEFAULT ''"),
                ("seo_tags",          "TEXT NOT NULL DEFAULT ''"),
                ("seo_description",   "TEXT NOT NULL DEFAULT ''"),
                ("niche_id",          "TEXT NOT NULL DEFAULT ''"),
                ("cloned_from",       "INTEGER NOT NULL DEFAULT 0"),
                ("clone_lang",        "TEXT NOT NULL DEFAULT ''"),
                ("job_type",          "TEXT NOT NULL DEFAULT 'tts'"),
                ("audio_track_path",  "TEXT NOT NULL DEFAULT ''"),
                ("lyrics_text",       "TEXT NOT NULL DEFAULT ''"),
                ("input_video_path",  "TEXT NOT NULL DEFAULT ''"),
            ]
            for col_name, col_def in migrations:
                if col_name not in existing:
                    conn.execute(f"ALTER TABLE video_jobs ADD COLUMN {col_name} {col_def}")
            conn.commit()

            try:
                stuck = conn.execute(
                    "SELECT COUNT(*) FROM video_jobs WHERE status='running'"
                ).fetchone()[0]
                if stuck > 0:
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
        finally:
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
    job_type: str          = "tts",
    audio_track_path: str  = "",
    lyrics_text: str       = "",
    input_video_path: str  = "",
) -> int:
    """Encola un nuevo trabajo de video. Retorna el ID generado."""
    _init_db()
    
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
    with _db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            cur  = conn.execute(
                "INSERT INTO video_jobs "
                "(topic, n_scenes, voice_speed, voice_id, style, narration_lang, transitions, "
                " resolution, subtitles, title, bgm_type, quality, use_lore, fps, scene_duration, "
                " duration_mode, bgm_volume, codec, ken_burns, intro_card, color_grade, "
                " animation_effect, animation_level, niche_id, job_type, audio_track_path, lyrics_text, input_video_path, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    topic, n_scenes, voice_speed, voice_id, style, narration_lang,
                    1 if transitions else 0, resolution, 1 if subtitles else 0,
                    title, bgm_type, quality, 1 if use_lore else 0,
                    fps, scene_duration, duration_mode, float(bgm_volume), codec,
                    1 if ken_burns else 0, 1 if intro_card else 0, color_grade,
                    animation_effect, int(animation_level), niche_id, 
                    job_type, audio_track_path, lyrics_text, input_video_path, now
                )
            )
            job_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()
    log.info(f"[VideoStudio] Job #{job_id} encolado: {title or topic[:60]} | estilo={style} | voz='{voice_id or 'auto'}' | calidad={quality}")
    return job_id


def get_queue_status() -> dict:
    """Estado completo de la cola de video para el dashboard de forma thread-safe."""
    _init_db()
    with _db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            conn.row_factory = sqlite3.Row
            pending  = [dict(r) for r in conn.execute(
                "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id"
            ).fetchall()]
            
            raw_history = conn.execute(
                "SELECT * FROM video_jobs WHERE status NOT IN ('pending', 'deleted') ORDER BY id DESC LIMIT ?",
                (MAX_HISTORY,)
            ).fetchall()
        finally:
            conn.close()

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
            with _db_lock:
                _pc = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
                try:
                    for _pid in purge_ids:
                        _pc.execute("UPDATE video_jobs SET status='deleted', output_path=NULL WHERE id=?", (_pid,))
                    _pc.commit()
                finally:
                    _pc.close()
        except Exception as _pe:
            log.debug(f"[VideoStudio] Purge batch error: {_pe}")

    with _lock:
        current = _current_job

    try:
        with _db_lock:
            _sc = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
            try:
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
            finally:
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
    """Cancela un trabajo pendiente de forma thread-safe."""
    _init_db()
    now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            rows = conn.execute(
                "UPDATE video_jobs SET status='cancelled', finished_at=? "
                "WHERE id=? AND status IN ('pending', 'running')",
                (now, job_id)
            ).rowcount
            conn.commit()
        finally:
            conn.close()
    return rows > 0


def delete_job(job_id: int) -> dict:
    """Elimina un job de la DB y borra sus archivos físicos de forma thread-safe."""
    _init_db()
    with _db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT output_path FROM video_jobs WHERE id=?", (job_id,)).fetchone()
        finally:
            conn.close()

    deleted_files: list[str] = []
    errors: list[str] = []

    if row:
        out_path = row["output_path"]
        if out_path and os.path.isfile(out_path):
            try:
                os.remove(out_path)
                deleted_files.append(out_path)
            except Exception as e:
                errors.append(str(e))
        job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
        if os.path.isdir(job_dir):
            import shutil
            try:
                shutil.rmtree(job_dir)
                deleted_files.append(job_dir)
            except Exception as e:
                errors.append(str(e))
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with _db_lock:
            conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
            try:
                conn.execute(
                    "UPDATE video_jobs SET status='deleted', output_path=NULL, finished_at=? WHERE id=?",
                    (now, job_id)
                )
                conn.commit()
            finally:
                conn.close()
    return {
        "ok": row is not None,
        "deleted_files": deleted_files,
        "errors": errors,
        "job_id": job_id,
    }


def _update_job(job_id: int, **kwargs) -> None:
    """Actualiza el estado de un trabajo de video de forma thread-safe."""
    valid  = {"status", "progress", "current_step", "output_path",
              "error", "started_at", "finished_at", "thumbnail_path", "title"}
    fields = {k: v for k, v in kwargs.items() if k in valid}
    if not fields:
        return
    sql    = "UPDATE video_jobs SET " + ", ".join(f"{k}=?" for k in fields)
    sql   += " WHERE id=?"
    values = list(fields.values()) + [job_id]
    with _db_lock:
        conn   = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(sql, values)
            conn.commit()
        finally:
            conn.close()


def _check_cancelled(job_id: int) -> None:
    """Verifica si un trabajo ha sido cancelado por el usuario de forma thread-safe."""
    with _db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
        try:
            status = conn.execute("SELECT status FROM video_jobs WHERE id=?", (job_id,)).fetchone()
        finally:
            conn.close()
    if status and status[0] == 'cancelled':
        raise RuntimeError("Proceso cancelado por el usuario.")


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
    job_type: str          = "tts",
    audio_track_path: str  = "",
    lyrics_text: str       = "",
    input_video_path: str  = "",
) -> None:
    """
    Pipeline completo con Character Consistency Engine + Motor de Animación (MAI).
    """
    global _current_job

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _update_job(job_id, status="running", started_at=now, progress=0,
                current_step="Generando guión con el LLM...")
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

    job_seed = int(hashlib.md5(f"{job_id}:{topic}".encode()).hexdigest()[:8], 16) % 2147483647

    try:
        _check_cancelled(job_id)
        
        # === YOUTUBE OAUTH2 SHIELD ===
        skip_social_upload = False
        try:
            from core.youtube_uploader import verify_token_health
            if not verify_token_health():
                log.warning("[VideoStudio] OAUTH_ERROR detectado. Se omitirá la subida a redes, pero el render local continuará.")
                skip_social_upload = True
        except ImportError:
            pass # Si el módulo no existe, ignorar
        
        v13_bypass = False

        # === INTERCEPTOR V13 BIOMECÁNICO / GALÁCTICO ===
        if job_type == "music" and style in ["biomechanic_v13", "galactic", "oceanic", "protean", "interstellar", "inception_kifs", "neon_fluid", "organic_core", "turing_patterns"]:
            log.info(f"[VideoStudio] Interceptando Pipeline: Redirigiendo a Motor GLSL V13...")
            if not audio_track_path or not os.path.isfile(audio_track_path):
                raise RuntimeError("El Motor V13 requiere un archivo de audio (.mp3/.wav) válido en audio_track_path.")
            
            _update_job(job_id, progress=10, current_step="Analizando frecuencias de audio (Multiband)...")
            multiband = extract_multiband_energy(audio_track_path, fps)
            total_frames = len(multiband.get('bass', []))
            
            if total_frames == 0:
                raise RuntimeError("Fallo al extraer energía del audio para V13.")
                
            _update_job(job_id, progress=30, current_step="Generando línea de tiempo y paletas fractales...")
            timeline = generate_timeline(multiband, fps)
            colorsA, colorsB = generate_color_sequence(total_frames, multiband, fps)
            
            # === AI DIRECTOR INJECTION (Per-Section Dynamic) ===
            speed_mult_arr = None   # None = escalar 1.0 (fallback)
            turb_mult_arr = None
            speed_mult = 1.0
            turb_mult = 1.0
            if lyrics_text and len(lyrics_text.strip()) > 10:
                _update_job(job_id, progress=40, current_step="AI Director: Analizando secciones de la letra...")
                try:
                    from core.video.v13_ai_director import analyze_lyrics_sections
                    ai_result = analyze_lyrics_sections(lyrics_text, total_frames, fps)
                    if ai_result and "colorsA" in ai_result:
                        log.info(f"[VideoStudio] AI Director: Paletas y Timeline Narrativo dinámico aplicado ({len(ai_result['colorsA'])} frames)")
                        colorsA = ai_result["colorsA"]
                        colorsB = ai_result["colorsB"]
                        speed_mult_arr = ai_result["speed"]
                        turb_mult_arr = ai_result["turbulence"]
                        if "timeline" in ai_result and len(ai_result["timeline"]) > 0:
                            timeline = ai_result["timeline"]
                            log.info(f"[VideoStudio] AI Director: {len(timeline)} escenas narrativas mapeadas con éxito.")
                    else:
                        log.warning("[VideoStudio] AI Director no devolvió secciones válidas, usando análisis acústico global de fallback.")
                except Exception as e_ai:
                    log.warning(f"[VideoStudio] AI Director (secciones) falló: {e_ai}")
            
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
            final_path = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_V13_{ts}.mp4")
            
            # Derivar resolución si está presente
            _res_parts = resolution.split("x") if "x" in resolution else []
            _tgt_w = int(_res_parts[0]) if len(_res_parts) == 2 and _res_parts[0].isdigit() else DEFAULT_IMG_W
            _tgt_h = int(_res_parts[1]) if len(_res_parts) == 2 and _res_parts[1].isdigit() else DEFAULT_IMG_H
            
            # === AI-FIRST: Generar imágenes de fondo cinematográficas ===
            if style in ["galactic", "oceanic", "protean", "interstellar", "inception_kifs", "neon_fluid", "organic_core", "turing_patterns"]:
                log.info(f"[VideoStudio] Estilo '{style}': Omitiendo generación de imágenes AI 2D (Render 100% Shader).")
                background_images = [None] * len(timeline)
            else:
                _update_job(job_id, progress=45, current_step="Generando fondos cinematográficos AI-First...")
                background_images = None
                try:
                    from core.video.ai_scene_generator import generate_scene_images
                    background_images = generate_scene_images(timeline, w=_tgt_w, h=_tgt_h, colorsA=colorsA)
                    if not background_images:
                        background_images = [None] * len(timeline)
                except Exception as e_bg:
                    log.warning(f"[VideoStudio] Fallo al generar imágenes AI-First: {e_bg}")
                    background_images = [None] * len(timeline)
                
            # === GENERAR SUBTÍTULOS CINEMÁTICOS ASS ===
            _update_job(job_id, progress=48, current_step="Extrayendo letras y generando subtítulos ASS...")
            ass_path = None
            try:
                from core.video.subtitle_engine import generate_ass_subtitles
                tmp_ass = os.path.join(OUTPUT_DIR, f"temp_{job_id}_lyrics.ass")
                ass_path = generate_ass_subtitles(audio_track_path, tmp_ass)
            except Exception as e_sub:
                log.warning(f"[VideoStudio] Fallo al generar subtítulos ASS: {e_sub}")

            # === FORZAR SHADER STANDALONE (Si aplica) ===
            if style in ["galactic", "oceanic", "protean", "interstellar", "inception_kifs", "neon_fluid", "organic_core", "turing_patterns"]:
                for sc in timeline:
                    sc["engine"] = style

            _update_job(job_id, progress=50, current_step=f"Renderizando {style.upper()} V17 (GPU)...")
            render_v13_video(
                timeline=timeline,
                multiband=multiband,
                colorsA=colorsA,
                colorsB=colorsB,
                w=_tgt_w,
                h=_tgt_h,
                fps=fps,
                out_mp4=final_path,
                audio_path=audio_track_path,
                speed_multiplier=speed_mult_arr if speed_mult_arr is not None else speed_mult,
                turbulence=turb_mult_arr if turb_mult_arr is not None else turb_mult,
                background_images=background_images,
                subtitle_file=ass_path
            )
            
            if not os.path.isfile(final_path):
                raise RuntimeError("El renderizador V13 falló y no devolvió ningún MP4.")
                
            if style in ["galactic", "oceanic", "protean", "interstellar", "inception_kifs", "neon_fluid", "organic_core", "turing_patterns"]:
                _shorts_path = final_path.replace(".mp4", "_short.mp4")
                _update_job(job_id, progress=75, current_step=f"Renderizando NATIVO VERTICAL {style.upper()} V17 (GPU)...")
                
                # Generar ASS específico para vertical (PlayResX: 720, PlayResY: 1280)
                ass_path_vertical = None
                if ass_path:
                    try:
                        from core.video.subtitle_engine import generate_ass_subtitles
                        tmp_ass_vert = os.path.join(OUTPUT_DIR, f"temp_{job_id}_lyrics_vertical.ass")
                        ass_path_vertical = generate_ass_subtitles(audio_track_path, tmp_ass_vert, tgt_w=_tgt_h, tgt_h=_tgt_w)
                    except Exception as e_sub_vert:
                        log.warning(f"[VideoStudio] Fallo al generar subtítulos ASS Verticales: {e_sub_vert}")

                render_v13_video(
                    timeline=timeline,
                    multiband=multiband,
                    colorsA=colorsA,
                    colorsB=colorsB,
                    w=_tgt_h,
                    h=_tgt_w,
                    fps=fps,
                    out_mp4=_shorts_path,
                    audio_path=audio_track_path,
                    speed_multiplier=speed_mult_arr if speed_mult_arr is not None else speed_mult,
                    turbulence=turb_mult_arr if turb_mult_arr is not None else turb_mult,
                    background_images=background_images,
                    subtitle_file=ass_path_vertical
                )

            # Saltar el resto del código y saltar directo a "render_ok"
            render_ok = True
            
            # Limpiamos el salto para que el resto de variables que usa el final no colapsen
            scenes = [{"title": "V13 Music Video", "image_prompt": "Audio Reactive V13", "narration": ""}]
            thumb_path = ""
            generated_title = title or topic or "Music Video"
            visual_anchor = "esthetic cinematic lighting, visually stunning"
            v13_bypass = True
            
        elif job_type == "music":
            visual_anchor = "esthetic cinematic lighting, visually stunning"
            generated_title = title or topic or "Music Video"
            scenes = []
            import subprocess
            _track_duration = 0
            if audio_track_path and os.path.isfile(audio_track_path):
                try:
                    probe = subprocess.run([FFMPEG_EXE, '-i', audio_track_path], capture_output=True, text=True, errors='replace')
                    for l in probe.stderr.splitlines():
                        if 'Duration:' in l:
                            t = l.split('Duration:')[1].split(',')[0].strip()
                            h, m, s = t.split(':')
                            _track_duration = int(h) * 3600 + int(m) * 60 + float(s)
                            break
                except: pass
                if _track_duration > 0:
                    scene_duration = _track_duration / max(1, n_scenes)
            
            lines = [l.strip() for l in lyrics_text.split('\n') if l.strip()]
            chunk_size = max(1, len(lines) // max(1, n_scenes)) if lines else 1
            for i in range(n_scenes):
                start_idx = i * chunk_size
                end_idx = len(lines) if i == n_scenes - 1 else (i + 1) * chunk_size
                lyric_chunk = " ".join(lines[start_idx:end_idx])
                prompt = f"{topic}. {lyric_chunk}" if lyric_chunk else topic
                scenes.append({
                    "title": f"Escena {i+1}",
                    "image_prompt": prompt[:300],
                    "narration": ""
                })
        else:
            scenes, visual_anchor, generated_title = _generate_script(topic, n_scenes, style, narration_lang, use_lore)
            if not scenes:
                raise RuntimeError("El LLM no devolvió escenas válidas.")
            v13_bypass = False

        if not title and generated_title:
            title = generated_title
            _update_job(job_id, title=title)
            with _lock:
                if _current_job:
                    _current_job["title"] = title

        if v13_bypass:
            # V13 Bypass salta directamente al final
            pass
        else:
            style_info   = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
            log.info(f"[VideoStudio] Visual Anchor del job #{job_id}: '{visual_anchor[:80]}'")
    
            effective_animation = animation_effect
            try:
                from core.animation_engine import resolve_effect as _resolve_effect
                effective_animation = _resolve_effect(style, animation_effect)
            except Exception:
                pass
    
            total_steps = n_scenes * 3 + 1
            step        = 0
        clip_paths: list[str] = []
        scenes_payload = []

        if intro_card and not v13_bypass:
            intro_path = os.path.join(job_dir, 'intro_card.mp4')
            w_ic, h_ic = DEFAULT_IMG_W, DEFAULT_IMG_H
            if 'x' in resolution:
                _p = resolution.split('x')
                if len(_p) == 2 and _p[0].isdigit() and _p[1].isdigit():
                    w_ic, h_ic = int(_p[0]), int(_p[1])
            if _create_title_card(title or "Video Promocional", style_info.get("label", "Cinema Studio"), intro_path, w_ic, h_ic, fps, 3.5, codec):
                clip_paths.insert(0, intro_path)

        previous_scene_image = None
        user_video_clips = []
        if input_video_path and os.path.isfile(input_video_path) and not v13_bypass:
            from core.video.video_slicer import extract_clips_from_video
            w_res, h_res = 1216, 832
            if 'x' in resolution:
                _p = resolution.split('x')
                if len(_p) == 2 and _p[0].isdigit() and _p[1].isdigit():
                    w_res, h_res = int(_p[0]), int(_p[1])
            user_video_clips = extract_clips_from_video(
                input_video_path,
                os.path.join(job_dir, 'user_clips'),
                n_scenes,
                float(scene_duration),
                w_res,
                h_res,
                fps
            )

        for i, scene in enumerate(scenes):
            if v13_bypass:
                break
            scene_num   = i + 1
            scene_title = scene.get("title", f"Escena {scene_num}")
            narration   = scene.get("narration", "")

            scene_visual_context = ""
            if previous_scene_image:
                scene_visual_context = _get_scene_visual_context(previous_scene_image)

            raw_prompt      = scene.get("image_prompt", topic)
            if scene_visual_context:
                raw_prompt = f"{scene_visual_context}, {raw_prompt}"
                
            anchored_prompt = (
                f"{visual_anchor}, {raw_prompt}, {style_info['prefix']}"
                if visual_anchor.lower() not in raw_prompt.lower()
                else f"{raw_prompt}, {style_info['prefix']}"
            )
            anchored_prompt = anchored_prompt[:150]

            # ── PASO 2: Imagen ──
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
                w_ph, h_ph = 1216, 832
                if "x" in resolution:
                    try:
                        w_ph, h_ph = map(int, resolution.split("x"))
                    except:
                        pass
                _create_placeholder_image(scene_title, placeholder, w_ph, h_ph)
                img_path = placeholder

            previous_scene_image = img_path

            # ── PASO 3: TTS ──
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
            if job_type == "music":
                audio_ok = False
            else:
                audio_ok   = _generate_audio(narration, audio_path, voice_speed, voice_id) if narration else False

            # ── PASO 4: Clip ──
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

            _animated_src = img_path
            if animation_level >= 1:
                # ── L1.5: Multi-variación Pollinations + FFmpeg xfade ──────────────
                try:
                    from core.animation_engine import animate_with_variations
                    _res_parts = resolution.split("x") if "x" in resolution else []
                    _tgt_w = int(_res_parts[0]) if len(_res_parts) == 2 and _res_parts[0].isdigit() else 0
                    _tgt_h = int(_res_parts[1]) if len(_res_parts) == 2 and _res_parts[1].isdigit() else 0
                    
                    _ai_dur = float(scene_duration)
                    if len(user_video_clips) >= scene_num and user_video_clips[scene_num - 1]:
                        _ai_dur = _ai_dur / 2.0

                    _anim_l15 = animate_with_variations(
                        image_path=img_path,
                        prompt=anchored_prompt,
                        job_id=job_id,
                        scene_idx=scene_num,
                        fps=min(fps, 8),
                        duration=_ai_dur,
                        n_variations=4,
                        output_dir=job_dir,
                        ffmpeg_exe=FFMPEG_EXE,
                        target_w=_tgt_w,
                        target_h=_tgt_h,
                    )
                    if _anim_l15:
                        _animated_src = _anim_l15
                        log.info(f"[VideoStudio] [MAI-L1.5] Escena {scene_num}: variaciones Pollinations → {os.path.basename(_anim_l15)}")
                except Exception as _l15_err:
                    log.warning(f"[VideoStudio] Animation Engine L1.5 fail: {_l15_err}")

            if animation_level >= 2 and _animated_src == img_path:
                # ── L2: ComfyUI (fallback si L1.5 falló) ─────────────────────────
                try:
                    from core.animation_engine import animate_with_comfyui
                    _anim_mp4 = animate_with_comfyui(
                        image_path=img_path,
                        job_id=job_id,
                        scene_idx=scene_num,
                        fps=min(fps, 8),
                        frames=int(_ai_dur * min(fps, 8)),
                        output_dir=job_dir,
                    )
                    if _anim_mp4:
                        _animated_src = _anim_mp4
                        log.info(f"[VideoStudio] [MAI-L2] Escena {scene_num}: animación ComfyUI → {os.path.basename(_anim_mp4)}")
                    else:
                        log.info(f"[VideoStudio] [MAI-L2] ComfyUI no disponible. Fallback a L1 ({effective_animation}).")
                except Exception as _ae_err:
                    log.warning(f"[VideoStudio] Animation Engine L2 fail: {_ae_err}")

            # ── Híbrido: Concatenar User Clip y AI Clip ──
            if len(user_video_clips) >= scene_num and user_video_clips[scene_num - 1]:
                user_clip = user_video_clips[scene_num - 1]
                hybrid_out = os.path.join(job_dir, f"scene_{scene_num:02d}_hybrid.mp4")
                # Derivar dimensiones del parámetro resolution (e.g. "720x1280")
                _res_wh = resolution.split("x") if "x" in resolution else []
                w = int(_res_wh[0]) if len(_res_wh) == 2 and _res_wh[0].isdigit() else DEFAULT_IMG_W
                h = int(_res_wh[1]) if len(_res_wh) == 2 and _res_wh[1].isdigit() else DEFAULT_IMG_H
                try:
                    if not _animated_src.endswith(".mp4"):
                        # Si la animación falló, convertimos la imagen estática a un clip MP4 del tiempo restante
                        ai_dur = float(scene_duration) / 2.0
                        img_vid = os.path.join(job_dir, f"scene_{scene_num:02d}_img.mp4")
                        subprocess.run([
                            FFMPEG_EXE, "-y",
                            "-loop", "1", "-framerate", "24", "-t", str(ai_dur),
                            "-i", _animated_src,
                            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                            "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
                            img_vid
                        ], capture_output=True, check=True)
                        _animated_src = img_vid

                    subprocess.run([
                        FFMPEG_EXE, "-y",
                        "-i", user_clip,
                        "-i", _animated_src,
                        "-filter_complex", f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1/1,fps=24[v0];[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1/1,fps=24[v1];[v0][v1]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
                        hybrid_out
                    ], capture_output=True, check=True)
                    _animated_src = hybrid_out
                    log.info(f"[VideoStudio] Híbrido creado para escena {scene_num}.")
                except Exception as e:
                    log.warning(f"[VideoStudio] Fallo al crear híbrido para escena {scene_num}: {e}")

            # Remotion Scene Gathering
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
                            hh, mm, ss = t.split(':')
                            _dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
                            break
                    _dur_frames = int(_dur * REMOTION_FPS)

                    if subtitles:
                        try:
                            from core.whisper_engine import WhisperEngine
                            _we = WhisperEngine(model_size="base")
                            _words = _we.extract_words(audio_path, language=narration_lang[:2])
                        except Exception as wh_err:
                            log.warning(f"[VideoStudio] Whisper Engine fail: {wh_err}")
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

        # ── PASO 5: Video final ──
        _update_job(job_id, progress=95, current_step="Renderizando video principal con Remotion...")
        with _lock:
            if _current_job:
                _current_job["progress"] = 95
                _current_job["current_step"] = "Renderizando video principal..."

        if not v13_bypass:
            ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
            final_path = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_{ts}.mp4")

        if v13_bypass:
            main_video_rendered = True
            main_rendered_path = final_path
        else:
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
                _update_job(job_id, error=str(rem_e)[:1000])
                log.error(f"[VideoStudio] Error en Remotion LongTemplate: {rem_e}")

        if main_video_rendered:
            if v13_bypass:
                pass # The V13 render is already at final_path, no concatenation or copying needed
            else:
                intro_clips = [p for p in clip_paths if p != main_rendered_path]
                needs_concat = bool(intro_clips) or bgm_type != "ninguna"
                if needs_concat:
                    if _concatenate_clips(clip_paths, final_path, bgm_type, bgm_volume, codec, resolution):
                        pass
                    else:
                        import shutil
                        shutil.copy2(main_rendered_path, final_path)
                        log.warning(f"[VideoStudio] Fallback: video sin BGM/intro (concat falló).")
                else:
                    import shutil
                    shutil.copy2(main_rendered_path, final_path)
                
            if v13_bypass:
                pass # The audio is already inside the final_path
            elif job_type == "music" and audio_track_path and os.path.isfile(audio_track_path):
                import subprocess
                final_music_path = final_path.replace(".mp4", "_music.mp4")
                subprocess.run([
                    FFMPEG_EXE, "-y", "-i", final_path, "-i", audio_track_path,
                    "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                    "-shortest", final_music_path
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if os.path.isfile(final_music_path):
                    import shutil
                    shutil.move(final_music_path, final_path)
                    
                # FASE 4: Sincronización Audiovisual Automática (Beat-Syncer)
                try:
                    from core.video.beat_syncer import apply_beat_synced_fx
                    beat_fx_path = final_path.replace(".mp4", "_rhythmic.mp4")
                    if apply_beat_synced_fx(final_path, audio_track_path, beat_fx_path, fps):
                        import shutil
                        shutil.move(beat_fx_path, final_path)
                        log.info("[VideoStudio] Beat-Synced FX (Glitch rítmico) aplicados con éxito al video.")
                except Exception as b_e:
                    log.warning(f"[VideoStudio] Error aplicando Beat-Syncer: {b_e}")

            render_ok = os.path.isfile(final_path) and os.path.getsize(final_path) > 0
        elif job_type == "music" and style == "biomechanic_v13":
            # El renderizado ya se completó arriba, render_ok está seteado
            pass
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
            
            if job_type == "music":
                import shutil
                music_out_dir = r"F:\PROYECTO VIDEOCLIP MUSICAL\output"
                os.makedirs(music_out_dir, exist_ok=True)
                try:
                    shutil.copy2(final_path, os.path.join(music_out_dir, os.path.basename(final_path)))
                except Exception as c_e:
                    log.warning(f"[VideoStudio] No se pudo copiar a carpeta musical: {c_e}")
            
            thumb_path = os.path.join(OUTPUT_DIR, f'thumb_{job_id}.jpg')
            if _extract_thumbnail(final_path, thumb_path):
                _update_job(job_id, thumbnail_path=thumb_path)
                log.info(f'[VideoStudio] Thumbnail: {os.path.basename(thumb_path)}')

            try:
                script_json_path = os.path.join(job_dir, "script.json")
                with open(script_json_path, "w", encoding="utf-8") as _sf:
                    json.dump(scenes, _sf, ensure_ascii=False, indent=2)
            except Exception as _sj_e:
                log.warning(f"[VideoStudio] Error guardando script.json: {_sj_e}")

            _niche_id = ""
            _niche_lang = "es"
            try:
                from core import content_scheduler as _cs
                _niche_id = _cs._state.get("last_niche", "")
                _niche_data = _cs._load_niches()
                for _n in _niche_data.get("niches", []):
                    if _n.get("id") == _niche_id:
                        _niche_lang = _n.get("lang", "es")
                        break
            except Exception:
                pass

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

            try:
                if style in ["galactic", "biomechanic_v13", "oceanic", "protean", "interstellar", "inception_kifs", "neon_fluid", "organic_core", "turing_patterns"]:
                    log.info(f"[VideoStudio] Shorts nativos verticales 9:16 ya fueron generados por la GPU en el paso anterior.")
                    _shorts_path = final_path.replace(".mp4", "_short.mp4")
                    try:
                        if job_type == "music":
                            import shutil
                            try:
                                # Entregar versión Vertical
                                shutil.copy2(_shorts_path, os.path.join(r"F:\PROYECTO VIDEOCLIP MUSICAL\output", os.path.basename(_shorts_path)))
                                # Entregar versión Horizontal (Master original)
                                shutil.copy2(final_path, os.path.join(r"F:\PROYECTO VIDEOCLIP MUSICAL\output", os.path.basename(final_path)))
                                log.info("[VideoStudio] Copia Dual (Horizontal + Vertical) enviada al directorio de música.")
                            except: pass
                    except Exception as e_crop:
                        log.warning(f"[VideoStudio] Error generando GLSL Short con FFMPEG: {e_crop}")
                else:
                    log.info("[VideoStudio] Iniciando generación de Shorts interactivos Multi-Parte con Remotion y Whisper...")
                    from core.whisper_engine import WhisperEngine
                    from core.remotion_engine import RemotionEngine
                    import subprocess
                    
                    # 1. Obtener duración total del video maestro
                    probe_master = subprocess.run([FFMPEG_EXE, '-i', final_path], capture_output=True, text=True, errors='replace')
                    total_dur = 59.0
                    for l in probe_master.stderr.splitlines():
                        if 'Duration:' in l:
                            t = l.split('Duration:')[1].split(',')[0].strip()
                            h, m, s = t.split(':')
                            total_dur = int(h) * 3600 + int(m) * 60 + float(s)
                            break
                    
                    chunk_length = 59.0
                    num_parts = max(1, int(total_dur // chunk_length) + (1 if total_dur % chunk_length > 5 else 0))
                    
                    w_engine = WhisperEngine(model_size="base")
                    r_engine = RemotionEngine()
                    
                    for part_idx in range(num_parts):
                        start_time = part_idx * chunk_length
                        actual_length = min(chunk_length, total_dur - start_time)
                        
                        if actual_length < 5.0: # Ignorar fragmentos finales muy cortos
                            continue
                            
                        part_suffix = f"_short_part{part_idx + 1}.mp4" if num_parts > 1 else "_short.mp4"
                        _shorts_path = final_path.replace('.mp4', part_suffix)
                        temp_short_src = final_path.replace('.mp4', f'_temp_short_{part_idx}.mp4')
                        
                        # 2. Cortar el fragmento
                        cut_result = subprocess.run([
                            FFMPEG_EXE, '-y', '-ss', str(start_time), '-i', final_path, 
                            '-t', str(actual_length), '-c:v', 'copy', '-c:a', 'copy', temp_short_src
                        ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        
                        # Verificar que el corte fue exitoso
                        if not os.path.isfile(temp_short_src):
                            log.warning(f"[VideoStudio] No se pudo cortar fragmento {part_idx+1}: {temp_short_src}")
                            continue
                        
                        duration_frames = int(actual_length * REMOTION_FPS)
                        
                        # 3. Extraer palabras del fragmento
                        try:
                            words_data = w_engine.extract_words(temp_short_src, language=narration_lang[:2])
                        except Exception as w_e:
                            log.warning(f"[VideoStudio] Whisper falló en parte {part_idx+1}: {w_e}. Usando palabras vacías.")
                            words_data = []
                        
                        # 4. Renderizar Remotion
                        try:
                            props = {"videoPath": temp_short_src, "words": words_data, "durationInFrames": duration_frames}
                            output_name = os.path.basename(_shorts_path).replace('.mp4', '')
                            rendered_mp4 = r_engine.render_composition("ShortTemplate", output_name, props)
                            
                            if os.path.isfile(rendered_mp4):
                                import shutil
                                shutil.move(rendered_mp4, _shorts_path)
                                log.info(f"[VideoStudio] Short (Parte {part_idx + 1}/{num_parts}) generado: {_shorts_path}")
                                if job_type == "music":
                                    try:
                                        shutil.copy2(_shorts_path, os.path.join(r"F:\PROYECTO VIDEOCLIP MUSICAL\output", os.path.basename(_shorts_path)))
                                    except Exception as c_e:
                                        log.warning(f"[VideoStudio] No se pudo copiar short a carpeta musical: {c_e}")
                        except Exception as rem_e:
                            log.error(f"[VideoStudio] Error Remotion en parte {part_idx+1}: {rem_e}")
                        finally:
                            try:
                                os.remove(temp_short_src)
                            except:
                                pass
                            



                try:
                    from core.youtube_uploader import upload_job_async
                    if not skip_social_upload:
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

                try:
                    from core.tiktok_uploader import distribute_short_async
                    if not skip_social_upload and '_shorts_path' in locals() and _shorts_path and os.path.isfile(_shorts_path):
                        distribute_short_async(
                            job_id      = job_id,
                            shorts_path = _shorts_path,
                            title       = title or topic[:100],
                        )
                except Exception as _tt_e:
                    log.warning(f"[VideoStudio] Social distribution error: {_tt_e}")

            except Exception as _tt_e:
                log.warning(f"[VideoStudio] Social distribution wrap error: {_tt_e}")

            try:
                from core.language_cloner import clone_job_async, get_enabled_languages
                if get_enabled_languages() and job_type != "music":
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


def _worker_loop() -> None:
    """Loop continuo del worker que consulta y procesa trabajos de video de forma secuencial."""
    _init_db()
    while True:
        try:
            with _db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=DB_CONNECT_TIMEOUT)
                try:
                    conn.row_factory = sqlite3.Row
                    row  = conn.execute(
                        "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id LIMIT 1"
                    ).fetchone()
                finally:
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
                    job_type         = row["job_type"]               if "job_type"          in keys else "tts",
                    audio_track_path = row["audio_track_path"]       if "audio_track_path"  in keys else "",
                    lyrics_text      = row["lyrics_text"]            if "lyrics_text"       in keys else "",
                    input_video_path = row["input_video_path"]       if "input_video_path"  in keys else "",
                )
            else:
                time.sleep(5)

        except Exception as e:
            log.error(f"[VideoStudio] Error en worker loop: {e}")
            time.sleep(10)


def start() -> None:
    """Inicia el worker daemon de video si no estaba ya corriendo de forma thread-safe."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
        _init_db()
        t = threading.Thread(target=_worker_loop, name="GravityVideoWorker", daemon=True)
        t.start()
        log.info("[VideoStudio] Worker daemon iniciado (Gravity Studio ULTRA V15.1 PRO - Modular Pipeline).")


def get_video_url(output_path: str) -> str:
    """Convierte ruta absoluta en URL relativa para descarga."""
    if not output_path:
        return ""
    fname = os.path.basename(output_path)
    return f"/v1/video/download?file={fname}"
