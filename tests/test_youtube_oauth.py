"""
tests/test_youtube_oauth.py — Pruebas unitarias para la autenticación y estado de YouTube:
- Resolución de credenciales en _load_oauth (AppData vs _integrations)
- GET /v1/youtube/status reconociendo archivos locales
- POST /v1/youtube/auth/exchange validando códigos vacíos y delegación a uploader
"""
import io
import json
import os
from unittest.mock import patch
from api.routes.mixin_get import GetRoutesMixin
from api.routes.mixin_post_media import PostMediaMixin
from core import youtube_uploader


class DummyGetHandler(GetRoutesMixin):
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

    def _send_cors(self):
        pass


class DummyPostHandler(PostMediaMixin):
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

    def _send_cors(self):
        pass


def test_youtube_uploader_load_oauth_fallback():
    # Probar que _get_oauth_filepath detecta _integrations si AppData no existe
    with patch("os.path.isfile") as mock_isfile:
        mock_isfile.side_effect = lambda path: "_integrations" in path
        path = youtube_uploader._get_oauth_filepath()
        assert "_integrations" in path


def test_youtube_status_endpoint():
    handler = DummyGetHandler("/v1/youtube/status")
    handler._serve_youtube_status()
    assert handler.response_status == 200
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "oauth_configured" in data
    assert "ready" in data
    # Comprobar que si _integrations/youtube_oauth.json existe en disco, se reporta
    integrations_path = os.path.join(youtube_uploader.BASE_DIR, "_integrations", "youtube_oauth.json")
    if os.path.isfile(integrations_path):
        assert data["oauth_file_exists"] is True


def test_youtube_auth_exchange_empty_code():
    handler = DummyPostHandler("/v1/youtube/auth/exchange", {})
    res = handler._handle_post_media()
    assert res is True
    assert handler.response_status == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in data


def test_youtube_auth_exchange_success():
    with patch("core.youtube_uploader.exchange_auth_code", return_value={"ok": True, "message": "Autenticado"}):
        handler = DummyPostHandler("/v1/youtube/auth/exchange", {"code": "mock_code_12345"})
        res = handler._handle_post_media()
        assert res is True
        assert handler.response_status == 200
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
