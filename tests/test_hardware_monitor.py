"""
Tests unitarios para telemetría de procesos y terminación segura en /v1/processes y /v1/security/kill.
"""

import io
import os
import json
from unittest.mock import patch, MagicMock

from api.routes.mixin_get import GetRoutesMixin
from api.routes.mixin_tiktok import TikTokMixin
from api.routes.mixin_post_system import PostSystemMixin


class DummyGetHandler(GetRoutesMixin, TikTokMixin):
    def __init__(self, path: str):
        self.path = path
        self.wfile = io.BytesIO()
        self.status_code = None
        self.response_headers = {}

    def send_response(self, code: int):
        self.status_code = code

    def send_header(self, key: str, value: str):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def _send_cors(self):
        pass

    def _check_rate(self) -> bool:
        return True


class DummyPostHandler(PostSystemMixin):
    def __init__(self, path: str, body: dict):
        self.path = path
        body_bytes = json.dumps(body).encode("utf-8")
        self.headers = {"Content-Length": str(len(body_bytes))}
        self.rfile = io.BytesIO(body_bytes)
        self.wfile = io.BytesIO()
        self.status_code = None
        self.response_headers = {}

    def send_response(self, code: int):
        self.status_code = code

    def send_header(self, key: str, value: str):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def _send_cors(self):
        pass


def test_serve_processes_flags_is_self():
    handler = DummyGetHandler("/v1/processes")
    handler.do_GET()
    assert handler.status_code == 200
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "processes" in data
    assert isinstance(data["processes"], list)

    current_pid = os.getpid()
    # Si el proceso actual está listado, debe tener is_self=True; los demás False
    for p in data["processes"]:
        if p["pid"] == current_pid:
            assert p["is_self"] is True
        else:
            assert p.get("is_self") is False


def test_kill_process_missing_pid():
    handler = DummyPostHandler("/v1/security/kill", {})
    res = handler._handle_post_system()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "error" in data


def test_kill_process_blocks_self_termination():
    current_pid = os.getpid()
    handler = DummyPostHandler("/v1/security/kill", {"pid": current_pid})
    res = handler._handle_post_system()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "Acción denegada" in data["error"]


def test_kill_process_nonexistent_pid():
    fake_pid = 99999999
    handler = DummyPostHandler("/v1/security/kill", {"pid": fake_pid})
    res = handler._handle_post_system()
    assert res is True
    assert handler.status_code == 404
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "ya no existe" in data["error"]


def test_kill_process_success():
    mock_proc = MagicMock()
    mock_proc.name.return_value = "rogue_task.exe"
    mock_proc.terminate.return_value = None
    mock_proc.wait.return_value = None

    with patch("psutil.Process", return_value=mock_proc):
        handler = DummyPostHandler("/v1/security/kill", {"pid": 12345})
        res = handler._handle_post_system()
        assert res is True
        assert handler.status_code == 200
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert "rogue_task.exe" in data["message"]
        mock_proc.terminate.assert_called_once()
