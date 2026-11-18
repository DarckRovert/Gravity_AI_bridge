"""
tests/test_parallel_orchestrator.py — Pruebas unitarias para core/parallel_orchestrator.py
Verifica el Shared Contract Protocol, dispatching paralelo asíncrono, locks y TTL cleanup.
"""
import time
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from core.parallel_orchestrator import (
    AgentResult,
    OrchestrationHandle,
    _build_shared_contract,
    _run_agent,
    _prune_stale,
    dispatch,
    get_orchestration,
    list_orchestrations,
    _active,
    _ORCH_LOCK,
)
from core.subagent_loader import AgentDefinition


@pytest.fixture
def dummy_agent():
    return AgentDefinition(
        name="test_worker",
        description="Agente de prueba para orquestación",
        mode="subagent",
        model="auto",
        provider="auto",
        temperature=0.2,
        max_tokens=1024,
        permissions={},
        system_prompt="Eres un agente de prueba.",
        source_file="test_worker.md",
    )


def test_agent_result_locking():
    res = AgentResult(agent_name="agent_a")
    assert res.status == "pending"
    with res._lock:
        res.status = "running"
        res.output = "trabajando..."
    assert res.status == "running"
    assert res.output == "trabajando..."


def test_orchestration_handle_to_dict():
    handle = OrchestrationHandle(
        orchestration_id="test1234",
        goal="Objetivo global",
        agent_results={
            "agent_1": AgentResult(agent_name="agent_1", status="done", output="Completado OK")
        },
    )
    data = handle.to_dict()
    assert data["orchestration_id"] == "test1234"
    assert data["status"] == "running"
    assert "agent_1" in data["agents"]
    assert data["agents"]["agent_1"]["status"] == "done"
    assert "Completado OK" in data["agents"]["agent_1"]["output_preview"]


def test_build_shared_contract(dummy_agent):
    contract = _build_shared_contract("Construir API", [dummy_agent])
    assert "CONTRATO COMPARTIDO DE ORQUESTACIÓN" in contract
    assert "Construir API" in contract
    assert "test_worker" in contract
    assert "Zonas de Responsabilidad" in contract


def test_run_agent_success(dummy_agent):
    result = AgentResult(agent_name=dummy_agent.name)
    with patch("tools.gravity_delegate.delegate_task") as mock_del:
        mock_del.return_value = {
            "success": True,
            "text": "Salida exitosa",
            "model": "model_x",
            "provider": "provider_y",
        }
        _run_agent(dummy_agent, "Hacer tarea", "Contrato", result)

    assert result.status == "done"
    assert result.output == "Salida exitosa"
    assert result.model_used == "model_x"
    assert result.provider_used == "provider_y"
    assert result.finished_at is not None


def test_run_agent_failure(dummy_agent):
    result = AgentResult(agent_name=dummy_agent.name)
    with patch("tools.gravity_delegate.delegate_task") as mock_del:
        mock_del.return_value = {
            "success": False,
            "error": "Timeout de inferencia",
        }
        _run_agent(dummy_agent, "Hacer tarea", "Contrato", result)

    assert result.status == "failed"
    assert "Timeout de inferencia" in result.error
    assert result.finished_at is not None


def test_prune_stale_cleanup():
    # Añade una orquestación expirada (> 3600s) y una reciente
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=4000)).isoformat()
    recent_time = datetime.now(timezone.utc).isoformat()

    h_old = OrchestrationHandle(
        orchestration_id="old_orch",
        goal="Vieja",
        status="done",
        finished_at=old_time,
    )
    h_new = OrchestrationHandle(
        orchestration_id="new_orch",
        goal="Nueva",
        status="done",
        finished_at=recent_time,
    )

    with _ORCH_LOCK:
        _active["old_orch"] = h_old
        _active["new_orch"] = h_new

    _prune_stale()

    with _ORCH_LOCK:
        assert "old_orch" not in _active
        assert "new_orch" in _active
        # Limpieza posterior
        _active.pop("new_orch", None)


def test_dispatch_invalid_agent():
    with pytest.raises(ValueError, match="Ninguno de los agentes existe"):
        dispatch(goal="Test", agent_names=["agente_totalmente_inexistente"])


def test_dispatch_e2e_with_mock():
    completed_handles = []

    def on_done(handle):
        completed_handles.append(handle.orchestration_id)

    with patch("tools.gravity_delegate.delegate_task") as mock_del:
        mock_del.return_value = {
            "success": True,
            "text": "Trabajo paralelo completado",
            "model": "gpt-oss",
            "provider": "Groq",
        }
        handle = dispatch(
            goal="Test Paralelo",
            agent_names=["backend_specialist", "qa_tester"],
            task_per_agent={
                "backend_specialist": "Tarea backend",
                "qa_tester": "Tarea qa",
                "desconocido_xyz": "Ignorado con warning",
            },
            on_complete=on_done,
        )

        assert handle.status == "running"
        assert "backend_specialist" in handle.agent_results
        assert "qa_tester" in handle.agent_results

        # Esperar a que el hilo coordinador finalice (máx 5s)
        start = time.time()
        while time.time() - start < 5:
            if handle.status in ("done", "failed"):
                break
            time.sleep(0.1)

        assert handle.status == "done"
        assert handle.agent_results["backend_specialist"].status == "done"
        assert handle.agent_results["qa_tester"].status == "done"
        assert handle.orchestration_id in completed_handles

        # Verificar consulta por API
        found = get_orchestration(handle.orchestration_id)
        assert found is not None
        assert found.orchestration_id == handle.orchestration_id

        all_orch = list_orchestrations()
        assert any(o["orchestration_id"] == handle.orchestration_id for o in all_orch)
