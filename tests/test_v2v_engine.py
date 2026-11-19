"""
tests/test_v2v_engine.py — Pruebas unitarias para el subsistema V2V Engine:
- GET /v1/v2v/status enrutando a puerto 7863
- Inicialización y contrato de métodos de V2VPipeline (start, stop, add_client, update_config)
- Prevención de colisión de puerto con Fooocus (7861 vs 7863)
"""
import io
import json
import sys
import os
from api.routes.mixin_get import GetRoutesMixin


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


def test_v2v_status_endpoint_returns_port_7863():
    handler = DummyGetHandler("/v1/v2v/status")
    handler._serve_v2v_status()
    assert handler.response_status == 200
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert data["port"] == 7863
    assert "online" in data
    assert "process_running" in data


def test_v2v_pipeline_class_contract():
    # Importar el pipeline desde _integrations/v2v_engine
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    v2v_dir = os.path.join(base_dir, "_integrations", "v2v_engine")
    if v2v_dir not in sys.path:
        sys.path.insert(0, v2v_dir)

    from v2v_pipeline import V2VPipeline

    pipeline = V2VPipeline()
    assert hasattr(pipeline, "start")
    assert hasattr(pipeline, "stop")
    assert hasattr(pipeline, "add_client")
    assert hasattr(pipeline, "remove_client")
    assert hasattr(pipeline, "update_config")
    assert hasattr(pipeline, "current_fps")
    assert hasattr(pipeline, "running")

    # Probar add y remove client
    mock_ws = object()
    pipeline.add_client(mock_ws)
    assert mock_ws in pipeline.clients
    pipeline.remove_client(mock_ws)
    assert mock_ws not in pipeline.clients

    # Probar update config
    pipeline.update_config({"preset": "samurai", "strength": 0.9})
    assert pipeline.config["preset"] == "samurai"
    assert pipeline.config["strength"] == 0.9
