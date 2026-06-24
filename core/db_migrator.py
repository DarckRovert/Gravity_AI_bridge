"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — DB MIGRATOR V1.0                                               ║
║  Sistema de migraciones de base de datos liviano y automático.               ║
║  Se ejecuta en el arranque de bridge_server.py — sin intervención humana.   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Flujo:
  1. Al iniciar, lee todos los archivos en _migrations/<db_alias>/NNN_*.sql
  2. Compara contra la versión actual en la tabla _schema_version de cada DB
  3. Aplica solo los scripts nuevos en orden numérico
  4. Registra la versión en _schema_version

Formato de archivo: _migrations/<db_alias>/NNN_descripcion.sql
  NNN  = número de 3 dígitos (001, 002, ...)
  Cada script SQL puede contener múltiples sentencias separadas por ;
"""

import os
import glob
import sqlite3
import threading
from typing import Dict, List, Tuple
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "_migrations")
_lock = threading.RLock()

# ── Registro de bases de datos gestionadas ────────────────────────────────────
# alias → ruta relativa al BASE_DIR
# NOTA: _cache.sqlite es ephémera y gestionada por WAL checkpoint — no incluir aquí.
MANAGED_DBS: Dict[str, str] = {
    "gravity_brain": "gravity_brain.db",
    "video_queue": "_video_queue.sqlite",
    "image_queue": "_image_queue.sqlite",
}


def _get_db_path(alias: str) -> str:
    return os.path.join(BASE_DIR, MANAGED_DBS[alias])


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    """Crea la tabla _schema_version si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _schema_version (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            version     INTEGER NOT NULL DEFAULT 0,
            applied_at  TEXT NOT NULL DEFAULT (datetime('now')),
            last_migration TEXT
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO _schema_version (id, version, applied_at)
        VALUES (1, 0, datetime('now'))
    """)
    conn.commit()


def _get_current_version(conn: sqlite3.Connection) -> int:
    """Retorna la versión de schema actual de esta DB."""
    _ensure_version_table(conn)
    row = conn.execute("SELECT version FROM _schema_version WHERE id = 1").fetchone()
    return row[0] if row else 0


def _set_version(conn: sqlite3.Connection, version: int, migration_name: str) -> None:
    conn.execute(
        "UPDATE _schema_version SET version=?, applied_at=datetime('now'), last_migration=? WHERE id=1",
        (version, migration_name),
    )
    conn.commit()


def _load_pending_migrations(
    alias: str, current_version: int
) -> List[Tuple[int, str, str]]:
    """
    Retorna lista de (version_num, filename, sql_content) para scripts
    con número > current_version, ordenados ascendentemente.
    """
    migration_dir = os.path.join(MIGRATIONS_DIR, alias)
    if not os.path.isdir(migration_dir):
        return []

    pending = []
    for path in sorted(glob.glob(os.path.join(migration_dir, "*.sql"))):
        filename = os.path.basename(path)
        try:
            num = int(filename.split("_")[0])
        except (ValueError, IndexError):
            log.warning(
                f"[DBMigrator] Archivo de migración con nombre inválido: {filename}"
            )
            continue
        if num > current_version:
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
            pending.append((num, filename, sql))

    return pending


def migrate_db(alias: str) -> int:
    """
    Aplica todas las migraciones pendientes para una DB específica.
    Retorna el número de migraciones aplicadas.
    """
    db_path = _get_db_path(alias)
    if not os.path.exists(db_path):
        # La DB aún no existe — SQLite la crea al conectar, no hay migraciones que aplicar
        return 0

    with _lock:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            current = _get_current_version(conn)
            pending = _load_pending_migrations(alias, current)

            if not pending:
                return 0

            applied = 0
            for version_num, filename, sql in pending:
                log.info(
                    f"[DBMigrator] Aplicando migración [{alias}] v{version_num}: {filename}"
                )
                try:
                    # Ejecutar cada sentencia SQL del script
                    for statement in sql.split(";"):
                        stmt = statement.strip()
                        if stmt:
                            conn.execute(stmt)
                    conn.commit()
                    _set_version(conn, version_num, filename)
                    applied += 1
                    log.info(f"[DBMigrator] [{alias}] v{version_num} aplicada OK")
                except Exception as e:
                    conn.rollback()
                    log.error(
                        f"[DBMigrator] FALLO en [{alias}] v{version_num} ({filename}): {e}"
                    )
                    # Detener aquí — no aplicar migraciones posteriores si una falla
                    break

            return applied
        finally:
            conn.close()


def run_pending() -> Dict[str, int]:
    """
    Entry point principal: aplica todas las migraciones pendientes
    en todas las bases de datos gestionadas.
    Retorna dict {alias: migrations_applied}.
    """
    results: Dict[str, int] = {}
    for alias in MANAGED_DBS:
        try:
            applied = migrate_db(alias)
            if applied > 0:
                log.info(f"[DBMigrator] {alias}: {applied} migracion(es) aplicada(s)")
            results[alias] = applied
        except Exception as e:
            log.error(f"[DBMigrator] Error procesando {alias}: {e}")
            results[alias] = -1
    return results


def get_status() -> Dict[str, dict]:
    """
    Retorna el estado de migraciones de cada DB.
    Para el dashboard de Gravity.
    """
    status = {}
    for alias, rel_path in MANAGED_DBS.items():
        db_path = os.path.join(BASE_DIR, rel_path)
        migration_dir = os.path.join(MIGRATIONS_DIR, alias)
        available = 0
        if os.path.isdir(migration_dir):
            available = len(glob.glob(os.path.join(migration_dir, "*.sql")))

        if not os.path.exists(db_path):
            status[alias] = {"exists": False, "version": 0, "available": available}
            continue
        try:
            conn = sqlite3.connect(db_path)
            _ensure_version_table(conn)
            version = _get_current_version(conn)
            row = conn.execute(
                "SELECT last_migration, applied_at FROM _schema_version WHERE id=1"
            ).fetchone()
            conn.close()
            status[alias] = {
                "exists": True,
                "version": version,
                "available": available,
                "pending": available - version,
                "last_migration": row[0] if row else None,
                "applied_at": row[1] if row else None,
            }
        except Exception as e:
            status[alias] = {"exists": True, "version": -1, "error": str(e)}
    return status
