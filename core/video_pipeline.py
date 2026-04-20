"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — VIDEO STUDIO PIPELINE V10.2                                    ║
║  Genera videos tipo documental/explainer automáticamente sin GPU dedicada.   ║
║                                                                              ║
║  Flujo completo:                                                             ║
║    1. LLM genera guión con N escenas (estructura JSON)                       ║
║    2. Fooocus (CPU) genera 1 imagen por escena vía native_trigger.py         ║
║    3. Windows SAPI (pyttsx3) convierte narración a audio .wav                ║
║    4. ffmpeg ensambla imagen + audio → clip .mp4 por escena                  ║
║    5. ffmpeg concatena todos los clips → video final .mp4                    ║
║                                                                              ║
║  Prerrequisitos (ya instalados):                                             ║
║    - ffmpeg en _integrations/ffmpeg/ffmpeg.exe                               ║
║    - pyttsx3 (pip install pyttsx3)                                           ║
║    - Fooocus corriendo en :7861                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import sqlite3
import threading
import subprocess
import tempfile
import math
from datetime import datetime, timezone
from typing import Optional

from core.logger import log

# ── Rutas absolutas del proyecto ───────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_EXE  = os.path.join(BASE_DIR, "_integrations", "ffmpeg", "ffmpeg.exe")
OUTPUT_DIR  = os.path.join(BASE_DIR, "_videos")
DB_PATH     = os.path.join(BASE_DIR, "_video_queue.sqlite")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Parámetros por defecto ─────────────────────────────────────────────────────
DEFAULT_SCENES     = 6       # Escenas por video
DEFAULT_IMG_W      = 1216    # Landscape 16:9 aproximado
DEFAULT_IMG_H      = 832
SECONDS_PER_SCENE  = 8       # Duración mínima por escena (ffmpeg la ajusta al audio)
TTS_RATE           = 150     # Palabras por minuto para la voz (150 = ritmo natural)
MAX_HISTORY        = 20      # Entradas en historial del dashboard

# ── Estado global ──────────────────────────────────────────────────────────────
_lock         = threading.Lock()
_current_job  = None   # job_id activo
_started      = False


# ── Base de datos ──────────────────────────────────────────────────────────────

def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            topic       TEXT    NOT NULL,
            n_scenes    INTEGER NOT NULL DEFAULT 6,
            voice_speed INTEGER NOT NULL DEFAULT 150,
            status      TEXT    NOT NULL DEFAULT 'pending',
            progress    INTEGER NOT NULL DEFAULT 0,
            current_step TEXT,
            output_path TEXT,
            error       TEXT,
            created_at  TEXT    NOT NULL,
            started_at  TEXT,
            finished_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_job(topic: str, n_scenes: int = DEFAULT_SCENES,
            voice_speed: int = TTS_RATE) -> int:
    """Encola un nuevo trabajo de video. Retorna el ID generado."""
    _init_db()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.execute(
        "INSERT INTO video_jobs (topic, n_scenes, voice_speed, created_at) "
        "VALUES (?, ?, ?, ?)",
        (topic, n_scenes, voice_speed, now)
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    log.info(f"[VideoStudio] Job #{job_id} encolado: {topic[:60]}")
    return job_id


def get_queue_status() -> dict:
    """Estado completo de la cola de video para el dashboard."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending  = [dict(r) for r in conn.execute(
        "SELECT * FROM video_jobs WHERE status='pending' ORDER BY id"
    ).fetchall()]
    history  = [dict(r) for r in conn.execute(
        "SELECT * FROM video_jobs WHERE status!='pending' ORDER BY id DESC LIMIT ?",
        (MAX_HISTORY,)
    ).fetchall()]
    conn.close()

    with _lock:
        current = _current_job

    return {
        "pending_count": len(pending),
        "pending_jobs":  pending,
        "current_job":   current,
        "history":       history,
        "ffmpeg_ok":     os.path.isfile(FFMPEG_EXE),
    }


def cancel_job(job_id: int) -> bool:
    """Cancela un trabajo pendiente. Retorna False si no existe o no estaba pendiente."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = conn.execute(
        "UPDATE video_jobs SET status='cancelled', finished_at=? "
        "WHERE id=? AND status='pending'",
        (now, job_id)
    ).rowcount
    conn.commit()
    conn.close()
    return rows > 0


