"""
Tests unitarios para la gestión de sesiones en /v1/sessions/delete y /v1/sessions/kill.
"""

import io
import json
import os
from unittest.mock import patch

from api.routes.mixin_post_system import PostSystemMixin


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
        self.send_header("Access-Control-Allow-Origin", "*")


def test_session_delete_missing_id():
    handler = DummyPostHandler("/v1/sessions/delete", {})
    res = handler._handle_post_system()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "session_id requerido" in data["error"]


def test_session_delete_nonexistent():
    handler = DummyPostHandler("/v1/sessions/delete", {"session_id": "non_existent_session_999"})
    res = handler._handle_post_system()
    assert res is True
    assert handler.status_code == 404
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False


def test_session_delete_success():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    saves_dir = os.path.join(BASE_DIR, "_saves")
    os.makedirs(saves_dir, exist_ok=True)

    test_file = os.path.join(saves_dir, "test_session_xyz.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"name": "test_session_xyz", "history": []}, f)

    assert os.path.isfile(test_file)

    with patch("core.session_runner.terminate_session", return_value=True) as mock_term:
        handler = DummyPostHandler("/v1/sessions/delete", {"session_id": "test_session_xyz"})
        res = handler._handle_post_system()
        assert res is True
        assert handler.status_code == 200
        assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert "eliminada permanentemente" in data["message"]
        mock_term.assert_called_once_with("test_session_xyz")

    assert not os.path.exists(test_file)


def test_session_kill_running_and_not_running():
    with patch("core.session_runner.terminate_session", return_value=True):
        handler = DummyPostHandler("/v1/sessions/kill", {"session_id": "active_worker"})
        res = handler._handle_post_system()
        assert res is True
        assert handler.status_code == 200

    with patch("core.session_runner.terminate_session", return_value=False):
        handler = DummyPostHandler("/v1/sessions/kill", {"session_id": "dead_worker"})
        res = handler._handle_post_system()
        assert res is True
        assert handler.status_code == 404
