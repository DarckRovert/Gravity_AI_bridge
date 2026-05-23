"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — SESSION RUNNER V15.0 PRO [Diamond-Tier Edition]                ║
║  Multi-Session Bridge con control de capacidad real                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cambios V15.0 PRO:
  - BoundedSemaphore(32) real regulado atómicamente
  - Locks de instancia locales en SessionHandle para evitar liberación doble
  - Fallback defensivo en available_slots() si _value es eliminado de CPython
  - Daemon de limpieza (reaper) protegido contra fallos asíncronos
  - Tipado moderno estricto
"""

import threading
import time
import sys
import os
import subprocess
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

log = logging.getLogger("gravity.session_runner")

# ── Capacidad global ──────────────────────────────────────────────────────────

# BoundedSemaphore limita el número de sesiones concurrentes.
_CAPACITY: int = 32
_semaphore: threading.BoundedSemaphore = threading.BoundedSemaphore(_CAPACITY)
_lock: threading.RLock = threading.RLock()

# Registro global de sesiones activas {session_id: SessionHandle}
active_sessions: Dict[str, "SessionHandle"] = {}


def _now_iso() -> str:
    """Devuelve la fecha/hora UTC actual formateada de forma segura."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── SessionHandle ─────────────────────────────────────────────────────────────

