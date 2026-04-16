"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — IMAGE QUEUE V9.4                                        ║
║         Cola persistente SQLite para generación secuencial de imágenes       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Sustituye el modelo de bloqueo síncrono de /v1/generate.
Los trabajos se encolan en SQLite y se procesan 1 a 1 en un daemon thread.
Esto evita que el servidor HTTP se bloquee durante la generación en CPU.

Endpoints integrados en bridge_server:
  POST /v1/queue/add   — Añadir trabajo a la cola
  GET  /v1/queue       — Estado actual de la cola + último historial
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "_image_queue.sqlite")

# ── Schema ─────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS image_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    started_at  TEXT,
    finished_at TEXT,
    status      TEXT    NOT NULL DEFAULT 'pending',
    prompt      TEXT    NOT NULL,
    performance TEXT    NOT NULL DEFAULT 'Speed',
    width       INTEGER NOT NULL DEFAULT 1024,
    height      INTEGER NOT NULL DEFAULT 1024,
    result_json TEXT,
    error       TEXT
);
"""

_lock = threading.Lock()
_started = False
_current_job: Optional[dict] = None


# ── DB Helpers ─────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _get_conn() as conn:
        conn.executescript(_SCHEMA)


# ── API Pública ────────────────────────────────────────────────────────────────

def add_job(prompt: str, performance: str = "Speed",
            width: int = 1024, height: int = 1024) -> int:
    """
    Encola un trabajo de generación de imagen.
    Retorna el ID del trabajo asignado.
    """
    now = datetime.utcnow().isoformat() + "Z"
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO image_jobs (created_at, status, prompt, performance, width, height) "
            "VALUES (?, 'pending', ?, ?, ?, ?)",
            (now, prompt, performance, width, height)
        )
        return cur.lastrowid


def get_queue_status() -> dict:
    """Retorna el estado completo de la cola y el historial reciente."""
    with _get_conn() as conn:
        pending = conn.execute(
            "SELECT * FROM image_jobs WHERE status='pending' ORDER BY id ASC"
        ).fetchall()

        history = conn.execute(
            "SELECT * FROM image_jobs WHERE status != 'pending' "
            "ORDER BY id DESC LIMIT 20"
        ).fetchall()

    with _lock:
        current = dict(_current_job) if _current_job else None

    return {
        "current_job": current,
        "pending_count": len(pending),
        "pending_jobs": [dict(r) for r in pending],
        "history": [dict(r) for r in history],
    }


def cancel_job(job_id: int) -> bool:
    """Cancela un trabajo pendiente (no puede cancelar el que está en proceso)."""
    with _get_conn() as conn:
        cur = conn.execute(
            "UPDATE image_jobs SET status='cancelled', "
            "finished_at=? WHERE id=? AND status='pending'",
            (datetime.utcnow().isoformat() + "Z", job_id)
        )
        return cur.rowcount > 0


# ── Worker ─────────────────────────────────────────────────────────────────────

def _process_job(job: sqlite3.Row) -> None:
    """Procesa un trabajo individual usando fooocus_client."""
    global _current_job
    job_id = job["id"]

    # Marcar como en progreso
    with _get_conn() as conn:
        conn.execute(
            "UPDATE image_jobs SET status='running', started_at=? WHERE id=?",
            (datetime.utcnow().isoformat() + "Z", job_id)
        )

    with _lock:
        _current_job = {
            "id":      job_id,
            "prompt":  job["prompt"],
            "status":  "running",
            "started": datetime.utcnow().isoformat() + "Z",
        }

    try:
        # Import del cliente de Fooocus
        import sys
        tools_dir = os.path.join(BASE_DIR, "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from fooocus_client import generate_image, ImageGenRequest

        req: ImageGenRequest = {
            "prompt":      job["prompt"],
            "performance": job["performance"],
            "width":       job["width"],
            "height":      job["height"],
            "num_images":  1,
        }
        result = generate_image(req)

        result_str = json.dumps(result, ensure_ascii=False)
        status     = "done" if result.get("success") else "failed"
        error_msg  = result.get("error") if not result.get("success") else None

        with _get_conn() as conn:
            conn.execute(
                "UPDATE image_jobs SET status=?, finished_at=?, result_json=?, error=? WHERE id=?",
                (status, datetime.utcnow().isoformat() + "Z", result_str, error_msg, job_id)
            )

    except Exception as e:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE image_jobs SET status='failed', finished_at=?, error=? WHERE id=?",
                (datetime.utcnow().isoformat() + "Z", str(e), job_id)
            )
    finally:
        with _lock:
            _current_job = None


def _worker_loop() -> None:
    """Loop del worker: obtiene y procesa trabajos pendientes 1 a 1."""
    while True:
        try:
            with _get_conn() as conn:
                job = conn.execute(
                    "SELECT * FROM image_jobs WHERE status='pending' ORDER BY id ASC LIMIT 1"
                ).fetchone()

            if job:
                _process_job(job)
            else:
                time.sleep(3)  # Esperar 3s antes de volver a consultar la cola

        except Exception:
            time.sleep(5)


# ── Arranque ───────────────────────────────────────────────────────────────────

def start() -> None:
    """Inicializa la base de datos y arranca el worker daemon."""
    global _started
    if _started:
        return
    _started = True

    _init_db()

    t = threading.Thread(
        target=_worker_loop,
        name="GravityImageQueueWorker",
        daemon=True,
    )
    t.start()