# ── Paso 1: Generación de guión via LLM ───────────────────────────────────────

def _generate_script(topic: str, n_scenes: int) -> list[dict]:
    """
    Llama al LLM local (Ollama) para generar un guión estructurado.
    Retorna lista de dicts con 'title', 'image_prompt', 'narration'.
    Si el LLM no está disponible, genera un guión de ejemplo.
    """
    system_prompt = (
        "Eres un guionista profesional de documentales. "
        "Responde ÚNICAMENTE con JSON válido, sin texto adicional."
    )
    user_prompt = (
        f"Crea un guión de {n_scenes} escenas para un video documental sobre: '{topic}'.\n"
        "Responde con este JSON exacto (sin ningún texto antes o después):\n"
        "[\n"
        "  {\n"
        '    "title": "Título corto de la escena",\n'
        '    "image_prompt": "Descripción visual detallada en inglés para generar imagen IA. '
        'Cinematic, 16:9, high detail, photorealistic",\n'
        '    "narration": "Texto de narración en español para esta escena (2-4 oraciones)."\n'
        "  }\n"
        "]\n"
        f"Genera exactamente {n_scenes} escenas. Solo JSON, nada más."
    )

    try:
        import urllib.request
        payload = json.dumps({
            "model":    "llama3",   # Se usa el modelo que tenga Ollama disponible
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "stream":   False,
            "options":  {"temperature": 0.7, "num_ctx": 4096},
        }).encode("utf-8")

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            data    = json.loads(r.read())
            content = data.get("message", {}).get("content", "")

        # Limpiar posibles bloques de código markdown
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        scenes = json.loads(content)
        if isinstance(scenes, list) and len(scenes) > 0:
            return scenes[:n_scenes]

    except Exception as e:
        log.warning(f"[VideoStudio] LLM no disponible ({e}). Usando guión de ejemplo.")

    # Fallback: guión de ejemplo si no hay LLM
    return [
        {
            "title":        f"Escena {i+1}: {topic}",
            "image_prompt": (
                f"Cinematic documentary scene {i+1} about {topic}, "
                "photorealistic, professional lighting, 16:9 landscape, "
                "high detail, dramatic composition"
            ),
            "narration": (
                f"Esta es la escena número {i+1} de nuestro documental sobre {topic}. "
                "La exploración de este tema nos lleva a reflexionar sobre su importancia "
                "y su impacto en nuestra vida cotidiana."
            ),
        }
        for i in range(n_scenes)
    ]


# ── Paso 2: Generación de imagen vía Fooocus ──────────────────────────────────

def _generate_scene_image(prompt: str, scene_idx: int, job_id: int) -> Optional[str]:
    """
    Dispara Fooocus para generar la imagen de una escena.
    Retorna la ruta absoluta de la imagen generada o None si falla.
    """
    try:
        from tools.fooocus_client import trigger_gradio_generation
        result = trigger_gradio_generation(
            prompt=prompt,
            performance="Speed",
            aspect_ratio=f"{DEFAULT_IMG_W}*{DEFAULT_IMG_H}",
        )
        if result.get("success") and result.get("images"):
            img_path = result["images"][0]
            log.info(f"[VideoStudio] Imagen escena {scene_idx} generada: {img_path}")
            return img_path
        else:
            log.warning(f"[VideoStudio] Fooocus falló escena {scene_idx}: {result.get('error')}")
            return None
    except Exception as e:
        log.error(f"[VideoStudio] Error generando imagen escena {scene_idx}: {e}")
        return None


# ── Paso 3: Text-to-Speech ────────────────────────────────────────────────────

