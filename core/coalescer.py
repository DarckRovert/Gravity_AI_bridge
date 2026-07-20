"""
Gravity AI — Message Coalescer & Session Lock Manager V1.0 PRO (Mythos Edition)

Evita la ejecucion de turnos LLM concurrentes por la misma sesion y agrupa
mensajes en rafaga (debounce) para ahorrar VRAM, tokens y evitar race conditions.
"""

import threading
import time
from typing import Dict, Callable, Any, Optional, List
from core.logger import log


class SessionCoalesceEntry:
    def __init__(self):
        self.lock = threading.Lock()
        self.running: bool = False
        self.pending: bool = False
        self.pending_payloads: List[Any] = []
        self.timer: Optional[threading.Timer] = None


class MessageCoalescer:
    _instance = None
    _global_lock = threading.Lock()

    def __new__(cls):
        with cls._global_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._setup()
                cls._instance = inst
        return cls._instance

    def _setup(self):
        self._sessions: Dict[str, SessionCoalesceEntry] = {}
        self._sessions_lock = threading.Lock()

    def _get_entry(self, session_id: str) -> SessionCoalesceEntry:
        with self._sessions_lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionCoalesceEntry()
            return self._sessions[session_id]

    def schedule_turn(
        self,
        session_id: str,
        payload: Any,
        execute_fn: Callable[[str, List[Any]], None],
        debounce_ms: float = 1500.0,
    ):
        """Encola un payload para una sesión.

        Si ya hay un procesamiento corriendo, lo marca como 'pending'.
        Si hay un timer de debounce activo, lo cancela y reinicia.
        """
        entry = self._get_entry(session_id)
        with entry.lock:
            entry.pending_payloads.append(payload)

            if entry.running:
                entry.pending = True
                log.info(
                    f"[Coalescer] Sesión {session_id} ocupada. Payload encolado como pendiente."
                )
                return

            if entry.timer is not None:
                entry.timer.cancel()
                entry.timer = None

            def _on_timer_fire():
                self._dispatch_turn(session_id, execute_fn)

            entry.timer = threading.Timer(debounce_ms / 1000.0, _on_timer_fire)
            entry.timer.start()
            log.debug(
                f"[Coalescer] Timer de debounce ({debounce_ms}ms) iniciado para sesión {session_id}"
            )

    def _dispatch_turn(self, session_id: str, execute_fn: Callable[[str, List[Any]], None]):
        entry = self._get_entry(session_id)
        with entry.lock:
            entry.running = True
            entry.pending = False
            payloads = list(entry.pending_payloads)
            entry.pending_payloads.clear()
            entry.timer = None

        def _worker():
            try:
                log.info(
                    f"[Coalescer] Ejecutando turno para sesión {session_id} con {len(payloads)} payload(s)"
                )
                execute_fn(session_id, payloads)
            except Exception as e:
                log.error(
                    f"[Coalescer] Error durante ejecución de turno en sesión {session_id}: {e}"
                )
            finally:
                with entry.lock:
                    entry.running = False
                    if entry.pending:
                        # Re-encolar inmediatamente si llegaron nuevos mensajes durante la ejecución
                        log.info(
                            f"[Coalescer] Sesión {session_id} tiene turnos pendientes. Re-encolando inmediatamente..."
                        )
                        threading.Thread(
                            target=self._dispatch_turn,
                            args=(session_id, execute_fn),
                            daemon=True,
                        ).start()

        threading.Thread(target=_worker, daemon=True).start()


# Instancia singleton global
coalescer = MessageCoalescer()
