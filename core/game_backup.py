"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — GAME BACKUP V12.1                                              ║
║  Módulo extraído de game_server_manager.py (BUG-punto 4 del plan)            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Responsabilidad única: backup/restore de bases de datos de servidores de juego.
"""

import os
import subprocess
import logging
from datetime import datetime

log = logging.getLogger("gravity.game_backup")

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES_DIR = os.path.join(BASE_DIR, "_saves")

# Cuántos backups conservar por servidor
MAX_BACKUPS_PER_SERVER = 5


def backup_database(server_id: str, cfg: dict) -> dict:
    """
    Realiza un mysqldump de la base de datos de personajes.
    Guarda en _saves/backup_<server_id>_YYYYMMDD_HHMMSS.sql.
    Limpia automáticamente backups viejos si hay más de MAX_BACKUPS_PER_SERVER.

    Returns:
        dict con claves: ok (bool), path (str|None), error (str|None)
    """
    # Verificar disponibilidad de mysqldump
    try:
        subprocess.run(
            ["mysqldump", "--version"],
            capture_output=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except FileNotFoundError:
        log.debug("[GameBackup] mysqldump no disponible en PATH — backup omitido.")
        return {"ok": False, "path": None, "error": "mysqldump no disponible"}
    except Exception as e:
        return {"ok": False, "path": None, "error": str(e)}

    os.makedirs(SAVES_DIR, exist_ok=True)
    ts          = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(SAVES_DIR, f"backup_{server_id}_{ts}.sql")

    db_host = cfg.get("db_host", "127.0.0.1")
    db_port = str(cfg.get("db_port", 3306))
    db_user = cfg.get("db_user", "mangos")
    db_pass = cfg.get("db_pass", "")
    db_name = cfg.get("db_name", "characters")

    cmd = [
        "mysqldump",
        f"--host={db_host}",
        f"--port={db_port}",
        f"--user={db_user}",
        f"--password={db_pass}" if db_pass else "--skip-password",
        db_name,
    ]

    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        if result.returncode != 0:
            err = result.stderr.decode(errors="replace")[:300]
            log.warning(f"[GameBackup] mysqldump error: {err}")
            return {"ok": False, "path": None, "error": err}

        log.info(f"[GameBackup] Backup realizado: {backup_file}")
        _prune_old_backups(server_id)
        return {"ok": True, "path": backup_file, "error": None}

    except subprocess.TimeoutExpired:
        return {"ok": False, "path": None, "error": "mysqldump timeout (120s)"}
    except Exception as e:
        log.warning(f"[GameBackup] Error inesperado: {e}")
        return {"ok": False, "path": None, "error": str(e)}


def _prune_old_backups(server_id: str) -> None:
    """Elimina backups viejos del servidor, conservando los últimos MAX_BACKUPS_PER_SERVER."""
    try:
        prefix   = f"backup_{server_id}_"
        all_baks = sorted(
            [
                os.path.join(SAVES_DIR, f)
                for f in os.listdir(SAVES_DIR)
                if f.startswith(prefix) and f.endswith(".sql")
            ]
        )
        while len(all_baks) > MAX_BACKUPS_PER_SERVER:
            oldest = all_baks.pop(0)
            try:
                os.remove(oldest)
                log.debug(f"[GameBackup] Backup antiguo eliminado: {oldest}")
            except Exception as e:
                log.warning(f"[GameBackup] No se pudo eliminar {oldest}: {e}")
                break
    except Exception as e:
        log.warning(f"[GameBackup] Error en prune: {e}")


def list_backups(server_id: str) -> list[dict]:
    """Lista los backups disponibles de un servidor."""
    if not os.path.isdir(SAVES_DIR):
        return []
    prefix = f"backup_{server_id}_"
    result = []
    for fname in sorted(os.listdir(SAVES_DIR)):
        if fname.startswith(prefix) and fname.endswith(".sql"):
            fpath = os.path.join(SAVES_DIR, fname)
            result.append({
                "filename":  fname,
                "path":      fpath,
                "size_kb":   round(os.path.getsize(fpath) / 1024, 1),
                "created_at": fname.replace(prefix, "").replace(".sql", ""),
            })
    return list(reversed(result))  # más reciente primero
