"""
tests/test_software_factory.py — Pruebas unitarias para Dev Studio / Fábrica de Software:
- core.config_manager.load_config()
- POST /v1/factory/generate con extracción estructurada (**Archivo:**)
- POST /v1/factory/generate con extracción heurística de fallback
- Validación de prompt vacío (400)
"""
import io
import json
import os
import zipfile
from unittest.mock import MagicMock, patch
from api.routes.base_mixin import BaseApiMixin
from api.routes.mixin_post_agent import PostAgentMixin
from core import config_manager


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


def test_config_manager_load_config():
    cfg = config_manager.load_config()
    assert isinstance(cfg, dict)
    assert "model" in cfg


def test_factory_generate_empty_prompt():
    handler = DummyPostHandler("/v1/factory/generate", {"prompt": ""})
    res = handler._handle_post_agent()
    assert res is True
    assert handler.response_status == 400
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in data


def test_factory_generate_structured():
    mock_ai_output = (
        "Aquí tienes el código solicitado:\n\n"
        "**Archivo:** main.py\n"
        "```python\n"
        "def main():\n"
        "    print('Gravity Factory')\n"
        "```\n\n"
        "**Archivo:** README.md\n"
        "```markdown\n"
        "# Gravity Project\n"
        "Instrucciones de uso.\n"
        "```\n"
    )

    mock_plugin = MagicMock()
    mock_plugin.check_health.return_value = MagicMock(is_healthy=True, models=[{"name": "test-model"}], active_model="test-model")
    mock_plugin.chat_stream.return_value = iter([mock_ai_output])

    with patch("core.provider_manager.get_plugin", return_value=mock_plugin):
        handler = DummyPostHandler("/v1/factory/generate", {"prompt": "Crea un script"})
        res = handler._handle_post_agent()
        assert res is True
        assert handler.response_status == 200
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert data["ok"] is True
        assert data["files_created"] == 2
        assert "filename" in data

        # Verificar que el zip realmente se construyó en _entregables
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zip_path = os.path.join(base_dir, "_entregables", data["filename"])
        assert os.path.isfile(zip_path)
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            assert "main.py" in names
            assert "README.md" in names
            assert "RAW_RESPONSE.md" in names


def test_factory_generate_heuristic_fallback():
    # El modelo no usó **Archivo:** sino bloques estándar
    mock_ai_output = (
        "```python\n"
        "print('Heuristic Python')\n"
        "```\n"
    )

    with patch("core.provider_manager.get_plugin", return_value=None):
        with patch("core.provider_manager.complete", return_value=mock_ai_output):
            handler = DummyPostHandler("/v1/factory/generate", {"prompt": "Script sin formato de archivo"})
            res = handler._handle_post_agent()
            assert res is True
            assert handler.response_status == 200
            data = json.loads(handler.wfile.getvalue().decode("utf-8"))
            assert data["ok"] is True
            assert data["files_created"] == 1
            assert "filename" in data
