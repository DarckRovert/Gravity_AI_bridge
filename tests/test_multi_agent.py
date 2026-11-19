"""
tests/test_multi_agent.py — Pruebas unitarias para core.multi_agent y los modos:
- compare (paralelo)
- vote (consenso TF-IDF / Jaccard y synthesize)
- debate (ronda 1 + réplica cruzada + síntesis de árbitro)
- /v1/agent/compare API router
"""
import io
import json
from unittest.mock import MagicMock, patch
from api.routes.base_mixin import BaseApiMixin
from api.routes.mixin_post_agent import PostAgentMixin
from core import multi_agent


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


def test_multi_agent_compare():
    mock_plugin1 = MagicMock()
    mock_plugin1.check_health.return_value = MagicMock(is_healthy=True, models=[{"name": "m1"}], active_model="m1")
    mock_plugin1.chat_stream.return_value = iter(["Respuesta ", "Modelo 1"])

    mock_plugin2 = MagicMock()
    mock_plugin2.check_health.return_value = MagicMock(is_healthy=True, models=[{"name": "m2"}], active_model="m2")
    mock_plugin2.chat_stream.return_value = iter(["Respuesta ", "Modelo 2"])

    def get_plugin_mock(name):
        return mock_plugin1 if name == "p1" else mock_plugin2

    with patch("core.multi_agent.get_plugin", side_effect=get_plugin_mock):
        results = multi_agent.compare(
            [{"role": "user", "content": "Hola"}],
            providers=["p1", "p2"],
            n_models=2
        )
        assert len(results) == 2
        providers = [r["provider"] for r in results]
        assert "p1" in providers
        assert "p2" in providers


def test_multi_agent_vote_synthesize():
    mock_results = [
        {"provider": "p1", "model": "m1", "response": "Python es genial"},
        {"provider": "p2", "model": "m2", "response": "Python es muy potente"},
    ]
    with patch("core.multi_agent.compare", return_value=mock_results):
        with patch("core.provider_manager.complete", return_value="Síntesis unificada: Python es excelente"):
            res = multi_agent.vote([{"role": "user", "content": "¿Qué tal Python?"}], mode="synthesize")
            assert res["provider"] == "synthesized"
            assert res["response"] == "Síntesis unificada: Python es excelente"


def test_multi_agent_vote_tfidf():
    mock_results = [
        {"provider": "p1", "model": "m1", "response": "Solución arquitectónica A para el sistema distribuido con microservicios"},
        {"provider": "p2", "model": "m2", "response": "Solución arquitectónica B para el sistema distribuido con microservicios"},
        {"provider": "p3", "model": "m3", "response": "Texto totalmente desconectado y sin relevancia"},
    ]
    with patch("core.multi_agent.compare", return_value=mock_results):
        res = multi_agent.vote([{"role": "user", "content": "arquitectura"}], mode="vote")
        assert res["provider"] in ("p1", "p2")
        assert "vote_score" in res


def test_multi_agent_debate():
    mock_round1 = [
        {"provider": "p1", "model": "m1", "response": "Propuesta A basada en PostgreSQL"},
        {"provider": "p2", "model": "m2", "response": "Propuesta B basada en MongoDB"},
    ]
    mock_p1 = MagicMock()
    mock_p1.chat_stream.return_value = iter(["Réplica de A: PostgreSQL garantiza ACID."])
    mock_p2 = MagicMock()
    mock_p2.chat_stream.return_value = iter(["Réplica de B: MongoDB ofrece mayor flexibilidad de esquema."])

    def get_plugin_mock(name):
        return mock_p1 if name == "p1" else mock_p2

    with patch("core.multi_agent.compare", return_value=mock_round1):
        with patch("core.multi_agent.get_plugin", side_effect=get_plugin_mock):
            with patch("core.provider_manager.complete", return_value="Veredicto: PostgreSQL para transacciones, MongoDB para documentos."):
                results = multi_agent.debate(
                    [{"role": "user", "content": "Elegir base de datos"}],
                    providers=["p1", "p2"],
                    n_models=2
                )
                assert len(results) == 3
                assert results[0]["provider"] == "ARBITER (Veredicto)"
                assert results[0]["phase"] == "verdict"
                phases = [r.get("phase") for r in results]
                assert "rebuttal" in phases


def test_api_agent_compare_modes():
    # Test mode: debate
    with patch("core.multi_agent.debate", return_value=[{"provider": "ARBITER", "response": "Ok"}]) as mock_deb:
        h = DummyPostHandler("/v1/agent/compare", {"prompt": "test", "mode": "debate"})
        res = h._handle_post_agent()
        assert res is True
        assert h.response_status == 200
        data = json.loads(h.wfile.getvalue().decode("utf-8"))
        assert data["mode"] == "debate"
        mock_deb.assert_called_once()

    # Test mode: consensus (synthesize)
    with patch("core.multi_agent.vote", return_value={"provider": "synthesized", "response": "Consenso"}) as mock_vote:
        h = DummyPostHandler("/v1/agent/compare", {"prompt": "test", "mode": "consensus"})
        res = h._handle_post_agent()
        assert res is True
        assert h.response_status == 200
        data = json.loads(h.wfile.getvalue().decode("utf-8"))
        assert data["mode"] == "consensus"
        mock_vote.assert_called_once_with([{"role": "user", "content": "test"}], n_models=3, mode="synthesize")
