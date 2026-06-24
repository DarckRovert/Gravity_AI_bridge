"""
Tests unitarios para core/session_runner.py — V16.0 PRO
Cubre: BoundedSemaphore, SessionHandle, spawn(), terminate(), shutdown(), reaper.
"""

import subprocess
import threading
import pytest
from unittest.mock import patch, MagicMock

# ── Fixture: entorno aislado ───────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_sessions():
    """Limpia el registro global de sesiones y resetea el semáforo antes de cada test."""
    import core.session_runner as sr

    # Terminar sesiones residuales
    with sr._lock:
        for handle in list(sr.active_sessions.values()):
            try:
                handle.terminate()
            except Exception:
                pass
        sr.active_sessions.clear()

    # Resetear semáforo a estado limpio
    # BoundedSemaphore no tiene reset() — lo recreamos
    sr._semaphore = threading.BoundedSemaphore(sr._CAPACITY)

    yield sr

    # Cleanup post-test
    with sr._lock:
        for handle in list(sr.active_sessions.values()):
            try:
                handle.terminate()
            except Exception:
                pass
        sr.active_sessions.clear()


def _make_mock_proc(alive: bool = True, pid: int = 9999) -> MagicMock:
    """Crea un Popen mock configurable."""
    proc = MagicMock(spec=subprocess.Popen)
    proc.pid = pid
    proc.poll.return_value = None if alive else 0
    proc.stdin = MagicMock()
    proc.stdout = MagicMock()
    proc.stderr = MagicMock()
    return proc


# ── Tests de CapacityWake / BoundedSemaphore ───────────────────────────────────


class TestBoundedSemaphore:

    def test_semaphore_initial_capacity(self, clean_sessions):
        sr = clean_sessions
        # El semáforo debe tener capacidad inicial = _CAPACITY
        assert sr._semaphore._value == sr._CAPACITY

    def test_semaphore_acquire_release(self, clean_sessions):
        sr = clean_sessions
        acquired = sr._semaphore.acquire(timeout=1)
        assert acquired is True
        assert sr._semaphore._value == sr._CAPACITY - 1
        sr._semaphore.release()
        assert sr._semaphore._value == sr._CAPACITY

    def test_semaphore_blocks_at_capacity(self, clean_sessions):
        sr = clean_sessions
        # Ocupar todos los slots
        for _ in range(sr._CAPACITY):
            sr._semaphore.acquire()
        # El siguiente acquire con timeout debe fallar
        result = sr._semaphore.acquire(timeout=0.1)
        assert result is False
        # Liberar todos
        for _ in range(sr._CAPACITY):
            sr._semaphore.release()


# ── Tests de SessionHandle ────────────────────────────────────────────────────


