"""
Tests unitarios para YouTubeAnalyzer y endpoint /v1/youtube/analyzer/process.
"""

import io
import json
from unittest.mock import patch, MagicMock

from api.routes.mixin_post_media import PostMediaMixin
from tools.youtube_analyzer import YouTubeAnalyzer


class DummyPostHandler(PostMediaMixin):
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


def test_youtube_analyzer_missing_url():
    handler = DummyPostHandler("/v1/youtube/analyzer/process", {})
    res = handler._handle_post_media()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in data


def test_youtube_analyzer_error_preserves_cors():
    with patch("tools.youtube_analyzer.YouTubeAnalyzer.process_url", side_effect=ValueError("Invalid Video")):
        handler = DummyPostHandler("/v1/youtube/analyzer/process", {"url": "https://youtube.com/watch?v=bad"})
        res = handler._handle_post_media()
        assert res is True
        assert handler.status_code == 500
        assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"
        assert handler.response_headers.get("Content-Type") == "application/json"
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert "Invalid Video" in data["error"]


def test_clean_vtt():
    analyzer = YouTubeAnalyzer()
    sample_vtt = (
        "WEBVTT\n"
        "Kind: captions\n"
        "Language: es\n\n"
        "00:00:01.000 --> 00:00:04.000\n"
        "<c>Hola</c> a todos los <b>espectadores</b>.\n\n"
        "00:00:04.500 --> 00:00:07.000\n"
        "Bienvenidos a Gravity AI.\n"
    )
    cleaned = analyzer._clean_vtt(sample_vtt)
    assert "Hola a todos los espectadores." in cleaned
    assert "Bienvenidos a Gravity AI." in cleaned
    assert "-->" not in cleaned
    assert "WEBVTT" not in cleaned


def test_fetch_video_info_extracts_subtitles_from_metadata():
    analyzer = YouTubeAnalyzer()
    mock_info = {
        "id": "abc12345",
        "title": "Gravity AI Demo",
        "uploader": "Gravity Channel",
        "view_count": 1000,
        "like_count": 50,
        "comment_count": 10,
        "duration": 120,
        "thumbnail": "https://img.youtube.com/vi/abc12345/0.jpg",
        "subtitles": {
            "es": [
                {"ext": "vtt", "url": "https://mock.subtitles/es.vtt"}
            ]
        },
        "automatic_captions": {}
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nTexto del subtítulo en español."

    mock_ydl_instance = MagicMock()
    mock_ydl_instance.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.extract_info.return_value = mock_info

    with patch("tools.youtube_analyzer.yt_dlp.YoutubeDL", return_value=mock_ydl_instance):
        with patch("requests.get", return_value=mock_resp):
            info = analyzer.fetch_video_info("https://youtube.com/watch?v=abc12345")
            assert info["title"] == "Gravity AI Demo"
            assert "Texto del subtítulo en español." in info["transcript"]
            assert info["engagement_rate"] == 6.0


def test_fallback_whisper_safely_handles_missing_module():
    analyzer = YouTubeAnalyzer()
    with patch.dict("sys.modules", {"faster_whisper": None}):
        res = analyzer._fallback_whisper("https://youtube.com/watch?v=test", "vid123")
        assert "no está instalado" in res
