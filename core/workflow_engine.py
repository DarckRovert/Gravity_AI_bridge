"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — WORKFLOW ENGINE V1.0                                          ║
║                                                                              ║
║   Motor de ejecución de grafos de nodos (DAG) al estilo ComfyUI.            ║
║   Permite definir pipelines de producción de contenido como JSON,           ║
║   ejecutarlos secuencialmente o en paralelo, y observar su progreso.        ║
║                                                                              ║
║   Conceptos clave:                                                           ║
║     • GravityNode  — unidad atómica de trabajo (input → output)             ║
║     • WorkflowGraph — parser JSON + topological sort + executor             ║
║     • NodeRegistry — catálogo de nodos disponibles                          ║
║     • WorkflowJob  — instancia en ejecución con estado observable           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import json
import time
import uuid
import threading
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Set

from core.logger import log
from core.hook_engine import hook_manager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS_DIR = os.path.join(BASE_DIR, "workflows")

# ── Tipos de dato que fluyen entre nodos ─────────────────────────────────────
DATA_TYPES = {
    "TEXT",       # str — prompt, guión, artículo, código
    "TEXT_LIST",  # list[str] — lista de escenas, capítulos, etc.
    "AUDIO",      # str — ruta absoluta a archivo .wav/.mp3
    "IMAGE",      # str — ruta absoluta a imagen .png/.jpg
    "IMAGE_LIST", # list[str] — lista de imágenes
    "VIDEO",      # str — ruta absoluta a .mp4
    "VIDEO_LIST", # list[str] — lista de clips
    "JSON",       # dict — metadata, config, contexto
    "JSON_LIST",  # list[dict] — lista de objetos
    "BOOL",       # bool
    "INT",        # int
    "FLOAT",      # float
    "ANY",        # sin restricción de tipo
}


# ══════════════════════════════════════════════════════════════════════════════
# BASE CLASS: GravityNode
# ══════════════════════════════════════════════════════════════════════════════

class GravityNode(ABC):
    """
    Unidad atómica de trabajo en un workflow de Gravity.

    Subclasses deben implementar:
      - NODE_TYPE: str — identificador único del nodo (ej. "LLMQuery")
      - INPUT_SCHEMA: dict[str, str] — {campo: tipo_dato}
      - OUTPUT_SCHEMA: dict[str, str] — {campo: tipo_dato}
      - execute(inputs: dict) -> dict
    """

    NODE_TYPE: str = "BaseNode"
    INPUT_SCHEMA: Dict[str, str] = {}
    OUTPUT_SCHEMA: Dict[str, str] = {}
    DESCRIPTION: str = ""

    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}

    @abstractmethod
    def execute(self, inputs: dict) -> dict:
        """
        Ejecuta la operación del nodo.
        inputs: dict con los valores de INPUT_SCHEMA
        retorna: dict con los valores de OUTPUT_SCHEMA
        """
        ...

    def validate_inputs(self, inputs: dict) -> None:
        """Valida que los inputs requeridos estén presentes."""
        for field in self.INPUT_SCHEMA:
            if field not in inputs and field not in self.config:
                raise ValueError(
                    f"[{self.NODE_TYPE}/{self.node_id}] Input requerido '{field}' no encontrado."
                )

    def safe_path_resolve(self, target_path: str, is_write: bool = False) -> str:
        """AgentShield: Previene Path Traversal y protege el Core de sobreescrituras (Ring 0)."""
        base_abs = os.path.abspath(BASE_DIR)
        absolute_target = os.path.abspath(os.path.join(base_abs, target_path))
        # 1. Asegurar que termina en sep para evitar bypass de hermanos (Path Traversal)
        # Excepción para el despliegue del portal de noticias
        is_news_portal = absolute_target.startswith(os.path.abspath("F:/gravity-news-portal") + os.sep) or absolute_target == os.path.abspath("F:/gravity-news-portal")
        
        if not absolute_target.startswith(base_abs + os.sep) and absolute_target != base_abs and not is_news_portal:
            log.warning(f"[{self.NODE_TYPE}] Path traversal bloqueado: {target_path} -> {absolute_target}")
            raise ValueError("Path traversal attempt blocked by AgentShield.")
            
        # 2. AgentShield Core Protection (Evitar sobrescritura del propio puente)
        if is_write:
            protected_items = {
                "core", "api", "tools", "rag", ".agents", "frontend", "launchers", "tests",
                "bridge_server.py", "ask_deepseek.py", "INSTALAR.py", "gravity_service.py",
                "gravity_launcher.pyw", ".env", "config.yaml", "_knowledge.json", "_settings.json"
            }
            import pathlib
            rel_path = os.path.relpath(absolute_target, base_abs)
            parts = pathlib.Path(rel_path).parts
            if parts and parts[0] in protected_items:
                log.error(f"[{self.NODE_TYPE}] Core Protection bloqueó intento de escritura en zona protegida: {absolute_target}")
                raise ValueError(f"AgentShield Core Protection blocked write attempt to system critical path: {parts[0]}")
                
        return absolute_target

    def __repr__(self) -> str:
        return f"<{self.NODE_TYPE} id={self.node_id}>"


