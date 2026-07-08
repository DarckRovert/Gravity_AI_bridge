"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — EDITORIAL MEMORY V1.0                                          ║
║                                                                              ║
║  Memoria editorial ligera con persistencia SQLite.                           ║
║  Previene la publicación de contenido duplicado entre ciclos del             ║
║  Periodista Autónomo (titulares RSS y topics de ensayos/ciencia).            ║
║                                                                              ║
║  API pública:                                                                ║
║    seen_headline(text, window_days)  → bool                                 ║
║    record_headline(text, source)     → None                                  ║
║    seen_topic(topic, workflow, days) → bool                                  ║
║    record_topic(topic, workflow)     → None                                  ║
║    get_stats()                       → dict                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from core.db_migrator import _get_db_path
DB_PATH = _get_db_path("gravity_brain")

_lock = threading.RLock()

# ── Inicialización del esquema ────────────────────────────────────────────────


def _get_conn() -> sqlite3.Connection:
    """Retorna una conexión al DB con row_factory configurado."""
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_schema() -> None:
    """Crea las tablas si no existen."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS editorial_headlines (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT    NOT NULL UNIQUE,
                raw_text    TEXT    NOT NULL,
                source      TEXT    DEFAULT '',
                workflow    TEXT    DEFAULT '',
                created_at  TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_headline_fp ON editorial_headlines(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_headline_ts ON editorial_headlines(created_at);

            CREATE TABLE IF NOT EXISTS editorial_topics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT    NOT NULL,
                raw_topic   TEXT    NOT NULL,
                workflow    TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_topic_fp ON editorial_topics(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_topic_wf ON editorial_topics(workflow);
            CREATE INDEX IF NOT EXISTS idx_topic_ts ON editorial_topics(created_at);
        """)


# Inicializar al importar
try:
    _init_schema()
except Exception as _init_err:
    log.warning(f"[EditorialMemory] Error inicializando schema: {_init_err}")


# ── Utilidades ────────────────────────────────────────────────────────────────


