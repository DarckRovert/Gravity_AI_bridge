"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — CACHE ENGINE V7.1                           ║
║     Optimized with WAL mode and Reasoning-Aware Hashing      ║
╚══════════════════════════════════════════════════════════════╝
"""

import sqlite3
import hashlib
import json
import time
import os
import threading
import re

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CACHE_DB    = os.path.join(BASE_DIR, "_cache.sqlite")
_db_lock    = threading.Lock()
_enabled    = True
DEFAULT_TTL = 24 * 3600  # 24 hours

# ── Hash Sanitizer (V7.1) ──────────────────────────────────────────────────
def _sanitize_content(text: str) -> str:
    """Removes reasoning blocks to ensure deterministic hashing of intent."""
    patterns = [r"<think>.*?</think>", r"<\|canal\|>pensamiento.*?<channel\|>"]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.DOTALL)
    return text.strip()

def _get_connection() -> sqlite3.Connection:
    """Returns a connection with WAL mode enabled for concurrent R/W."""
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            response   TEXT NOT NULL,
            model      TEXT NOT NULL,
            provider   TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            hit_count  INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value REAL NOT NULL)")
    conn.commit()
    return conn

def _make_key(messages: list[dict], model: str) -> str:
    """Deterministic hash of sanitized message chain + model."""
    sanitized = []
    for m in messages:
        sanitized.append({
            "role": m.get("role", "user"),
            "content": _sanitize_content(m.get("content", ""))
        })
    payload = json.dumps({"messages": sanitized, "model": model}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

class CacheEngine:
    """
    V7.1 Optimized SQLite Cache.
    Features: WAL Mode, Thread-Safe, Reasoning-Aware Hashing.
    """

    @staticmethod
    def enable():
        global _enabled
        _enabled = True

    @staticmethod
    def disable():
        global _enabled
        _enabled = False

    @staticmethod
    def is_enabled() -> bool:
        return _enabled

    @staticmethod
    def get(messages: list[dict], model: str) -> str | None:
        if not _enabled: return None
        key = _make_key(messages, model)
        with _db_lock:
            try:
                with _get_connection() as conn:
                    row = conn.execute(
                        "SELECT response, expires_at FROM cache WHERE key = ?", (key,)
                    ).fetchone()
                    if row and row[1] > time.time():
                        conn.execute("UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?", (key,))
                        conn.execute(
                            "INSERT OR REPLACE INTO stats (key, value) "
                            "VALUES ('hits', COALESCE((SELECT value FROM stats WHERE key='hits'),0)+1)"
                        )
                        return row[0]
                    elif row:
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            except Exception: pass
            
            # Miss tracking
            try:
                with _get_connection() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO stats (key, value) "
                        "VALUES ('misses', COALESCE((SELECT value FROM stats WHERE key='misses'),0)+1)"
                    )
            except Exception: pass
        return None

    @staticmethod
    def set(messages: list[dict], model: str, response: str, provider: str = "", ttl: int = DEFAULT_TTL) -> None:
        if not _enabled: return
        key = _make_key(messages, model)
        with _db_lock:
            try:
                with _get_connection() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO cache (key, response, model, provider, created_at, expires_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (key, response, model, provider, time.time(), time.time() + ttl)
                    )
            except Exception: pass

    @staticmethod
    def clear() -> int:
        with _db_lock:
            try:
                with _get_connection() as conn:
                    count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
                    conn.execute("DELETE FROM cache")
                    conn.execute("DELETE FROM stats")
                    return count
            except Exception: return 0

    @staticmethod
    def clear_expired() -> int:
        """Cleans up expired entries. Returns count deleted."""
        with _db_lock:
            try:
                with _get_connection() as conn:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM cache WHERE expires_at <= ?", (time.time(),)
                    ).fetchone()[0]
                    conn.execute("DELETE FROM cache WHERE expires_at <= ?", (time.time(),))
                    return count
            except Exception:
                return 0

    @staticmethod
    def stats() -> dict:
        with _db_lock:
            try:
                with _get_connection() as conn:
                    total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
                    size  = os.path.getsize(CACHE_DB) // 1024
                    rows  = conn.execute("SELECT key, value FROM stats").fetchall()
                    st    = {r[0]: r[1] for r in rows}
                    hits, misses = int(st.get("hits", 0)), int(st.get("misses", 0))
                    total_req = hits + misses
                    return {
                        "entries": total, "size_kb": size, "hits": hits, "misses": misses,
                        "hit_rate": f"{(hits/total_req*100) if total_req > 0 else 0:.1f}%",
                        "enabled": _enabled
                    }
            except Exception:
                return {"entries": 0, "size_kb": 0, "hits": 0, "misses": 0, "hit_rate": "0%", "enabled": _enabled}
