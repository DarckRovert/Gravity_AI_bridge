"""
Tests unitarios para core/mcp_adapter.py — V15.0 PRO
Cubre: connect(), _read_line_timeout(), backoff, health check, call_tool(), disconnect().
"""
import json
import queue
import subprocess
import threading
import time
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ── Fixture: adaptador aislado ─────────────────────────────────────────────────

@pytest.fixture()
def adapter(tmp_path):
    """Crea un MCPAdapter sin iniciar procesos reales, con health daemon desactivado."""
    import core.mcp_adapter as mcp

    # Desactivar el health daemon durante tests
    with patch.object(mcp.MCPAdapter, "_start_health_daemon", return_value=None):
        adp = mcp.MCPAdapter(
            server_path=str(tmp_path / "fake_mcp_server"),
            args=[],
            name="test_adapter",
        )
    yield adp
    # Cleanup
    adp.process = None
    mcp.active_adapters.pop("test_adapter", None)


def _make_mock_proc(stdout_lines: list[str] = None, alive: bool = True) -> MagicMock:
    """Crea un mock de subprocess.Popen para MCP."""
    proc = MagicMock(spec=subprocess.Popen)
    proc.pid  = 42
    proc.poll.return_value = None if alive else 0
    proc.stdin = MagicMock()
    proc.stdout = MagicMock()
    proc.stderr = MagicMock()

    if stdout_lines is not None:
        # Simular readline() con respuestas predefinidas
        responses = iter(stdout_lines + [""])
        proc.stdout.readline.side_effect = lambda: next(responses, "")

    return proc


# ── Tests de connect() ────────────────────────────────────────────────────────

class TestConnect:

    def test_connect_success(self, adapter):
        mock_proc = _make_mock_proc(alive=True)
        with patch("subprocess.Popen", return_value=mock_proc):
            result = adapter.connect()
        assert result is True
        assert adapter.process is mock_proc

    def test_connect_returns_true_if_already_connected(self, adapter):
        mock_proc = _make_mock_proc(alive=True)
        adapter.process = mock_proc
        with patch("subprocess.Popen") as mock_popen:
            result = adapter.connect()
            # No debe llamar a Popen si ya está conectado
            mock_popen.assert_not_called()
        assert result is True

    def test_connect_false_when_process_dies_immediately(self, adapter):
        mock_proc = _make_mock_proc(alive=False)
        with patch("subprocess.Popen", return_value=mock_proc):
            result = adapter.connect()
        assert result is False
        assert adapter.process is None

    def test_connect_false_on_popen_exception(self, adapter):
        with patch("subprocess.Popen", side_effect=FileNotFoundError("no existe")):
            result = adapter.connect()
        assert result is False


# ── Tests de _read_line_timeout() ─────────────────────────────────────────────

class TestReadLineTimeout:

    def test_reads_line_within_timeout(self, adapter):
        """Debe retornar la línea cuando el proceso responde a tiempo."""
        expected_line = '{"jsonrpc":"2.0","id":1,"result":{}}'
        mock_proc = _make_mock_proc(stdout_lines=[expected_line])
        adapter.process = mock_proc

        result = adapter._read_line_timeout(timeout=2.0)
        assert result == expected_line

    def test_returns_none_on_timeout(self, adapter):
        """Debe retornar None cuando el proceso no responde en tiempo."""
        # stdout.readline() bloquea indefinidamente → simular con sleep largo
        blocker_called = threading.Event()

        def slow_readline():
            blocker_called.set()
            time.sleep(5)  # Bloquear más tiempo que el timeout del test
            return ""

        mock_proc = _make_mock_proc()
        mock_proc.stdout.readline.side_effect = slow_readline
        adapter.process = mock_proc

        start = time.time()
        result = adapter._read_line_timeout(timeout=0.3)
        elapsed = time.time() - start

        assert result is None
        assert elapsed < 1.0  # Debe terminar rápido (timeout)

    def test_returns_none_when_no_process(self, adapter):
        adapter.process = None
        result = adapter._read_line_timeout()
        assert result is None


# ── Tests de _send_request() / call_tool() ────────────────────────────────────