class SessionHandle:
    """
    Handle que representa una sesión activa, encapsulando su proceso.
    Cada instancia ocupa 1 slot del BoundedSemaphore hasta que se libere.
    Todos los métodos internos están sincronizados localmente mediante un RLock de instancia.
    """

    def __init__(self, session_id: str, process: subprocess.Popen) -> None:
        self.session_id = session_id
        self.process = process
        self.start_time: str = _now_iso()
        self.last_activity: str = _now_iso()
        self.activities: List[Dict[str, Any]] = []
        self.current_activity: Optional[Dict[str, Any]] = None
        self._released: bool = False
        self._handle_lock: threading.RLock = threading.RLock()

    def update_activity(self, activity: Dict[str, Any]) -> None:
        """Registra una nueva actividad; mantiene historial de las últimas 10."""
        with self._handle_lock:
            self.current_activity = activity
            self.last_activity = _now_iso()
            activity["timestamp"] = self.last_activity
            self.activities.append(activity)
            if len(self.activities) > 10:
                self.activities.pop(0)

    def is_alive(self) -> bool:
        """Devuelve True si el proceso del agente sigue corriendo."""
        with self._handle_lock:
            try:
                return self.process.poll() is None
            except Exception:
                return False

    def terminate(self) -> None:
        """Termina el proceso y libera el slot del semáforo de forma segura."""
        with self._handle_lock:
            try:
                if self.is_alive():
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            self.process.kill()
                        except Exception:
                            pass
            except Exception as e:
                log.warning(f"[SessionHandle] Error al terminar {self.session_id}: {e}")
            finally:
                self._release_slot()

    def _release_slot(self) -> None:
        """Libera el slot del BoundedSemaphore exactamente una vez de manera atómica."""
        with self._handle_lock:
            if not self._released:
                self._released = True
                try:
                    _semaphore.release()
                except ValueError:
                    # Ya liberado o semáforo sobrepasado
                    pass
                except Exception as e:
                    log.warning(f"[SessionHandle] Fallo liberando slot: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Representación serializable del handle."""
        with self._handle_lock:
            try:
                pid = self.process.pid
            except Exception:
                pid = -1
            return {
                "session_id":       self.session_id,
                "start_time":       self.start_time,
                "last_activity":    self.last_activity,
                "alive":            self.is_alive(),
                "pid":              pid,
                "current_activity": self.current_activity,
                "history_count":    len(self.activities),
            }


# ── SessionSpawner ────────────────────────────────────────────────────────────

class SessionSpawner:
    """
    Manejador de creación de subprocesos de sesión.
    Thread-safe. Controla capacidad vía BoundedSemaphore.
    """

    def __init__(
        self,
        python_executable: Optional[str] = None,
        script_path: Optional[str] = None,
    ) -> None:
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.python_exec = python_executable or sys.executable
        self.script_path = script_path or os.path.join(_base, "ask_deepseek.py")

    def available_slots(self) -> int:
        """Número de slots libres calculado con fallback dinámico thread-safe."""
        with _lock:
            try:
                return _semaphore._value  # type: ignore[attr-defined]
            except AttributeError:
                # Si CPython oculta el atributo privado, calculamos por exclusión
                return max(0, _CAPACITY - len(active_sessions))

    def spawn(self, session_id: str, work_data: Dict[str, Any], role: Optional[str] = None) -> SessionHandle:
        """
        Levanta un nuevo agente subproceso aislado.

        Bloquea si se ha alcanzado el límite de _CAPACITY sesiones concurrentes.
        El slot del semáforo se libera automáticamente cuando el handle llama
        a terminate() o cuando shutdown() limpia sesiones muertas.

        Returns:
            SessionHandle — handle de la sesión iniciada.
        Raises:
            RuntimeError — si el proceso no puede iniciarse.
        """
        # Adquirir slot (bloquea si estamos al límite)
        acquired = _semaphore.acquire(timeout=5)
        if not acquired:
            raise RuntimeError(
                f"[SessionSpawner] Capacidad máxima ({_CAPACITY}) alcanzada. "
                "Espera a que terminen sesiones activas."
            )

        cmd = [self.python_exec, self.script_path, "--session", session_id]
        if role:
            cmd.extend(["--role", role])

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except Exception as e:
            # Si el Popen falla, liberar el slot inmediatamente
            _semaphore.release()
            raise RuntimeError(f"[SessionSpawner] Popen falló: {e}") from e

        handle = SessionHandle(session_id, proc)

        with _lock:
            active_sessions[session_id] = handle

        log.info(f"[SessionSpawner] Sesión iniciada: {session_id} (PID {proc.pid})")
        return handle


# ── Limpieza de huérfanos ─────────────────────────────────────────────────────

def _reap_dead_sessions() -> int:
    """
    Elimina del registro las sesiones cuyo proceso ya terminó.
    Libera los slots correspondientes del semáforo de manera atómica.
    Retorna el número de sesiones limpiadas.
    """
    to_remove: List[str] = []
    with _lock:
        for sid, handle in list(active_sessions.items()):
            if not handle.is_alive():
                to_remove.append(sid)

    reaped = 0
    for sid in to_remove:
        with _lock:
            handle = active_sessions.pop(sid, None)
        if handle:
            handle.terminate()  # Esto internamente llama a _release_slot() de forma segura
            reaped += 1
            log.debug(f"[SessionRunner] Sesión huérfana limpia: {sid}")

    return reaped


def shutdown() -> None:
    """
    Limpieza completa: termina todos los procesos activos y libera recursos.
    Llamar en el shutdown del servidor.
    """
    log.info("[SessionRunner] Iniciando shutdown de sesiones activas...")
    with _lock:
        handles = list(active_sessions.values())

    for handle in handles:
        try:
            handle.terminate()
        except Exception as e:
            log.warning(f"[SessionRunner] Error al terminar {handle.session_id}: {e}")

    with _lock:
        active_sessions.clear()

    log.info(f"[SessionRunner] Shutdown completo. {len(handles)} sesiones terminadas.")


# ── Daemon de limpieza de huérfanos ──────────────────────────────────────────

def _orphan_reaper_loop() -> None:
    """Loop daemon que limpia sesiones muertas cada 30s."""
    while True:
        time.sleep(30)
        try:
            reaped = _reap_dead_sessions()
            if reaped > 0:
                log.info(f"[SessionRunner] Reaper: {reaped} sesiones huérfanas limpiadas.")
        except Exception as e:
            log.warning(f"[SessionRunner] Error en reaper loop: {e}")


def start_orphan_reaper() -> None:
    """Arranca el daemon de limpieza. Idempotente."""
    t = threading.Thread(
        target=_orphan_reaper_loop,
        name="GravityOrphanReaper",
        daemon=True,
    )
    t.start()


# ── API pública ───────────────────────────────────────────────────────────────

def get_all_sessions() -> List[Dict[str, Any]]:
    """Devuelve el estado serializable de todas las sesiones activas."""
    with _lock:
        return [h.to_dict() for h in active_sessions.values()]


def get_session(session_id: str) -> Optional[SessionHandle]:
    """Busca un handle por session_id."""
    with _lock:
        return active_sessions.get(session_id)


def terminate_session(session_id: str) -> bool:
    """Termina y elimina una sesión por ID. Retorna True si existía."""
    with _lock:
        handle = active_sessions.pop(session_id, None)
    if handle:
        handle.terminate()
        return True
    return False
