"""
api/routes/mixin_get_agents.py — GRAVITY AI V30.3
Mixin GET para los endpoints de gestión de agentes paralelos.
Se hereda en GetRoutesMixin (mixin_get.py).
"""
from http import HTTPStatus
from core.parallel_orchestrator import get_orchestration
from core.subagent_loader import discover_agents


class GetAgentsMixin:
    """Handlers GET para /v1/agents/list y /v1/agents/status/<orch_id>."""

    def _serve_agents_list(self):
        """GET /v1/agents/list — retorna todos los agentes disponibles en .agents/agents/"""
        agents = discover_agents()
        payload = {
            "ok": True,
            "agents": [
                {
                    "name": a.name,
                    "description": a.description,
                    "mode": a.mode,
                    "model": a.model,
                    "provider": a.provider,
                }
                for a in agents.values()
            ],
        }
        self._send_json(payload, HTTPStatus.OK)

    def _serve_agents_status(self):
        """GET /v1/agents/status/<orch_id> — retorna estado de una orquestación."""
        orch_id = self.path.split("/v1/agents/status/", 1)[-1].split("?")[0].strip("/")
        handle = get_orchestration(orch_id)
        if handle is None:
            self._send_json({"ok": False, "error": f"Orquestación '{orch_id}' no encontrada"}, HTTPStatus.NOT_FOUND)
        else:
            self._send_json({"ok": True, **handle.to_dict()}, HTTPStatus.OK)
