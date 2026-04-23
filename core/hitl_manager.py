"""
Gravity AI — HITL Manager V10.4 (Human-In-The-Loop)
Interceptor de herramientas de alto riesgo.
Cuando el agente quiere ejecutar una tool sensible, la encola
en 'pending_approvals' y bloquea hasta que el humano aprueba o rechaza
desde el Dashboard.
"""
import threading
import time
import uuid
from typing import Dict, Any, List, Optional

# ── Riesgo de tools ──────────────────────────────────────────────────────────
# tools en esta lista requieren aprobación humana antes de ejecutarse.
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
_lock = threading.Lock()
_pending: Dict[str, Dict[str, Any]] = {}   # approval_id → request
_decisions: Dict[str, str] = {}            # approval_id → "approved" | "rejected"
TIMEOUT_SECONDS = 120                      # Timeout auto-rechazo


def request_approval(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str = "default",
) -> str:
    """
    Encola una solicitud de aprobación. Retorna el approval_id.
    El llamador debe luego invocar wait_for_decision(approval_id).
    """
    approval_id = str(uuid.uuid4())[:12]
    with _lock:
        _pending[approval_id] = {
            "id":         approval_id,
            "tool":       tool_name,
            "arguments":  arguments,
            "session_id": session_id,
            "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status":     "pending",
        }
    return approval_id


def wait_for_decision(approval_id: str, timeout: int = TIMEOUT_SECONDS) -> str:
    """
    Bloquea hasta que el humano tome una decisión (aprueba/rechaza)
    o hasta que expire el timeout.
    Retorna "approved" | "rejected" | "timeout".
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with _lock:
            if approval_id in _decisions:
                decision = _decisions.pop(approval_id)
                _pending.pop(approval_id, None)
                return decision
        time.sleep(0.5)

    # Timeout → auto-rechazo
    with _lock:
        if approval_id in _pending:
            _pending[approval_id]["status"] = "timeout"
    return "timeout"


def approve(approval_id: str) -> bool:
    """El humano aprueba la acción desde el Dashboard."""
    with _lock:
        if approval_id not in _pending:
            return False
        _pending[approval_id]["status"] = "approved"
        _decisions[approval_id] = "approved"
    return True


def reject(approval_id: str, reason: str = "") -> bool:
    """El humano rechaza la acción desde el Dashboard."""
    with _lock:
        if approval_id not in _pending:
            return False
        _pending[approval_id]["status"] = "rejected"
        _pending[approval_id]["reject_reason"] = reason
        _decisions[approval_id] = "rejected"
    return True


def get_pending() -> List[Dict[str, Any]]:
    """Retorna la lista de solicitudes pendientes de aprobación."""
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
    - Si la tool no es de alto riesgo: retorna {"proceed": True} directamente.
    - Si bg_mode es True: retorna {"proceed": True} sin preguntar (modo background).
    - Si es de alto riesgo y no bg_mode: encola y bloquea esperando decisión.
    Retorna dict con keys: proceed (bool), decision (str), approval_id (str).
    """
    if bg_mode or not is_high_risk(tool_name):
        return {"proceed": True, "decision": "auto", "approval_id": None}

    approval_id = request_approval(tool_name, arguments, session_id)
    decision    = wait_for_decision(approval_id)

    return {
        "proceed":     decision == "approved",
        "decision":    decision,
        "approval_id": approval_id,
    }
