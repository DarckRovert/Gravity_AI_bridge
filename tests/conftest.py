"""
tests/conftest.py — Fixtures compartidos para toda la suite de tests de Gravity AI Bridge.
Resetea singletons globales y provee rutas temporales aisladas por test.
"""

import json
import os
import sys
import pytest

# Asegurar raíz del proyecto en sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── Fixture: _settings.json temporal ─────────────────────────────────────────


@pytest.fixture
def mock_settings(tmp_path, monkeypatch):
    """
    Provee un _settings.json temporal con valores base.
    Parchea SETTINGS_FILE en engine_watchdog para aislamiento total.
    """
    settings_file = tmp_path / "_settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "bridge_port": 7860,
                "provider": "ollama",
                "model_locked": False,
                "advanced_params": {"num_ctx": 4096},
            },
            indent=2,
        )
    )

    import core.engine_watchdog as ew

    monkeypatch.setattr(ew, "SETTINGS_FILE", str(settings_file))
    return settings_file


# ── Fixture: audit log temporal ───────────────────────────────────────────────


@pytest.fixture
def mock_audit_log(tmp_path):
    """
    Instancia un AuditLogger apuntando a un archivo temporal.
    No contamina el _audit_log.jsonl real del proyecto.
    """
    from core.audit_log import AuditLogger

    return AuditLogger(log_path=str(tmp_path / "test_audit.jsonl"))


# ── Fixture: base de datos de imagen queue temporal ───────────────────────────


@pytest.fixture
def mock_image_queue_db(tmp_path, monkeypatch):
    """
    Redirige image_queue al SQLite temporal y resetea su estado global.
    """
    import core.image_queue as iq

    db_path = str(tmp_path / "test_image_queue.sqlite")
    monkeypatch.setattr(iq, "DB_PATH", db_path)
    monkeypatch.setattr(iq, "_started", False)
    monkeypatch.setattr(iq, "_current_job", None)
    iq._init_db()
    return db_path


# ── Fixture: reset security monitor ──────────────────────────────────────────


@pytest.fixture(autouse=False)
def reset_security_monitor(monkeypatch):
    """
    Limpia el estado de alertas del security monitor entre tests.
    No es autouse para no impactar tests que no lo necesitan.
    """
    from core import security_monitor as sm

    with sm._lock:
        sm._state["alerts"].clear()
        sm._baseline_hashes.clear()
        sm._known_pids.clear()
    yield
    with sm._lock:
        sm._state["alerts"].clear()


# ── Fixture: reset engine watchdog ────────────────────────────────────────────


@pytest.fixture(autouse=False)
def reset_watchdog(monkeypatch):
    """Reset completo del estado global del engine watchdog."""
    import core.engine_watchdog as ew

    monkeypatch.setattr(ew, "_current_provider_name", None)
    monkeypatch.setattr(ew, "_current_model", None)
    monkeypatch.setattr(ew, "_current_url", None)
    monkeypatch.setattr(ew, "_current_protocol", None)
    monkeypatch.setattr(ew, "_current_api_opts", {})
    monkeypatch.setattr(ew, "_hardware_profile", None)
    monkeypatch.setattr(ew, "_on_switch_callbacks", [])
    monkeypatch.setattr(ew, "_started", False)


# ── Fixture: mixin handler HTTP mock ─────────────────────────────────────────


@pytest.fixture
def make_post_handler():
    """
    Factoría de handlers HTTP mock para tests de PostRoutesMixin.
    Uso: handler = make_post_handler("/v1/alguna/ruta", {"key": "val"})
    """
    import json
    from unittest.mock import MagicMock

    def _factory(path: str, body: dict = None, headers: dict = None):
        handler = MagicMock()
        handler.path = path
        handler.client_address = ("127.0.0.1", 9999)
        raw_body = json.dumps(body or {}).encode("utf-8")
        handler.headers = {
            "Content-Length": str(len(raw_body)),
            "Content-Type": "application/json",
            "Authorization": "",
            **(headers or {}),
        }
        handler.rfile.read.return_value = raw_body
        handler.wfile = MagicMock()
        handler._send_cors = MagicMock()
        return handler

    return _factory


# ── Fixture: RAG retriever con índice vacío ───────────────────────────────────


@pytest.fixture
def empty_rag_index(tmp_path, monkeypatch):
    """
    Proporciona un índice RAG vacío y temporal para tests que necesiten
    verificar el comportamiento cuando no hay documentos indexados.
    """
    from rag import vector_store

    monkeypatch.setattr(
        vector_store, "INDEX_PATH", str(tmp_path / "test_rag_index.json")
    )
    # Resetear el store en memoria
    monkeypatch.setattr(vector_store, "_store", {"chunks": [], "embeddings": []})
    return tmp_path / "test_rag_index.json"
