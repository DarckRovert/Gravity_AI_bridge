"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — CACHE ENGINE V7.0 (SQLite)                  ║
║     Evita re-consultar la IA para queries idénticos         ║
╚══════════════════════════════════════════════════════════════╝
Especialmente útil en cloud providers (ahorra dinero).
Usa SQLite como backend — sin dependencias externas.
"""

import sqlite3
import hashlib
import json
import time
import os
import threading

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CACHE_DB    = os.path.join(BASE_DIR, "_cache.sqlite")
_db_lock    = threading.Lock()
_enabled    = True
DEFAULT_TTL = 24 * 3600  # 24 hours


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key   TEXT PRIMARY KEY,
            value REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def _make_key(messages: list[dict], model: str) -> str:
    """Deterministic hash of the message chain + model."""
    payload = json.dumps({"messages": messages, "model": model}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


class CacheEngine:
    """
    SQLite-backed response cache for Gravity AI.

    Keyed by SHA-256 of (messages + model). TTL-based expiry.
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
        if not _enabled:
            return None
        key = _make_key(messages, model)
        with _db_lock:
            try:
                conn = _get_connection()
                row  = conn.execute(
                    "SELECT response, expires_at FROM cache WHERE key = ?", (key,)
                ).fetchone()
                if row and row[1] > time.time():
                    conn.execute("UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?", (key,))
                    conn.execute(
                        "INSERT OR REPLACE INTO stats (key, value) "
                        "VALUES ('hits', COALESCE((SELECT value FROM stats WHERE key='hits'),0)+1)"
                    )
                    conn.commit()
                    return row[0]
                elif row:
                    # Expired
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
            except Exception:
                pass
            # Record miss
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO stats (key, value) "
                    "VALUES ('misses', COALESCE((SELECT value FROM stats WHERE key='misses'),0)+1)"
                )
                conn.commit()
            except Exception:
                pass
        return None

    @staticmethod
    def set(messages: list[dict], model: str, response: str,
            provider: str = "", ttl: int = DEFAULT_TTL) -> None:
        if not _enabled:
            return
        key = _make_key(messages, model)
        with _db_lock:
            try:
                conn = _get_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, response, model, provider, created_at, expires_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (key, response, model, provider, time.time(), time.time() + ttl)
                )
                conn.commit()
            except Exception:
                pass

    @staticmethod
    def clear() -> int:
        """Deletes all cached entries. Returns count deleted."""
        with _db_lock:
            try:
                conn  = _get_connection()
                count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
                conn.execute("DELETE FROM cache")
                conn.execute("DELETE FROM stats")
                conn.commit()
                return count
            except Exception:
                return 0

    @staticmethod
    def clear_expired() -> int:
        """Cleans up expired entries. Returns count deleted."""
        with _db_lock:
            try:
                conn  = _get_connection()
                count = conn.execute(
                    "SELECT COUNT(*) FROM cache WHERE expires_at <= ?", (time.time(),)
                ).fetchone()[0]
                conn.execute("DELETE FROM cache WHERE expires_at <= ?", (time.time(),))
                conn.commit()
                return count
            except Exception:
                return 0

    @staticmethod
    def stats() -> dict:
        """Returns cache statistics."""
        with _db_lock:
            try:
                conn   = _get_connection()
                total  = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
                size   = os.path.getsize(CACHE_DB) // 1024  # KB
                rows   = conn.execute("SELECT key, value FROM stats").fetchall()
                st     = {r[0]: r[1] for r in rows}
                hits   = int(st.get("hits",   0))
                misses = int(st.get("misses", 0))
                total_req = hits + misses
                hit_rate  = (hits / total_req * 100) if total_req > 0 else 0.0
                return {
                    "entries":  total,
                    "size_kb":  size,
                    "hits":     hits,
                    "misses":   misses,
                    "hit_rate": f"{hit_rate:.1f}%",
                    "enabled":  _enabled,
                }
            except Exception:
                return {"entries": 0, "size_kb": 0, "hits": 0, "misses": 0,
                        "hit_rate": "0%", "enabled": _enabled}
