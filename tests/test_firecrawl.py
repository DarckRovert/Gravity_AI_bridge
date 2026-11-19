"""
Tests unitarios para el scraper Firecrawl y su integración RAG en /v1/tools/scrape.
"""

import io
import json
from unittest.mock import patch

from api.routes.mixin_post_agent import PostAgentMixin


class DummyPostHandler(PostAgentMixin):
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


def test_scrape_missing_url():
    handler = DummyPostHandler("/v1/tools/scrape", {})
    res = handler._handle_post_agent()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in data


def test_scrape_with_rag_ingest():
    mock_scrape = {
        "ok": True,
        "url": "https://example.com/article",
        "title": "Test Title",
        "content": "Este es el contenido completo del artículo extraído.",
        "source": "native_html_fallback",
    }
    with patch("core.firecrawl_scraper.scrape_url", return_value=mock_scrape):
        with patch("rag.retriever.RAGIndexer.index_text", return_value=3) as mock_rag:
            handler = DummyPostHandler(
                "/v1/tools/scrape",
                {"url": "https://example.com/article", "ingest_memory": True},
            )
            res = handler._handle_post_agent()
            assert res is True
            assert handler.status_code == 200
            data = json.loads(handler.wfile.getvalue().decode("utf-8"))
            assert data["ok"] is True
            assert data["memory_ingested"] is True
            assert data["indexed_chunks"] == 3
            mock_rag.assert_called_once()


def test_scrape_without_rag_ingest():
    mock_scrape = {
        "ok": True,
        "url": "https://example.com/article",
        "title": "Test Title",
        "content": "Este es el contenido.",
        "source": "firecrawl",
    }
    with patch("core.firecrawl_scraper.scrape_url", return_value=mock_scrape):
        with patch("rag.retriever.RAGIndexer.index_text") as mock_rag:
            handler = DummyPostHandler(
                "/v1/tools/scrape",
                {"url": "https://example.com/article", "ingest_memory": False},
            )
            res = handler._handle_post_agent()
            assert res is True
            assert handler.status_code == 200
            data = json.loads(handler.wfile.getvalue().decode("utf-8"))
            assert data["ok"] is True
            assert data["memory_ingested"] is False
            assert data["indexed_chunks"] == 0
            mock_rag.assert_not_called()


def test_scrape_scraper_failure():
    mock_scrape = {
        "ok": False,
        "error": "Timeout conectando al servidor",
        "url": "https://invalid-host-404.com",
    }
    with patch("core.firecrawl_scraper.scrape_url", return_value=mock_scrape):
        handler = DummyPostHandler(
            "/v1/tools/scrape",
            {"url": "https://invalid-host-404.com"},
        )
        res = handler._handle_post_agent()
        assert res is True
        assert handler.status_code == 400
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is False
        assert data["memory_ingested"] is False