class TestSessionHandle:

    def test_is_alive_true_when_process_running(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=True)
        handle = sr.SessionHandle("test-001", proc)
        assert handle.is_alive() is True

    def test_is_alive_false_when_process_dead(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=False)
        handle = sr.SessionHandle("test-002", proc)
        assert handle.is_alive() is False

    def test_update_activity_stores_last(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc()
        handle = sr.SessionHandle("test-003", proc)
        handle.update_activity({"type": "chat", "msg": "hola"})
        assert handle.current_activity["type"] == "chat"
        assert len(handle.activities) == 1

    def test_activity_history_capped_at_10(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc()
        handle = sr.SessionHandle("test-004", proc)
        for i in range(15):
            handle.update_activity({"index": i})
        assert len(handle.activities) == 10
        assert handle.activities[-1]["index"] == 14

    def test_terminate_releases_semaphore_slot(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=True)
        # Simular que el handle adquirió el slot
        sr._semaphore.acquire()
        initial = sr._semaphore._value
        handle = sr.SessionHandle("test-005", proc)
        handle._released = False  # simular slot adquirido

        handle.terminate()

        # El slot debe haber sido liberado
        assert sr._semaphore._value == initial + 1

    def test_terminate_idempotent(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=False)
        sr._semaphore.acquire()
        handle = sr.SessionHandle("test-006", proc)
        handle._released = False

        handle.terminate()
        handle.terminate()  # Segunda llamada no debe lanzar ValueError

        # Semáforo no debe sobre-releasarse
        assert sr._semaphore._value <= sr._CAPACITY

    def test_to_dict_structure(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc()
        handle = sr.SessionHandle("test-007", proc)
        d = handle.to_dict()
        assert "session_id" in d
        assert "start_time" in d
        assert "alive" in d
        assert "pid" in d
        assert d["session_id"] == "test-007"


# ── Tests de SessionSpawner ───────────────────────────────────────────────────


class TestSessionSpawner:

    def test_spawn_registers_session(self, clean_sessions):
        sr = clean_sessions
        mock_proc = _make_mock_proc(pid=1234)

        with patch("subprocess.Popen", return_value=mock_proc):
            spawner = sr.SessionSpawner(
                python_executable="python", script_path="fake.py"
            )
            handle = spawner.spawn("sess-001", {})

        assert "sess-001" in sr.active_sessions
        assert handle.session_id == "sess-001"

    def test_spawn_acquires_semaphore_slot(self, clean_sessions):
        sr = clean_sessions
        mock_proc = _make_mock_proc()
        before = sr._semaphore._value

        with patch("subprocess.Popen", return_value=mock_proc):
            spawner = sr.SessionSpawner()
            spawner.spawn("sess-002", {})

        assert sr._semaphore._value == before - 1

    def test_spawn_releases_slot_on_popen_failure(self, clean_sessions):
        sr = clean_sessions
        before = sr._semaphore._value

        with patch("subprocess.Popen", side_effect=OSError("binario no encontrado")):
            spawner = sr.SessionSpawner()
            with pytest.raises(RuntimeError, match="Popen falló"):
                spawner.spawn("sess-003", {})

        # El slot debe haberse liberado
        assert sr._semaphore._value == before

    def test_spawn_raises_when_at_capacity(self, clean_sessions):
        sr = clean_sessions
        # Ocupar todos los slots
        for _ in range(sr._CAPACITY):
            sr._semaphore.acquire()

        spawner = sr.SessionSpawner()
        with pytest.raises(RuntimeError, match="Capacidad máxima"):
            spawner.spawn("sess-overflow", {})

        # Restaurar
        for _ in range(sr._CAPACITY):
            sr._semaphore.release()


# ── Tests de API pública ───────────────────────────────────────────────────────


class TestPublicAPI:

    def test_get_all_sessions_empty(self, clean_sessions):
        sr = clean_sessions
        result = sr.get_all_sessions()
        assert result == []

    def test_get_all_sessions_returns_dicts(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc()
        handle = sr.SessionHandle("s1", proc)
        with sr._lock:
            sr.active_sessions["s1"] = handle
        result = sr.get_all_sessions()
        assert len(result) == 1
        assert result[0]["session_id"] == "s1"

    def test_get_session_found(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc()
        handle = sr.SessionHandle("s2", proc)
        with sr._lock:
            sr.active_sessions["s2"] = handle
        assert sr.get_session("s2") is handle

    def test_get_session_not_found(self, clean_sessions):
        sr = clean_sessions
        assert sr.get_session("no-existe") is None

    def test_terminate_session_removes_from_registry(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=False)
        handle = sr.SessionHandle("s3", proc)
        handle._released = True  # evitar ValueError en BoundedSemaphore
        with sr._lock:
            sr.active_sessions["s3"] = handle
        result = sr.terminate_session("s3")
        assert result is True
        assert "s3" not in sr.active_sessions

    def test_terminate_session_nonexistent(self, clean_sessions):
        sr = clean_sessions
        result = sr.terminate_session("no-existe")
        assert result is False


# ── Tests de reap_dead_sessions ───────────────────────────────────────────────


class TestOrphanReaper:

    def test_reap_removes_dead_session(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=False)
        sr._semaphore.acquire()
        handle = sr.SessionHandle("dead-001", proc)
        handle._released = False
        with sr._lock:
            sr.active_sessions["dead-001"] = handle

        reaped = sr._reap_dead_sessions()

        assert reaped == 1
        assert "dead-001" not in sr.active_sessions

    def test_reap_keeps_alive_session(self, clean_sessions):
        sr = clean_sessions
        proc = _make_mock_proc(alive=True)
        sr._semaphore.acquire()
        handle = sr.SessionHandle("alive-001", proc)
        with sr._lock:
            sr.active_sessions["alive-001"] = handle

        reaped = sr._reap_dead_sessions()

        assert reaped == 0
        assert "alive-001" in sr.active_sessions
        # Cleanup manual
        sr._semaphore.release()