# ══════════════════════════════════════════════════════════════════════════════
# NODE REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

class _NodeRegistry:
    """Catálogo singleton de todos los nodos disponibles en Gravity."""

    def __init__(self):
        self._nodes: Dict[str, type] = {}

    def register(self, cls: type) -> type:
        """Decorator para registrar un nodo. Uso: @registry.register"""
        self._nodes[cls.NODE_TYPE] = cls
        return cls

    def get(self, node_type: str) -> Optional[type]:
        return self._nodes.get(node_type)

    def list_all(self) -> Dict[str, dict]:
        """Retorna metadatos de todos los nodos registrados."""
        return {
            nt: {
                "type": nt,
                "description": cls.DESCRIPTION,
                "inputs": cls.INPUT_SCHEMA,
                "outputs": cls.OUTPUT_SCHEMA,
            }
            for nt, cls in self._nodes.items()
        }


registry = _NodeRegistry()


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW JOB — instancia en ejecución
# ══════════════════════════════════════════════════════════════════════════════

class WorkflowJob:
    """Estado observable de un workflow en ejecución."""

    def __init__(self, job_id: str, workflow_id: str, params: dict):
        self.job_id = job_id
        self.workflow_id = workflow_id
        self.params = params
        self.status: str = "pending"         # pending | running | done | failed
        self.progress: int = 0               # 0-100
        self.current_node: Optional[str] = None
        self.current_step: str = ""
        self.outputs: Dict[str, Any] = {}    # outputs finales del workflow
        self.node_outputs: Dict[str, Any] = {}  # outputs intermedios por nodo
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self._lock = threading.Lock()

    def update(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "job_id": self.job_id,
                "workflow_id": self.workflow_id,
                "status": self.status,
                "progress": self.progress,
                "current_node": self.current_node,
                "current_step": self.current_step,
                "error": self.error,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "elapsed_s": round(self.finished_at - self.started_at, 2)
                if (self.finished_at and self.started_at)
                else None,
            }


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW GRAPH — parser + executor
# ══════════════════════════════════════════════════════════════════════════════

