"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — LOG BUFFER V12.2 PRO                                               ║
║  Módulo extraído de game_server_manager.py (BUG-punto 4 del plan)            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Responsabilidad única: buffer circular de logs de stdout de procesos externos.
Thread-safe. Soporta múltiples fuentes por server_id.
"""

import threading
import subprocess
from collections import deque
from typing import Optional

_lock    = threading.Lock()
_buffers: dict[str, deque] = {}   # {server_id: deque(maxlen=500)}

BUFFER_SIZE = 500  # líneas por servidor


# ── Gestión de buffers ────────────────────────────────────────────────────────

def get_buffer(server_id: str) -> deque:
    """Obtiene (o crea) el buffer circular de un servidor."""
    with _lock:
        if server_id not in _buffers:
            _buffers[server_id] = deque(maxlen=BUFFER_SIZE)
        return _buffers[server_id]


def clear_buffer(server_id: str) -> None:
    """Vacía el buffer de un servidor."""
    with _lock:
        if server_id in _buffers:
            _buffers[server_id].clear()


def get_lines(server_id: str, n: int = 100) -> list[str]:
    """Devuelve las últimas n líneas del buffer de un servidor."""
    with _lock:
        buf = _buffers.get(server_id)
        if not buf:
            return []
        return list(buf)[-n:]


def has_buffer(server_id: str) -> bool:
    """Devuelve True si hay un buffer con datos para el servidor."""
    with _lock:
        return bool(_buffers.get(server_id))


# ── Thread lector de stdout ───────────────────────────────────────────────────

def start_reader(
    proc: subprocess.Popen,
    server_id: str,
    label: str,
) -> threading.Thread:
    """
    Inicia un thread daemon que captura STDOUT del proceso al buffer circular.

    Args:
        proc:      El Popen cuyo stdout se va a leer.
        server_id: Identificador del servidor (clave del buffer).
        label:     Prefijo de cada línea (ej. "WORLD", "REALM").

    Returns:
        El thread iniciado.
    """
    buf = get_buffer(server_id)

    def _reader() -> None:
        try:
            for raw_line in iter(proc.stdout.readline, b""):  # type: ignore[union-attr]
                try:
                    if isinstance(raw_line, bytes):
                        line = raw_line.decode("utf-8", errors="replace").rstrip()
                    else:
                        line = raw_line.rstrip()
                except Exception:
                    line = repr(raw_line)
                with _lock:
                    buf.append(f"[{label}] {line}")
        except Exception:
            pass  # El proceso terminó o el pipe se cerró — salir limpiamente

    t = threading.Thread(
        target=_reader,
        name=f"GravityLogReader_{server_id}_{label}",
        daemon=True,
    )
    t.start()
    return t


def init_server_buffer(server_id: str) -> None:
    """Inicializa (o resetea) el buffer de un servidor antes de arrancar."""
    with _lock:
        _buffers[server_id] = deque(maxlen=BUFFER_SIZE)
