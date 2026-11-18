"""
core/parallel_orchestrator.py — GRAVITY AI V30.3
Dispatcher asíncrono con Shared Contract Protocol.
Despacha tareas distintas a múltiples subagentes especializados en paralelo.
"""
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from core.logger import log
from core.subagent_loader import AgentDefinition, discover_agents

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ORCH_LOCK = threading.RLock()
_active: Dict[str, "OrchestrationHandle"] = {}
_TTL_SECONDS = 3600  # 1 hora — orquestaciones finalizadas se podan tras este tiempo


@dataclass
class AgentResult:
    """Resultado por agente dentro de una orquestación.

    Cada AgentResult tiene su propio RLock para escrituras atómicas.
    compare=False, repr=False evitan que el lock rompa __eq__ y __hash__.
    """
    agent_name: str
    status: str = "pending"   # pending | running | done | failed
    output: str = ""
    error: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    model_used: str = ""
    provider_used: str = ""
    _lock: threading.RLock = field(
        default_factory=threading.RLock, compare=False, repr=False
    )


@dataclass
class OrchestrationHandle:
    """Handle de una orquestación. Acceso concurrente protegido por _lock."""
    orchestration_id: str
    goal: str
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    shared_contract: str = ""
    status: str = "running"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    _lock: threading.RLock = field(
        default_factory=threading.RLock, compare=False, repr=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialización thread-safe.

        Cada AgentResult se lee dentro de su propio lock (r._lock) para máxima granularidad.
        """
        with self._lock:
            handle_snap = {
                "orchestration_id": self.orchestration_id,
                "goal": self.goal[:200],
                "status": self.status,
                "created_at": self.created_at,
                "finished_at": self.finished_at,
            }
        agents_snap: Dict[str, Any] = {}
        for n, r in self.agent_results.items():
            with r._lock:
                agents_snap[n] = {
                    "status": r.status,
                    "model": r.model_used,
                    "provider": r.provider_used,
                    "output_preview": r.output[:300],
                    "error": r.error,
                    "started_at": r.started_at,
                    "finished_at": r.finished_at,
                }
        handle_snap["agents"] = agents_snap
        return handle_snap


def _prune_stale() -> None:
    """Elimina orquestaciones finalizadas con más de _TTL_SECONDS de antigüedad.

    Llamada al inicio de cada dispatch() para evitar que _active crezca sin límite.
    """
    now = time.time()
    to_delete = []
    with _ORCH_LOCK:
        for orch_id, handle in _active.items():
            if handle.finished_at is None:
                continue
            try:
                ts = datetime.fromisoformat(handle.finished_at).timestamp()
                if now - ts > _TTL_SECONDS:
                    to_delete.append(orch_id)
            except (ValueError, TypeError):
                pass
        for orch_id in to_delete:
            del _active[orch_id]
    if to_delete:
        log.debug(f"[ParallelOrchestrator] _prune_stale: eliminadas {len(to_delete)} orquestaciones antiguas.")


def _build_shared_contract(goal: str, agents: List[AgentDefinition]) -> str:
    """Genera el Contrato Compartido que todos los agentes reciben como contexto previo."""
    zone_lines = []
    for a in agents:
        desc = a.description.strip().replace("\n", " ")
        perms = []
        if isinstance(a.permissions, dict):
            if a.permissions.get("write_dirs"):
                perms.append(f"Escritura: {a.permissions['write_dirs']}")
            if a.permissions.get("forbidden_dirs"):
                perms.append(f"PROHIBIDO: {a.permissions['forbidden_dirs']}")
        perm_str = f" [{'; '.join(perms)}]" if perms else ""
        zone_lines.append(f"- **{a.name}** ({a.mode}): {desc[:150]}{perm_str}")

    zones = "\n".join(zone_lines)
    return (
        f"# 📋 CONTRATO COMPARTIDO DE ORQUESTACIÓN\n\n"
        f"**Objetivo Global:** {goal}\n\n"
        f"## Zonas de Responsabilidad y Permisos (DISJUNTAS — no solapar)\n\n{zones}\n\n"
        f"## Reglas de Colaboración Estricta\n"
        f"1. NO modifiques archivos fuera de tu zona asignada ni toques rutas PROHIBIDAS.\n"
        f"2. Describe interfaces hacia otras zonas como comentarios o contratos de tipos.\n"
        f"3. Finaliza siempre con un resumen explícito de los cambios realizados.\n"
    )


def _run_agent(agent: AgentDefinition, task: str, contract: str, result: AgentResult) -> None:
    """Ejecuta un agente en su hilo. Escribe resultados en el objeto AgentResult.

    Usa result._lock (lock propio del AgentResult).
    NOTE: forbidden_dirs es advisory — enforcement planificado para V30.4.
    """
    from tools.gravity_delegate import delegate_task
    with result._lock:
        result.status = "running"
        result.started_at = datetime.now(timezone.utc).isoformat()
    full_system = f"{contract}\n\n---\n\n{agent.system_prompt}"
    try:
        res = delegate_task(
            prompt=task,
            system=full_system,
            provider=agent.provider if agent.provider != "auto" else "auto",
            model=agent.model if agent.model != "auto" else "auto",
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )
        with result._lock:
            if res.get("success"):
                result.status = "done"
                result.output = res.get("text", "")
                result.model_used = res.get("model", "")
                result.provider_used = res.get("provider", "")
            else:
                result.status = "failed"
                result.error = res.get("error", "Unknown")
    except Exception as e:
        with result._lock:
            result.status = "failed"
            result.error = str(e)
        log.error(f"[ParallelOrchestrator] Agente '{agent.name}' excepción: {e}")
    finally:
        with result._lock:
            result.finished_at = datetime.now(timezone.utc).isoformat()


def dispatch(
    goal: str,
    agent_names: Optional[List[str]] = None,
    task_per_agent: Optional[Dict[str, str]] = None,
    max_workers: int = 6,
    on_complete: Optional[Callable[["OrchestrationHandle"], None]] = None,
) -> OrchestrationHandle:
    """
    Despacha subagentes en paralelo de forma NO BLOQUEANTE.
    Retorna el handle inmediatamente. Los resultados se completan en background.
    Soporta extracción automática de menciones @agente en el objetivo (OpenCode 2.3).

    Args:
        goal: Objetivo global (usado para el Contrato Compartido y como prompt default).
        agent_names: Nombres de agentes definidos en .agents/agents/*.md
        task_per_agent: Dict opcional {nombre: prompt_específico}. Si None, todos usan `goal`.
        max_workers: Max hilos paralelos.
        on_complete: Callback llamado al terminar todos los agentes.
    """
    _prune_stale()

    all_agents = discover_agents()

    # Extracción automática de @mention estilo OpenCode 2.3
    if not agent_names and goal:
        import re
        extracted = [m for m in re.findall(r"@([a-zA-Z0-9_\-]+)", goal) if m in all_agents]
        if extracted:
            agent_names = extracted

    agent_names = agent_names or []
    selected = [all_agents[n] for n in agent_names if n in all_agents]

    if task_per_agent:
        selected_names = {a.name for a in selected}
        for k in task_per_agent:
            if k not in selected_names:
                log.warning(
                    f"[ParallelOrchestrator] task_per_agent contiene agente desconocido: '{k}' "
                    f"(no encontrado en .agents/agents/). La tarea será ignorada."
                )

    if not selected:
        raise ValueError(f"Ninguno de los agentes existe: {agent_names}")

    orch_id = str(uuid.uuid4())[:8]
    contract = _build_shared_contract(goal, selected)
    handle = OrchestrationHandle(
        orchestration_id=orch_id,
        goal=goal,
        shared_contract=contract,
        agent_results={a.name: AgentResult(agent_name=a.name) for a in selected},
    )
    with _ORCH_LOCK:
        _active[orch_id] = handle

    def _coordinator():
        log.info(f"[ParallelOrchestrator] {orch_id} — iniciando {[a.name for a in selected]}")
        with ThreadPoolExecutor(max_workers=min(max_workers, len(selected))) as pool:
            futures = {
                pool.submit(
                    _run_agent,
                    agent,
                    (task_per_agent or {}).get(agent.name, goal),
                    contract,
                    handle.agent_results[agent.name],
                ): agent.name
                for agent in selected
            }
            for fut in as_completed(futures, timeout=600):
                agent_name = futures[fut]
                try:
                    fut.result()
                    log.info(f"[ParallelOrchestrator] '{agent_name}' completado.")
                except Exception as e:
                    log.error(f"[ParallelOrchestrator] '{agent_name}' excepción en future: {e}")

        with handle._lock:
            all_failed = all(r.status == "failed" for r in handle.agent_results.values())
            handle.status = "failed" if all_failed else "done"
            handle.finished_at = datetime.now(timezone.utc).isoformat()
        log.info(f"[ParallelOrchestrator] {orch_id} finalizado. Status: {handle.status}")
        if on_complete:
            try:
                on_complete(handle)
            except Exception as e:
                log.warning(f"[ParallelOrchestrator] Callback on_complete falló: {e}")

    threading.Thread(target=_coordinator, name=f"orch-{orch_id}", daemon=True).start()
    log.info(f"[ParallelOrchestrator] Hilo coordinador lanzado. ID: {orch_id}")
    return handle


def get_orchestration(orch_id: str) -> Optional[OrchestrationHandle]:
    with _ORCH_LOCK:
        return _active.get(orch_id)


def list_orchestrations() -> List[Dict[str, Any]]:
    with _ORCH_LOCK:
        return [h.to_dict() for h in _active.values()]