class WorkflowGraph:
    """
    Lee una definición JSON de workflow y la ejecuta como un DAG.

    Formato JSON mínimo:
    {
      "workflow_id": "mi_workflow",
      "description": "...",
      "nodes": [
        {
          "id": "n1",
          "type": "LLMQuery",
          "config": {"system": "..."},
          "inputs": {
            "prompt": "{{topic}}"       ← template de parámetro
          }
        },
        {
          "id": "n2",
          "type": "ImageGenerator",
          "inputs": {
            "prompt": "n1.text"         ← output del nodo n1
          }
        }
      ]
    }
    """

    def __init__(self, workflow_def: dict):
        self.workflow_id: str = workflow_def.get("workflow_id", "unnamed")
        self.description: str = workflow_def.get("description", "")
        self.node_defs: List[dict] = workflow_def.get("nodes", [])
        self._validate_structure()

    def _validate_structure(self) -> None:
        ids: Set[str] = set()
        for nd in self.node_defs:
            if "id" not in nd:
                raise ValueError(f"[WorkflowGraph] Nodo sin 'id': {nd}")
            if "type" not in nd:
                raise ValueError(f"[WorkflowGraph] Nodo sin 'type': {nd}")
            if nd["id"] in ids:
                raise ValueError(f"[WorkflowGraph] ID duplicado: {nd['id']}")
            ids.add(nd["id"])

    def _resolve_deps(self) -> List[str]:
        """
        Topological sort de los nodos.
        Un nodo B depende de A si algún input de B referencia 'A.*'
        """
        dep_graph: Dict[str, Set[str]] = defaultdict(set)
        all_ids = {nd["id"] for nd in self.node_defs}

        for nd in self.node_defs:
            nid = nd["id"]
            dep_graph[nid]  # ensure entry
            for val in (nd.get("inputs") or {}).values():
                if isinstance(val, str):
                    for src_id in all_ids:
                        if f"{src_id}." in val:
                            dep_graph[nid].add(src_id)

        # Kahn's algorithm
        in_degree = {nid: 0 for nid in all_ids}
        for nid, deps in dep_graph.items():
            for dep in deps:
                in_degree[nid] += 1 if dep != nid else 0

        # Recalculate in_degree properly
        in_degree = defaultdict(int)
        for nid in all_ids:
            for dep in dep_graph[nid]:
                in_degree[nid] += 1

        # Build reverse: who does this node unlock?
        unlocks: Dict[str, List[str]] = defaultdict(list)
        for nid, deps in dep_graph.items():
            for dep in deps:
                unlocks[dep].append(nid)

        queue = deque(nid for nid in all_ids if in_degree[nid] == 0)
        order: List[str] = []

        while queue:
            nid = queue.popleft()
            order.append(nid)
            for unlocked in unlocks[nid]:
                in_degree[unlocked] -= 1
                if in_degree[unlocked] == 0:
                    queue.append(unlocked)

        if len(order) != len(all_ids):
            raise ValueError("[WorkflowGraph] Ciclo detectado en el grafo de nodos.")

        return order

    def _resolve_value(
        self,
        val: Any,
        params: dict,
        node_outputs: Dict[str, Any],
    ) -> Any:
        """
        Resuelve el valor de un input:
          - "n1.text"     → node_outputs["n1"]["text"] (si es valor exacto)
          - "{{param}}"   → interpolación de params o node_outputs
          - cualquier otro valor → literal
        """
        if not isinstance(val, str):
            return val

        # 1. Resolver valor exacto de output de nodo (ej. "n1.text")
        parts = val.split(".", 1)
        if len(parts) == 2 and parts[0] in node_outputs:
            src_node_id, field_expr = parts
            src_out = node_outputs[src_node_id]
            if isinstance(src_out, dict):
                if "[" not in field_expr:
                    return src_out.get(field_expr)
                bracket_idx = field_expr.index("[")
                field_name = field_expr[:bracket_idx]
                idx_str = field_expr[bracket_idx + 1 : field_expr.index("]")]
                arr = src_out.get(field_name, [])
                try:
                    return arr[int(idx_str)]
                except (IndexError, ValueError):
                    pass

        # 2. Resolver interpolación inline (ej. "Hola {{topic}} o {{n1.text}}")
        import re
        
        # Si es exactamente "{{algo}}", queremos preservar el tipo (puede no ser string)
        exact_match = re.fullmatch(r"\{\{\s*(.*?)\s*\}\}", val)
        if exact_match:
            key = exact_match.group(1)
            # Primero buscar en params
            if key in params:
                return params[key]
            # Si no, buscar como output de nodo
            parts = key.split(".", 1)
            if len(parts) == 2 and parts[0] in node_outputs:
                src_node_id, field_expr = parts
                src_out = node_outputs[src_node_id]
                if isinstance(src_out, dict):
                    if "[" not in field_expr:
                        return src_out.get(field_expr)
                    bracket_idx = field_expr.index("[")
                    field_name = field_expr[:bracket_idx]
                    idx_str = field_expr[bracket_idx + 1 : field_expr.index("]")]
                    arr = src_out.get(field_name, [])
                    try:
                        return arr[int(idx_str)]
                    except (IndexError, ValueError):
                        pass
            # Si es exacto pero no se encontró, retorna el texto original o falla
            raise KeyError(f"[WorkflowGraph] Parámetro '{key}' no encontrado en params ni outputs.")

        # Si hay multiples {{}} dentro de un string, reemplazar
        def _replace_match(match):
            key = match.group(1).strip()
            if key in params:
                return str(params[key])
            parts = key.split(".", 1)
            if len(parts) == 2 and parts[0] in node_outputs:
                src_node_id, field_expr = parts
                src_out = node_outputs[src_node_id]
                if isinstance(src_out, dict):
                    if "[" not in field_expr:
                        return str(src_out.get(field_expr, ""))
                    bracket_idx = field_expr.index("[")
                    field_name = field_expr[:bracket_idx]
                    idx_str = field_expr[bracket_idx + 1 : field_expr.index("]")]
                    arr = src_out.get(field_name, [])
                    try:
                        return str(arr[int(idx_str)])
                    except (IndexError, ValueError):
                        pass
            return match.group(0) # dejar igual si no resuelve

        return re.sub(r"\{\{(.*?)\}\}", _replace_match, val)

    def _build_node_inputs(
        self,
        nd: dict,
        params: dict,
        node_outputs: Dict[str, Any],
    ) -> dict:
        """Construye el dict de inputs para un nodo resolviendo referencias."""
        resolved = {}
        for field, val in (nd.get("inputs") or {}).items():
            resolved[field] = self._resolve_value(val, params, node_outputs)
        # Merge config values (config = defaults, inputs override)
        config = nd.get("config") or {}
        merged = {**config, **resolved}
        return merged

    def execute(
        self,
        params: dict = None,
        on_progress: Optional[Callable[[int, str, str], None]] = None,
        job: Optional[WorkflowJob] = None,
    ) -> dict:
        """
        Ejecuta el workflow completo.

        params: variables de entrada (sustituyen {{placeholder}})
        on_progress(progress_pct, node_id, message): callback opcional
        job: WorkflowJob para actualizar estado observable

        Retorna dict con los outputs finales (último nodo o nodos sin consumidores).
        """
        params = params or {}
        node_outputs: Dict[str, Any] = {}

        order = self._resolve_deps()
        total = len(order)
        nd_map = {nd["id"]: nd for nd in self.node_defs}

        for step_idx, nid in enumerate(order):
            nd = nd_map[nid]
            node_type = nd["type"]
            node_cls = registry.get(node_type)

            if node_cls is None:
                raise ValueError(
                    f"[WorkflowGraph] Nodo tipo '{node_type}' no registrado. "
                    f"Tipos disponibles: {list(registry._nodes.keys())}"
                )

            progress_pct = int((step_idx / total) * 100)
            step_msg = f"Ejecutando [{node_type}] ({step_idx + 1}/{total})"

            if job:
                job.update(
                    current_node=nid,
                    current_step=step_msg,
                    progress=progress_pct,
                )
            if on_progress:
                on_progress(progress_pct, nid, step_msg)

            log.info(f"[WorkflowEngine] {self.workflow_id} -> {step_msg}")

            node_inputs = self._build_node_inputs(nd, params, node_outputs)

            # --- PRE-EXECUTION HOOKS ---
            try:
                node_inputs = hook_manager.run_pre_hooks(nid, node_type, node_inputs)
            except Exception as exc:
                err_msg = f"[{node_type}/{nid}] Pre-Hook Error: {exc}"
                log.error(f"[WorkflowEngine] {err_msg}")
                raise RuntimeError(err_msg) from exc

            # Instanciar y ejecutar el nodo
            node_instance = node_cls(node_id=nid, config=nd.get("config") or {})

            try:
                result = node_instance.execute(node_inputs)
            except Exception as exc:
                err_msg = f"[{node_type}/{nid}] Error: {exc}\n{traceback.format_exc()}"
                log.error(f"[WorkflowEngine] {err_msg}")
                raise RuntimeError(err_msg) from exc

            if not isinstance(result, dict):
                raise TypeError(
                    f"[WorkflowGraph] Nodo {node_type}/{nid} retornó {type(result).__name__}, se esperaba dict."
                )

            # --- POST-EXECUTION HOOKS ---
            try:
                result = hook_manager.run_post_hooks(nid, node_type, result)
            except Exception as exc:
                err_msg = f"[{node_type}/{nid}] Post-Hook Error: {exc}"
                log.error(f"[WorkflowEngine] {err_msg}")
                raise RuntimeError(err_msg) from exc

            node_outputs[nid] = result
            log.info(f"[WorkflowEngine] [{node_type}/{nid}] OK — outputs: {list(result.keys())}")

        # Los outputs del workflow son los del último nodo en orden topológico
        final_outputs = node_outputs.get(order[-1], {}) if order else {}
        # Incluir también todos los outputs intermedios bajo "all_outputs"
        final_outputs["_all_node_outputs"] = node_outputs

        return final_outputs


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW MANAGER — API pública de alto nivel
# ══════════════════════════════════════════════════════════════════════════════