def _generate_audio(text: str, output_wav: str, rate: int = TTS_RATE) -> bool:
    """
    Convierte texto a audio WAV usando Windows SAPI (pyttsx3).
    Retorna True si el archivo se generó correctamente.
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)

        # Seleccionar voz en español si está disponible
        voices = engine.getProperty("voices")
        es_voice = next(
            (v for v in voices if "es" in v.id.lower() or "español" in v.name.lower()),
            None
        )
        if es_voice:
            engine.setProperty("voice", es_voice.id)

        engine.save_to_file(text, output_wav)
        engine.runAndWait()
        engine.stop()

        return os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0
    except Exception as e:
        log.error(f"[VideoStudio] Error TTS: {e}")
        return False


# ── Paso 4: Ensamblado por escena ─────────────────────────────────────────────

def _assemble_clip(image_path: str, audio_path: str, output_mp4: str) -> bool:
    """
    Combina una imagen + audio en un clip mp4.
    La duración del clip = duración del audio + 0.5s de margen.
    Si no hay audio, usa SECONDS_PER_SCENE como duración fija.
    """
    if not os.path.isfile(FFMPEG_EXE):
        log.error(f"[VideoStudio] ffmpeg no encontrado en {FFMPEG_EXE}")
        return False

    try:
        has_audio = audio_path and os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0

        if has_audio:
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-i", audio_path,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-vf", f"scale={DEFAULT_IMG_W}:{DEFAULT_IMG_H}:force_original_aspect_ratio=decrease,"
                       f"pad={DEFAULT_IMG_W}:{DEFAULT_IMG_H}:(ow-iw)/2:(oh-ih)/2:black,"
                       "fps=24",
                "-movflags", "+faststart",
                output_mp4,
            ]
        else:
            # Sin audio: imagen estática con duración fija
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(SECONDS_PER_SCENE),
                "-c:v", "libx264", "-preset", "fast",
                "-vf", f"scale={DEFAULT_IMG_W}:{DEFAULT_IMG_H}:force_original_aspect_ratio=decrease,"
                       f"pad={DEFAULT_IMG_W}:{DEFAULT_IMG_H}:(ow-iw)/2:(oh-ih)/2:black,"
                       "fps=24",
                "-movflags", "+faststart",
                output_mp4,
            ]

        result = subprocess.run(
            cmd, capture_output=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0 and os.path.isfile(output_mp4):
            log.info(f"[VideoStudio] Clip ensamblado: {os.path.basename(output_mp4)}")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-300:]
            log.error(f"[VideoStudio] ffmpeg error: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error ensamblando clip: {e}")
        return False


# ── Paso 5: Concatenación final ───────────────────────────────────────────────

def _concatenate_clips(clip_paths: list[str], output_mp4: str) -> bool:
    """
    Concatena todos los clips en el video final usando un archivo de lista ffmpeg.
    """
    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        # Solo una escena: copiar directamente
        import shutil
        shutil.copy2(clip_paths[0], output_mp4)
        return True

    try:
        # Crear archivo de lista temporal
        list_file = output_mp4 + ".list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{cp.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_mp4,
        ]
        result = subprocess.run(
            cmd, capture_output=True, timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        os.remove(list_file)

        if result.returncode == 0 and os.path.isfile(output_mp4):
            size_mb = os.path.getsize(output_mp4) / 1024 / 1024
            log.info(f"[VideoStudio] Video final: {os.path.basename(output_mp4)} ({size_mb:.1f} MB)")
            return True
        else:
            err = result.stderr.decode(errors="replace")[-300:]
            log.error(f"[VideoStudio] Concatenación fallida: {err}")
            return False
    except Exception as e:
        log.error(f"[VideoStudio] Error concatenando: {e}")
        return False


# ── Actualizador de estado en DB ──────────────────────────────────────────────

def _update_job(job_id: int, **kwargs) -> None:
    """Actualiza campos del job en SQLite. Acepta cualquier clave del schema."""
    valid = {"status", "progress", "current_step", "output_path",
             "error", "started_at", "finished_at"}
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


# ── Worker principal ──────────────────────────────────────────────────────────

def _process_job(job_id: int, topic: str, n_scenes: int, voice_speed: int) -> None:
    """
    Ejecuta el pipeline completo para un job dado.
    1. Genera guión   → 2. Genera imágenes → 3. TTS → 4. Clips → 5. Video final
    """
    global _current_job

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _update_job(job_id, status="running", started_at=now, progress=0,
                current_step="Generando guión con el LLM...")
    with _lock:
        _current_job = {"id": job_id, "topic": topic, "progress": 0,
                        "step": "Generando guión..."}

    # Carpeta temporal de trabajo para este job
    job_dir = os.path.join(OUTPUT_DIR, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    try:
        # ── PASO 1: Guión ──────────────────────────────────────────────────────
        scenes = _generate_script(topic, n_scenes)
        if not scenes:
            raise RuntimeError("El LLM no devolvió escenas válidas.")

        total_steps = n_scenes * 3 + 1  # imagen + audio + clip por escena + concat
        step        = 0

        clip_paths: list[str] = []

        for i, scene in enumerate(scenes):
            scene_num    = i + 1
            scene_title  = scene.get("title", f"Escena {scene_num}")
            img_prompt   = scene.get("image_prompt", topic)
            narration    = scene.get("narration", "")

            # ── PASO 2: Imagen ─────────────────────────────────────────────────
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando imagen: {scene_title[:40]}")
            with _lock:
                if _current_job:
                    _current_job["progress"] = pct
                    _current_job["step"]     = f"Escena {scene_num}/{n_scenes}: imagen..."

            img_path = _generate_scene_image(img_prompt, scene_num, job_id)

            # Si Fooocus no está disponible, usar imagen en negro de marcador
            if not img_path:
                placeholder = os.path.join(job_dir, f"scene_{scene_num:02d}_placeholder.png")
                _create_placeholder_image(scene_title, placeholder)
                img_path = placeholder

            # ── PASO 3: TTS ─────────────────────────────────────────────────
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Generando audio: {scene_title[:40]}")

            audio_path = os.path.join(job_dir, f"scene_{scene_num:02d}_audio.wav")
            audio_ok   = _generate_audio(narration, audio_path, voice_speed) if narration else False

            # ── PASO 4: Clip ─────────────────────────────────────────────────
            step += 1
            pct = int(step / total_steps * 100)
            _update_job(job_id, progress=pct,
                        current_step=f"[{scene_num}/{n_scenes}] Ensamblando clip...")

            clip_path = os.path.join(job_dir, f"scene_{scene_num:02d}_clip.mp4")
            if _assemble_clip(img_path, audio_path if audio_ok else None, clip_path):
                clip_paths.append(clip_path)

        # ── PASO 5: Video final ────────────────────────────────────────────────
        _update_job(job_id, progress=95, current_step="Concatenando clips en video final...")
        with _lock:
            if _current_job:
                _current_job["progress"] = 95
                _current_job["step"]     = "Concatenando video final..."

        ts          = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_topic  = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_")
        final_path  = os.path.join(OUTPUT_DIR, f"video_{job_id}_{safe_topic}_{ts}.mp4")

        if clip_paths and _concatenate_clips(clip_paths, final_path):
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _update_job(job_id, status="done", progress=100,
                        current_step="Completado", output_path=final_path,
                        finished_at=now)
            log.info(f"[VideoStudio] Job #{job_id} completado → {final_path}")
        else:
            raise RuntimeError("No se pudieron generar clips. Verifica que Fooocus esté corriendo.")

    except Exception as e:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _update_job(job_id, status="failed", error=str(e), finished_at=now,
                    current_step="Error")
        log.error(f"[VideoStudio] Job #{job_id} falló: {e}")
    finally:
        with _lock:
            _current_job = None


# ── Imagen de marcador (cuando Fooocus no está disponible) ────────────────────

def _create_placeholder_image(text: str, output_path: str) -> None:
    """Genera una imagen negra con texto usando Pillow como placeholder."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img  = Image.new("RGB", (DEFAULT_IMG_W, DEFAULT_IMG_H), color=(10, 12, 20))
        draw = ImageDraw.Draw(img)
        # Texto centrado aproximado
        draw.text((DEFAULT_IMG_W // 2, DEFAULT_IMG_H // 2),
                  text[:80], fill=(100, 100, 140), anchor="mm")
        img.save(output_path, "PNG")
    except Exception:
        # Pillow no disponible — crear archivo PNG minimal válido
        with open(output_path, "wb") as f:
            f.write(bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
                0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
                0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
                0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
                0x44, 0xAE, 0x42, 0x60, 0x82,
            ]))


# ── Worker daemon ─────────────────────────────────────────────────────────────

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
                _process_job(
                    job_id      = row["id"],
                    topic       = row["topic"],
                    n_scenes    = row["n_scenes"],
                    voice_speed = row["voice_speed"],
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
    log.info("[VideoStudio] Worker daemon iniciado.")


# ── API pública (usada por los endpoints) ─────────────────────────────────────

def get_video_url(output_path: str) -> str:
    """Convierte ruta absoluta en URL relativa del bridge para descarga."""
    if not output_path:
        return ""
    fname = os.path.basename(output_path)
    return f"/v1/video/download?file={fname}"
