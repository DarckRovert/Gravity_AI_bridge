"""
Tests unitarios para deploy_manager y endpoint /v1/fabricaweb/status.
"""

import io
import json
from unittest.mock import patch

from core import deploy_manager
from api.routes.mixin_get import GetRoutesMixin
from api.routes.mixin_tiktok import TikTokMixin


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
        self.send_header("Access-Control-Allow-Origin", "*")

    def _check_rate(self) -> bool:
        return True


def test_deploy_manager_check_tools():
    tools = deploy_manager.check_tools()
    assert isinstance(tools, dict)
    assert "npm" in tools
    assert "netlify" in tools
    assert "node" in tools
    assert isinstance(tools["npm"], bool)
    assert isinstance(tools["netlify"], bool)
    assert isinstance(tools["node"], bool)


def test_deploy_manager_start_deploy_invalid_path():
    res = deploy_manager.start_deploy("C:/NonExistentPath/123456_xyz")
    assert res["started"] is False
    assert "Ruta de proyecto inválida" in res["reason"]


def test_serve_fabricaweb_status_endpoint():
    mock_status = {
        "status": "idle",
        "last_run": None,
        "project": None,
        "log": ["[BUILD] Test build step 1", "[BUILD] Test build step 2"],
        "netlify_url": "https://test-deploy.netlify.app",
        "error": None,
        "tools": {"npm": True, "netlify": False, "node": True},
        "running": False,
    }
    with patch("core.deploy_manager.get_status", return_value=mock_status):
        handler = DummyGetHandler("/v1/fabricaweb/status")
        handler.do_GET()
        assert handler.status_code == 200
        assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["status"] == "idle"
        assert "fabricaweb_path" in data
        assert "fabricaweb_exists" in data
        assert "Test build step 1\n[BUILD] Test build step 2" in data["last_log"]
        assert data["netlify_url"] == "https://test-deploy.netlify.app"