_active_jobs: Dict[str, WorkflowJob] = {}
_jobs_lock = threading.RLock()
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gravity-wf")


def load_workflow(workflow_id: str) -> dict:
    """
    Carga la definición de un workflow desde workflows/<workflow_id>.json
    o desde un path absoluto.
    """
    path = workflow_id if os.path.isabs(workflow_id) else os.path.join(
        WORKFLOWS_DIR, f"{workflow_id}.json"
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"[WorkflowManager] Workflow no encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_workflow(
    workflow_id: str,
    params: dict = None,
    blocking: bool = False,
) -> WorkflowJob:
    """
    Lanza un workflow. Retorna un WorkflowJob inmediatamente.

    workflow_id: nombre del workflow (sin .json) o path absoluto
    params: variables de entrada para el workflow
    blocking: si True, espera a que termine antes de retornar
    """
    definition = load_workflow(workflow_id)
    graph = WorkflowGraph(definition)

    job_id = str(uuid.uuid4())[:8]
    job = WorkflowJob(
        job_id=job_id,
        workflow_id=graph.workflow_id,
        params=params or {},
    )

    with _jobs_lock:
        _active_jobs[job_id] = job

    def _run():
        job.update(status="running", started_at=time.time(), progress=0)
        try:
            outputs = graph.execute(
                params=params or {},
                job=job,
            )
            job.update(
                status="done",
                progress=100,
                finished_at=time.time(),
                outputs=outputs,
                current_step="Completado",
            )
            log.info(
                f"[WorkflowManager] Job {job_id} ({graph.workflow_id}) completado en "
                f"{round(job.finished_at - job.started_at, 2)}s"
            )
        except Exception as exc:
            job.update(
                status="failed",
                error=str(exc),
                finished_at=time.time(),
                current_step="Error",
            )
            log.error(f"[WorkflowManager] Job {job_id} ({graph.workflow_id}) falló: {exc}")

    if blocking:
        _run()
    else:
        _executor.submit(_run)

    return job