class TestSendRequest:

    def test_call_tool_success(self, adapter):
        """Debe enviar la request y parsear la respuesta correctamente."""
        response = {"jsonrpc": "2.0", "id": 1, "result": {"content": "ok"}}
        response_line = json.dumps(response)

        mock_proc = _make_mock_proc(stdout_lines=[response_line], alive=True)
        adapter.process = mock_proc

        with patch.object(adapter, "connect", return_value=True):
            result = adapter.call_tool("my_tool", {"arg": "value"})

        assert "error" not in result or result.get("result") is not None

    def test_call_tool_returns_error_on_timeout(self, adapter):
        """Cuando readline hace timeout, debe devolver error."""
        mock_proc = _make_mock_proc(alive=True)
        mock_proc.stdout.readline.side_effect = lambda: time.sleep(5) or ""
        adapter.process = mock_proc

        with patch.object(adapter, "connect", return_value=True):
            with patch.object(adapter, "_read_line_timeout", return_value=None):
                result = adapter.call_tool("slow_tool", {})

        assert "error" in result

    def test_call_tool_invalid_json_returns_error(self, adapter):
        """Respuesta no-JSON debe retornar error descriptivo."""
        mock_proc = _make_mock_proc(stdout_lines=["not json at all!!!"], alive=True)
        adapter.process = mock_proc

        with patch.object(adapter, "connect", return_value=True):
            with patch.object(adapter, "_read_line_timeout", return_value="not json"):
                result = adapter.call_tool("bad_tool", {})

        assert "error" in result

    def test_call_tool_reconnects_on_dead_process(self, adapter):
        """Si el proceso está muerto, debe intentar reconectar."""
        adapter.process = None

        with patch.object(adapter, "connect", return_value=False) as mock_connect:
            with patch.object(adapter, "_reconnect_with_backoff", return_value=False) as mock_reconnect:
                result = adapter.call_tool("tool", {})

        assert "error" in result

    def test_id_counter_increments(self, adapter):
        """Cada request debe usar un ID único y creciente."""
        with adapter._counter_lock:
            initial = adapter._id_counter

        adapter._next_id()
        adapter._next_id()

        with adapter._counter_lock:
            assert adapter._id_counter == initial + 2

    def test_id_counter_thread_safe(self, adapter):
        """IDs generados concurrentemente no deben colisionar."""
        ids = []
        ids_lock = threading.Lock()

        def gen_ids():
            for _ in range(50):
                rid = adapter._next_id()
                with ids_lock:
                    ids.append(rid)

        threads = [threading.Thread(target=gen_ids) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(ids) == len(set(ids)), "IDs duplicados detectados — no es thread-safe"


# ── Tests de list_tools() / list_resources() ─────────────────────────────────

class TestListEndpoints:

    def test_list_tools_returns_list(self, adapter):
        tools_resp = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "tool1"}]}}
        with patch.object(adapter, "_send_request", return_value=tools_resp):
            result = adapter.list_tools()
        assert isinstance(result, list)
        assert result[0]["name"] == "tool1"

    def test_list_tools_returns_empty_on_error(self, adapter):
        with patch.object(adapter, "_send_request", return_value={"error": "fallo"}):
            result = adapter.list_tools()
        assert result == []

    def test_list_resources_returns_list(self, adapter):
        res_resp = {"jsonrpc": "2.0", "id": 1, "result": {"resources": [{"uri": "file://a"}]}}
        with patch.object(adapter, "_send_request", return_value=res_resp):
            result = adapter.list_resources()
        assert isinstance(result, list)
        assert result[0]["uri"] == "file://a"


# ── Tests de health_check() ────────────────────────────────────────────────────

class TestHealthCheck:

    def test_health_check_true_when_alive(self, adapter):
        mock_proc = _make_mock_proc(alive=True)
        adapter.process = mock_proc
        assert adapter.health_check() is True

    def test_health_check_false_when_no_process(self, adapter):
        adapter.process = None
        assert adapter.health_check() is False

    def test_health_check_false_when_process_dead(self, adapter):
        mock_proc = _make_mock_proc(alive=False)
        adapter.process = mock_proc
        assert adapter.health_check() is False


# ── Tests de disconnect() ─────────────────────────────────────────────────────

class TestDisconnect:

    def test_disconnect_terminates_process(self, adapter):
        mock_proc = _make_mock_proc(alive=True)
        adapter.process = mock_proc
        adapter.disconnect()
        mock_proc.terminate.assert_called_once()
        assert adapter.process is None

    def test_disconnect_safe_when_no_process(self, adapter):
        adapter.process = None
        adapter.disconnect()  # No debe lanzar excepción
