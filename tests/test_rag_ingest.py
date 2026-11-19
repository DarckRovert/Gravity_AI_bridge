"""
Tests unitarios para la ingesta de documentos RAG en /v1/rag/ingest en Python 3.13+.
"""

import io
import json
import os
import time
from unittest.mock import patch

from api.routes.mixin_post_agent import PostAgentMixin


class DummyPostHandler(PostAgentMixin):
    def __init__(self, path: str, body: bytes, content_type: str = "application/json"):
        self.path = path
        self.headers = {
            "Content-Length": str(len(body)),
            "Content-Type": content_type,
        }
        self.rfile = io.BytesIO(body)
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


def test_rag_ingest_missing_body_or_wrong_content_type():
    handler = DummyPostHandler("/v1/rag/ingest", b"", "application/json")
    res = handler._handle_post_agent()
    assert res is True
    assert handler.status_code == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["ok"] is False
    assert "multipart/form-data" in data["error"]


def test_rag_ingest_multipart_file_upload_success():
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    multipart_body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="test_doc.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
        "Contenido de prueba para indexación semántica en Python 3.13 sin CGI.\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    content_type = f"multipart/form-data; boundary={boundary}"
    handler = DummyPostHandler("/v1/rag/ingest", multipart_body, content_type)

    with patch("rag.retriever.RAGIndexer.index_file", return_value=1) as mock_index:
        res = handler._handle_post_agent()
        assert res is True
        assert handler.status_code == 200
        assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert data["indexed"] == 1

        # Permitir que el hilo daemon ejecute RAGIndexer.index_file
        time.sleep(0.1)
        mock_index.assert_called()

    # Limpieza de archivo de prueba en _rag_sources si se guardó
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file_path = os.path.join(BASE_DIR, "_rag_sources", "test_doc.txt")
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