def get_job(job_id: str) -> Optional[WorkflowJob]:
    with _jobs_lock:
        return _active_jobs.get(job_id)


def list_jobs() -> List[dict]:
    with _jobs_lock:
        return [job.to_dict() for job in _active_jobs.values()]


def list_workflows() -> List[dict]:
    """Lista todos los workflows disponibles en el directorio workflows/."""
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)
    workflows = []
    for fname in os.listdir(WORKFLOWS_DIR):
        if fname.endswith(".json"):
            path = os.path.join(WORKFLOWS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    wf = json.load(f)
                workflows.append({
                    "workflow_id": wf.get("workflow_id", fname[:-5]),
                    "description": wf.get("description", ""),
                    "node_count": len(wf.get("nodes", [])),
                    "file": fname,
                })
            except Exception:
                pass
    return workflows


def list_nodes() -> Dict[str, dict]:
    """Lista todos los nodos registrados con sus schemas."""
    return registry.list_all()


# ── Auto-carga de nodos al importar ──────────────────────────────────────────
def _autoload_nodes() -> None:
    """Importa todos los módulos de core/nodes/ para que se auto-registren."""
    nodes_dir = os.path.join(os.path.dirname(__file__), "nodes")
    if not os.path.isdir(nodes_dir):
        return
    for fname in os.listdir(nodes_dir):
        if fname.endswith(".py") and not fname.startswith("_"):
            module_name = f"core.nodes.{fname[:-3]}"
            try:
                __import__(module_name)
            except Exception as exc:
                log.warning(f"[WorkflowEngine] No se pudo cargar nodo {module_name}: {exc}")


_autoload_nodes()