def _fingerprint(text: str) -> str:
    """
    Genera una huella normalizada del texto para comparación fuzzy.
    Elimina stopwords comunes, puntuación y mayúsculas.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Eliminar artículos y preposiciones comunes para matching más robusto
    stopwords = {
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        "de", "del", "en", "por", "para", "con", "sin", "sobre",
        "the", "a", "an", "of", "in", "for", "to", "by",
    }
    words = [w for w in text.split() if w not in stopwords]
    # Usar los primeros 10 tokens significativos como fingerprint
    return " ".join(words[:10])


# ── Headlines (titulares RSS) ─────────────────────────────────────────────────


def seen_headline(text: str, window_days: int = 7) -> bool:
    """
    Verifica si un titular ya fue publicado en la ventana de tiempo dada.

    Args:
        text: El titular a verificar.
        window_days: Ventana de tiempo en días hacia atrás (default 7).

    Returns:
        True si el titular ya fue publicado, False si es nuevo.
    """
    if not text or not text.strip():
        return False

    fp = _fingerprint(text)
    cutoff = (datetime.utcnow() - timedelta(days=window_days)).isoformat()

    try:
        with _lock:
            with _get_conn() as conn:
                row = conn.execute(
                    "SELECT id, raw_text FROM editorial_headlines "
                    "WHERE fingerprint = ? AND created_at >= ? LIMIT 1",
                    (fp, cutoff),
                ).fetchone()
        if row:
            log.info(
                f"[EditorialMemory] Titular duplicado detectado: '{text[:60]}' "
                f"(ya publicado como: '{row['raw_text'][:60]}')"
            )
            return True
        return False
    except Exception as e:
        log.warning(f"[EditorialMemory] Error verificando headline: {e}")
        return False  # Falla abierta: mejor publicar duplicado que bloquearse


def record_headline(
    text: str,
    source: str = "",
    workflow: str = "reporter",
) -> None:
    """Registra un titular como publicado."""
    if not text or not text.strip():
        return

    fp = _fingerprint(text)
    now = datetime.utcnow().isoformat()

    try:
        with _lock:
            with _get_conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO editorial_headlines "
                    "(fingerprint, raw_text, source, workflow, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (fp, text.strip(), source, workflow, now),
                )
        log.debug(f"[EditorialMemory] Titular registrado: '{text[:60]}'")
    except Exception as e:
        log.warning(f"[EditorialMemory] Error registrando headline: {e}")


# ── Topics (ensayos y ciencia) ────────────────────────────────────────────────


def seen_topic(
    topic: str,
    workflow: str = "",
    window_days: int = 14,
) -> bool:
    """
    Verifica si un topic de ensayo o artículo científico ya fue usado.

    Args:
        topic: El topic a verificar.
        workflow: Nombre del workflow (ej. 'essayist', 'scientist'). Si vacío, verifica global.
        window_days: Ventana de tiempo en días (default 14).

    Returns:
        True si el topic fue usado recientemente, False si es nuevo.
    """
    if not topic or not topic.strip():
        return False

    fp = _fingerprint(topic)
    cutoff = (datetime.utcnow() - timedelta(days=window_days)).isoformat()

    try:
        with _lock:
            with _get_conn() as conn:
                if workflow:
                    row = conn.execute(
                        "SELECT id FROM editorial_topics "
                        "WHERE fingerprint = ? AND workflow = ? AND created_at >= ? LIMIT 1",
                        (fp, workflow, cutoff),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT id FROM editorial_topics "
                        "WHERE fingerprint = ? AND created_at >= ? LIMIT 1",
                        (fp, cutoff),
                    ).fetchone()
        if row:
            log.info(f"[EditorialMemory] Topic duplicado detectado: '{topic[:60]}' (workflow={workflow})")
            return True
        return False
    except Exception as e:
        log.warning(f"[EditorialMemory] Error verificando topic: {e}")
        return False


def record_topic(topic: str, workflow: str = "") -> None:
    """Registra un topic como usado."""
    if not topic or not topic.strip():
        return

    fp = _fingerprint(topic)
    now = datetime.utcnow().isoformat()

    try:
        with _lock:
            with _get_conn() as conn:
                conn.execute(
                    "INSERT INTO editorial_topics "
                    "(fingerprint, raw_topic, workflow, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (fp, topic.strip(), workflow or "", now),
                )
        log.debug(f"[EditorialMemory] Topic registrado: '{topic[:60]}' (workflow={workflow})")
    except Exception as e:
        log.warning(f"[EditorialMemory] Error registrando topic: {e}")


# ── Stats ─────────────────────────────────────────────────────────────────────


def get_stats() -> dict:
    """Retorna estadísticas de la memoria editorial."""
    try:
        with _lock:
            with _get_conn() as conn:
                total_headlines = conn.execute(
                    "SELECT COUNT(*) FROM editorial_headlines"
                ).fetchone()[0]
                headlines_7d = conn.execute(
                    "SELECT COUNT(*) FROM editorial_headlines WHERE created_at >= ?",
                    ((datetime.utcnow() - timedelta(days=7)).isoformat(),),
                ).fetchone()[0]
                total_topics = conn.execute(
                    "SELECT COUNT(*) FROM editorial_topics"
                ).fetchone()[0]
                topics_14d = conn.execute(
                    "SELECT COUNT(*) FROM editorial_topics WHERE created_at >= ?",
                    ((datetime.utcnow() - timedelta(days=14)).isoformat(),),
                ).fetchone()[0]
                # Intentar contar libros si la tabla existe
                try:
                    total_books = conn.execute(
                        "SELECT COUNT(*) FROM editorial_books"
                    ).fetchone()[0]
                except Exception:
                    total_books = 0
        return {
            "total_headlines": total_headlines,
            "headlines_last_7d": headlines_7d,
            "total_topics": total_topics,
            "topics_last_14d": topics_14d,
            "total_books": total_books,
        }
    except Exception as e:
        log.warning(f"[EditorialMemory] Error obteniendo stats: {e}")
        return {}


# ── Books (libros generados) ──────────────────────────────────────────────────


def _init_books_table() -> None:
    """Crea la tabla de libros si no existe."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS editorial_books (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT    NOT NULL UNIQUE,
                title       TEXT    NOT NULL,
                mode        TEXT    DEFAULT 'academic',
                book_path   TEXT    DEFAULT '',
                created_at  TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_book_fp ON editorial_books(fingerprint);
        """)


try:
    _init_books_table()
except Exception as _books_err:
    log.warning(f"[EditorialMemory] Error inicializando tabla de libros: {_books_err}")


def seen_book(title: str) -> bool:
    """
    Verifica si un libro con ese título ya fue generado previamente.

    Args:
        title: Título del libro.

    Returns:
        True si ya existe, False si es nuevo.
    """
    if not title or not title.strip():
        return False

    fp = _fingerprint(title)
    try:
        with _lock:
            with _get_conn() as conn:
                row = conn.execute(
                    "SELECT id, title FROM editorial_books WHERE fingerprint = ? LIMIT 1",
                    (fp,),
                ).fetchone()
        if row:
            log.info(
                f"[EditorialMemory] Libro duplicado detectado: '{title}' "
                f"(ya existe como: '{row['title']}')"
            )
            return True
        return False
    except Exception as e:
        log.warning(f"[EditorialMemory] Error verificando libro: {e}")
        return False


def record_book(title: str, mode: str = "academic", book_path: str = "") -> None:
    """Registra un libro como generado."""
    if not title or not title.strip():
        return

    fp = _fingerprint(title)
    now = datetime.utcnow().isoformat()

    try:
        with _lock:
            with _get_conn() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO editorial_books "
                    "(fingerprint, title, mode, book_path, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (fp, title.strip(), mode, book_path, now),
                )
        log.debug(f"[EditorialMemory] Libro registrado: '{title}' ({mode})")
    except Exception as e:
        log.warning(f"[EditorialMemory] Error registrando libro: {e}")
