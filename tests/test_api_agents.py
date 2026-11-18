"""
tests/test_api_agents.py — Pruebas unitarias para los endpoints REST de agentes:
- GET /v1/agents/list
- GET /v1/agents/status/<orch_id>
- POST /v1/agents/dispatch
"""
import io
import json
import pytest
from unittest.mock import MagicMock, patch
from api.routes.base_mixin import BaseApiMixin
from api.routes.mixin_get_agents import GetAgentsMixin
from api.routes.mixin_post_agent import PostAgentMixin
from core.parallel_orchestrator import OrchestrationHandle, AgentResult, _active, _ORCH_LOCK


class DummyGetHandler(BaseApiMixin, GetAgentsMixin):
    def __init__(self, path):
        self.path = path
        self.wfile = io.BytesIO()
        self.response_status = None
        self.headers_sent = {}

    def send_response(self, status):
        self.response_status = status

    def send_header(self, k, v):
        self.headers_sent[k] = v

    def end_headers(self):
        pass


class DummyPostHandler(BaseApiMixin, PostAgentMixin):
    def __init__(self, path, payload):
        self.path = path
        body_bytes = json.dumps(payload).encode("utf-8")
        self.rfile = io.BytesIO(body_bytes)
        self.headers = {"Content-Length": str(len(body_bytes))}
        self.wfile = io.BytesIO()
        self.response_status = None
        self.headers_sent = {}

    def send_response(self, status):
        self.response_status = status

    def send_header(self, k, v):
        self.headers_sent[k] = v

    def end_headers(self):
        pass


def test_api_get_agents_list():
    handler = DummyGetHandler("/v1/agents/list")
    handler._serve_agents_list()
    assert handler.response_status == 200
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is True
    agent_names = [a["name"] for a in data["agents"]]
    assert "backend_specialist" in agent_names
    assert "frontend_specialist" in agent_names
    assert "qa_tester" in agent_names


def test_api_get_agents_status_not_found():
    handler = DummyGetHandler("/v1/agents/status/inexistente999")
    handler._serve_agents_status()
    assert handler.response_status == 404
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False


def test_api_get_agents_status_success():
    h = OrchestrationHandle(
        orchestration_id="test_status_123",
        goal="Test Goal",
        status="done",
        agent_results={"ag1": AgentResult(agent_name="ag1", status="done")},
    )
    with _ORCH_LOCK:
        _active["test_status_123"] = h

    try:
        handler = DummyGetHandler("/v1/agents/status/test_status_123")
        handler._serve_agents_status()
        assert handler.response_status == 200
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert data["orchestration_id"] == "test_status_123"
        assert data["status"] == "done"
    finally:
        with _ORCH_LOCK:
            _active.pop("test_status_123", None)


def test_api_post_agents_dispatch_missing_goal():
    handler = DummyPostHandler("/v1/agents/dispatch", {"agents": ["backend_specialist"]})
    res = handler._handle_post_agent()
    assert res is True
    assert handler.response_status == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "goal" in data["error"]


def test_api_post_agents_dispatch_missing_agents():
    handler = DummyPostHandler("/v1/agents/dispatch", {"goal": "Hacer algo", "agents": []})
    res = handler._handle_post_agent()
    assert res is True
    assert handler.response_status == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "agents" in data["error"]


def test_api_post_agents_dispatch_success():
    mock_handle = OrchestrationHandle(
        orchestration_id="mock_orch_789",
        goal="Objetivo de prueba",
        status="running",
    )
    with patch("core.parallel_orchestrator.dispatch", return_value=mock_handle) as mock_disp:
        handler = DummyPostHandler(
            "/v1/agents/dispatch",
            {"goal": "Objetivo de prueba", "agents": ["backend_specialist", "qa_tester"]},
        )
        res = handler._handle_post_agent()
        assert res is True
        assert handler.response_status == 202
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert data["orchestration_id"] == "mock_orch_789"
        mock_disp.assert_called_once_with(
            goal="Objetivo de prueba",
            agent_names=["backend_specialist", "qa_tester"],
            task_per_agent=None,
        )
