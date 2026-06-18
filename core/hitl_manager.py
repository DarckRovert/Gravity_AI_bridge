"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — HITL MANAGER V16.0 PRO [Diamond Edition]                           ║
║  Interceptor de herramientas de alto riesgo.                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cuando el agente quiere ejecutar una tool sensible, la encola
en 'pending_approvals' y bloquea de manera ultraeficiente usando Eventos
de sincronización nativos hasta que el usuario aprueba/rechaza.
"""

import threading
import time
import uuid
from typing import Dict, Any, List, Optional

# ── Riesgo de tools ──────────────────────────────────────────────────────────
HIGH_RISK_TOOLS: List[str] = [
    "code_runner",
    "shell_exec",
    "file_write",
    "file_delete",
    "deploy",
    "git_push",
    "git_commit",
    "send_email",
    "send_request",
    "database_write",
]

# ── Estado global ────────────────────────────────────────────────────────────
_lock = threading.RLock()  # Cerrojo reentrante robusto
_pending: Dict[str, Dict[str, Any]] = {}   # approval_id → request
_decisions: Dict[str, str] = {}            # approval_id → "approved" | "rejected"
_events: Dict[str, threading.Event] = {}   # approval_id → Evento de suspensión
TIMEOUT_SECONDS: int = 120                 # Timeout auto-rechazo


def request_approval(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str = "default",
) -> str:
    """
    Encola una solicitud de aprobación. Retorna el approval_id.
    """
    approval_id: str = str(uuid.uuid4())[:12]
    with _lock:
        _pending[approval_id] = {
            "id":         approval_id,
            "tool":       tool_name,
            "arguments":  arguments,
            "session_id": session_id,
            "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status":     "pending",
        }
        # Crear un evento de sincronización exclusivo para esta aprobación
        _events[approval_id] = threading.Event()
    return approval_id


def wait_for_decision(approval_id: str, timeout: int = TIMEOUT_SECONDS) -> str:
    """
    Bloquea el hilo de forma nativa ultraeficiente en el kernel hasta que
    el usuario tome una decisión o el timeout expire. Elimina bucles de polling.
    """
    with _lock:
        event: Optional[threading.Event] = _events.get(approval_id)

    if not event:
        # Si el evento no existe, caer en el valor por defecto
        return "rejected"

    # Esperar de forma síncrona suspendido en el kernel sin gastar CPU
    signaled: bool = event.wait(timeout=float(timeout))

    with _lock:
        _events.pop(approval_id, None)
        if approval_id in _decisions:
            decision = _decisions.pop(approval_id)
            _pending.pop(approval_id, None)
            return decision

        # Si expiró el timeout sin decisión
        if approval_id in _pending:
            _pending[approval_id]["status"] = "timeout"
            _pending.pop(approval_id, None)
    return "timeout"


def approve(approval_id: str) -> bool:
    """El humano aprueba la acción desde el Dashboard."""
    with _lock:
        if approval_id not in _pending:
            return False
        _pending[approval_id]["status"] = "approved"
        _decisions[approval_id] = "approved"
        # Despertar de inmediato al hilo suspendido en wait_for_decision
        event = _events.get(approval_id)
        if event:
            event.set()
    return True


def reject(approval_id: str, reason: str = "") -> bool:
    """El humano rechaza la acción desde el Dashboard."""
    with _lock:
        if approval_id not in _pending:
            return False
        _pending[approval_id]["status"] = "rejected"
        _pending[approval_id]["reject_reason"] = reason
        _decisions[approval_id] = "rejected"
        # Despertar de inmediato al hilo suspendido en wait_for_decision
        event = _events.get(approval_id)
        if event:
            event.set()
    return True


def get_pending() -> List[Dict[str, Any]]:
    """Retorna la lista de solicitudes pendientes de aprobación de forma thread-safe."""
    with _lock:
        return list(_pending.values())


def is_high_risk(tool_name: str) -> bool:
    """Comprueba si una tool requiere aprobación humana."""
    return tool_name.lower() in [t.lower() for t in HIGH_RISK_TOOLS]


def intercept(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str = "default",
    bg_mode: bool = False,
) -> Dict[str, Any]:
    """
    Punto de entrada principal desde el agente.
    """
    if bg_mode or not is_high_risk(tool_name):
        return {"proceed": True, "decision": "auto", "approval_id": None}

    approval_id: str = request_approval(tool_name, arguments, session_id)
    decision: str = wait_for_decision(approval_id)

    return {
        "proceed":     decision == "approved",
        "decision":    decision,
        "approval_id": approval_id,
    }

