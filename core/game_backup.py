"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — GAME BACKUP V16.0 PRO [Diamond-Tier Edition]                       ║
║  Módulo optimizado para copias de seguridad concurrentes de bases de datos.   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Responsabilidad única: backup/restore de bases de datos de servidores de juego.
Garantiza total exclusión mutua de I/O y portabilidad multiplataforma de procesos.
"""

import os
import subprocess
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List

log = logging.getLogger("gravity.game_backup")

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVES_DIR: str = os.path.join(BASE_DIR, "_saves")

# Cuántos backups conservar por servidor
MAX_BACKUPS_PER_SERVER: int = 5

# Cerrojo de exclusión mutua para operaciones físicas de E/S y poda concurrente
_backup_lock = threading.RLock()


def backup_database(server_id: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza un mysqldump de la base de datos de personajes de forma thread-safe.
    Guarda en _saves/backup_<server_id>_YYYYMMDD_HHMMSS.sql.
    Limpia automáticamente backups viejos si hay más de MAX_BACKUPS_PER_SERVER.

    Returns:
        Dict con claves: ok (bool), path (str|None), error (str|None)
    """
    # Calcular flags de creación portables para evitar excepciones en plataformas Unix
    creation_flags: int = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    # Verificar disponibilidad de mysqldump
    try:
        subprocess.run(
            ["mysqldump", "--version"],
            capture_output=True,
            timeout=5,
            creationflags=creation_flags,
        )
    except FileNotFoundError:
        log.debug("[GameBackup] mysqldump no disponible en PATH — backup omitido.")
        return {"ok": False, "path": None, "error": "mysqldump no disponible"}
    except Exception as e:
        return {"ok": False, "path": None, "error": str(e)}

    with _backup_lock:
        os.makedirs(SAVES_DIR, exist_ok=True)
        ts: str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file: str = os.path.join(SAVES_DIR, f"backup_{server_id}_{ts}.sql")

        db_host: str = cfg.get("db_host", "127.0.0.1")
        db_port: str = str(cfg.get("db_port", 3306))
        db_user: str = cfg.get("db_user", "mangos")
        db_pass: str = cfg.get("db_pass", "")
        if not db_pass:
            try:
                from core.key_manager import KeyManager

                db_pass = KeyManager.get_key(f"{server_id}_db_pass") or ""
            except Exception:
                pass
        db_name: str = cfg.get("db_name", "characters")

        cmd: List[str] = [
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
                    creationflags=creation_flags,
                )

            if result.returncode != 0:
                err: str = result.stderr.decode(errors="replace")[:300]
                log.warning(f"[GameBackup] mysqldump error: {err}")
                # Si falló, eliminar el archivo vacío creado
                try:
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                except Exception:
                    pass
                return {"ok": False, "path": None, "error": err}

            log.info(f"[GameBackup] Backup realizado con éxito: {backup_file}")
            _prune_old_backups(server_id)
            return {"ok": True, "path": backup_file, "error": None}

        except subprocess.TimeoutExpired:
            try:
                if os.path.exists(backup_file):
                    os.remove(backup_file)
            except Exception:
                pass
            return {"ok": False, "path": None, "error": "mysqldump timeout (120s)"}
        except Exception as e:
            log.warning(f"[GameBackup] Error inesperado en mysqldump: {e}")
            try:
                if os.path.exists(backup_file):
                    os.remove(backup_file)
            except Exception:
                pass
            return {"ok": False, "path": None, "error": str(e)}


def _prune_old_backups(server_id: str) -> None:
    """Elimina backups viejos del servidor de forma thread-safe, conservando los últimos 5."""
    with _backup_lock:
        try:
            prefix: str = f"backup_{server_id}_"
            all_baks: List[str] = sorted(
                [
                    os.path.join(SAVES_DIR, f)
                    for f in os.listdir(SAVES_DIR)
                    if f.startswith(prefix) and f.endswith(".sql")
                ]
            )
            while len(all_baks) > MAX_BACKUPS_PER_SERVER:
                oldest: str = all_baks.pop(0)
                try:
                    os.remove(oldest)
                    log.debug(f"[GameBackup] Backup antiguo eliminado: {oldest}")
                except Exception as e:
                    log.warning(
                        f"[GameBackup] No se pudo eliminar backup antiguo {oldest}: {e}"
                    )
                    break
        except Exception as e:
            log.warning(f"[GameBackup] Error podando backups viejos: {e}")


def list_backups(server_id: str) -> List[Dict[str, Any]]:
    """Lista los backups disponibles de un servidor de forma thread-safe."""
    with _backup_lock:
        if not os.path.isdir(SAVES_DIR):
            return []
        prefix: str = f"backup_{server_id}_"
        result: List[Dict[str, Any]] = []
        for fname in sorted(os.listdir(SAVES_DIR)):
            if fname.startswith(prefix) and fname.endswith(".sql"):
                fpath: str = os.path.join(SAVES_DIR, fname)
                try:
                    size_kb: float = round(os.path.getsize(fpath) / 1024, 1)
                except Exception:
                    size_kb = 0.0
                result.append(
                    {
                        "filename": fname,
                        "path": fpath,
                        "size_kb": size_kb,
                        "created_at": fname.replace(prefix, "").replace(".sql", ""),
                    }
                )
        return list(reversed(result))  # Más reciente primero
