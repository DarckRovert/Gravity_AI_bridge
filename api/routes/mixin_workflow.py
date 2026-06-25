"""
Gravity Workflow Engine — Rutas API
Mixin de rutas GET y POST para exponer el motor de workflows en el bridge server.

Endpoints:
  GET  /v1/workflow/list              → lista workflows disponibles
  GET  /v1/workflow/nodes             → lista nodos registrados
  GET  /v1/workflow/jobs              → lista jobs activos/recientes
  GET  /v1/workflow/status/{job_id}   → estado de un job
  POST /v1/workflow/run               → lanza un workflow
"""

import json


class WorkflowMixin:
    """
    Mixin de rutas del Gravity Workflow Engine.
    Se integra en bridge_server.py igual que los demás mixins.
    """

    # ── GET handlers ──────────────────────────────────────────────────────────

    def _serve_workflow_list(self):
        """GET /v1/workflow/list — lista workflows .json disponibles."""
        try:
            from core.workflow_engine import list_workflows
            workflows = list_workflows()
            body = json.dumps({"ok": True, "workflows": workflows}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self._json_error(500, str(exc))

    def _serve_workflow_nodes(self):
        """GET /v1/workflow/nodes — catálogo de nodos registrados."""
        try:
            from core.workflow_engine import list_nodes
            nodes = list_nodes()
            body = json.dumps({"ok": True, "nodes": nodes, "count": len(nodes)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self._json_error(500, str(exc))

    def _serve_workflow_jobs(self):
        """GET /v1/workflow/jobs — lista de jobs activos y recientes."""
        try:
            from core.workflow_engine import list_jobs
            jobs = list_jobs()
            body = json.dumps({"ok": True, "jobs": jobs, "count": len(jobs)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self._json_error(500, str(exc))

    def _serve_workflow_status(self):
        """GET /v1/workflow/status/<job_id> — estado de un job."""
        try:
            from core.workflow_engine import get_job
            # Extraer job_id del path: /v1/workflow/status/abc123
            parts = self.path.split("/")
            job_id = parts[-1] if len(parts) >= 5 else ""

            job = get_job(job_id) if job_id else None
            if not job:
                self._json_error(404, f"Job '{job_id}' no encontrado.")
                return

            body = json.dumps({"ok": True, "job": job.to_dict()}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self._json_error(500, str(exc))

    # ── POST handlers ─────────────────────────────────────────────────────────

    def _handle_post_workflow(self) -> bool:
        """
        Dispatcher para rutas POST del workflow engine.
        Retorna True si la ruta fue manejada.
        """
        if self.path == "/v1/workflow/run":
            self._post_workflow_run()
            return True
        return False

    def _post_workflow_run(self):
        """POST /v1/workflow/run — lanza un workflow.

        Body JSON:
          {
            "workflow_id": "noticia_portal",
            "params": { "topic": "...", ... },
            "blocking": false
          }
        """
        try:
            from core.workflow_engine import run_workflow

            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length)) if length else {}

            workflow_id: str = data.get("workflow_id", "").strip()
            params: dict = data.get("params") or {}
            blocking: bool = bool(data.get("blocking", False))

            if not workflow_id:
                self._json_error(400, "'workflow_id' es requerido.")
                return

            job = run_workflow(
                workflow_id=workflow_id,
                params=params,
                blocking=blocking,
            )

            response = {
                "ok": True,
                "job_id": job.job_id,
                "workflow_id": job.workflow_id,
                "status": job.status,
            }
            if blocking:
                response["result"] = job.to_dict()

            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)

        except FileNotFoundError as exc:
            self._json_error(404, str(exc))
        except Exception as exc:
            self._json_error(500, str(exc))

    # ── Helper ────────────────────────────────────────────────────────────────

    def _json_error(self, code: int, message: str):
        body = json.dumps({"ok": False, "error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)
