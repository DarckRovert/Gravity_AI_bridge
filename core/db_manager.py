"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             GRAVITY AI — DB MANAGER V1.0 PRO [Resilience Layer]              ║
║         Gestor Centralizado de Conexiones SQLite con Resiliencia WAL         ║
╚══════════════════════════════════════════════════════════════════════════════╝
Maneja bloqueos concurrentes de disco en Windows mediante:
  - Reintentos con retroceso exponencial (Exponential Backoff).
  - Activación forzada de WAL (Write-Ahead Logging) y busy_timeout=30000ms.
  - Context Manager thread-safe con cierre garantizado de cursores/conexiones.
"""

import time
import functools
import sqlite3
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger("gravity.db")


def sqlite_retry(max_retries: int = 5, initial_delay: float = 0.05, backoff: float = 2.0):
    """
    Decorador para reintentar operaciones de SQLite que fallen por 'database is locked' o 'busy'.
    Previene caídas por contención en Windows.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_err = e
                    err_msg = str(e).lower()
                    if "locked" in err_msg or "busy" in err_msg:
                        if attempt == max_retries:
                            logger.error(f"[SQLiteRetry] Excedido límite de {max_retries} reintentos en {func.__name__}: {e}")
                            raise
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        raise
                except Exception:
                    raise
            raise last_err  # type: ignore[misc]
        return wrapper
    return decorator


def get_connection(
    db_path: str,
    timeout: float = 30.0,
    check_same_thread: bool = False,
    wal_mode: bool = True
) -> sqlite3.Connection:
    """
    Obtiene una conexión a SQLite optimizada para concurrencia y tolerancia a fallos en Windows.
    """
    conn = sqlite3.connect(
        db_path,
        timeout=timeout,
        check_same_thread=check_same_thread
    )
    if wal_mode:
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
        except sqlite3.OperationalError:
            pass
    return conn


class SafeDBContext:
    """
    Context manager seguro para transacciones SQLite.
    Asegura commit automático en éxito, rollback en fallo y cierre de conexión.
    """
    def __init__(self, db_path: str, timeout: float = 30.0, check_same_thread: bool = False):
        self.db_path = db_path
        self.timeout = timeout
        self.check_same_thread = check_same_thread
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self.conn = get_connection(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=self.check_same_thread
        )
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except Exception as e:
                logger.warning(f"[SafeDBContext] Error en commit/rollback: {e}")
            finally:
                try:
                    self.conn.close()
                except Exception:
                    pass
        return False
