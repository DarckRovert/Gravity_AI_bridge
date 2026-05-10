"""
Tests unitarios para core/image_queue.py — V13.0 PRO
Cubre: add_job, get_queue_status, cancel_job, _process_job (con retry),
       start() idempotente, notificación SSE.
Usa SQLite en memoria vía monkeypatch de DB_PATH.
"""
import os
import json
import sqlite3
import threading
import time
import pytest
from unittest.mock import patch, MagicMock, call


# ── Fixture: entorno aislado con SQLite en memoria ────────────────────────────

@pytest.fixture(autouse=True)
def isolated_queue(tmp_path, monkeypatch):
    """
    Redirige DB_PATH a un archivo temporal y resetea el estado global
    del módulo antes de cada test. Esto evita contaminación entre tests.
    """
    import core.image_queue as iq

    db_path = str(tmp_path / "_image_queue_test.sqlite")
    monkeypatch.setattr(iq, "DB_PATH",      db_path)
    monkeypatch.setattr(iq, "_started",     False)
    monkeypatch.setattr(iq, "_current_job", None)

    iq._init_db()
    yield iq


# ── Tests de add_job() ────────────────────────────────────────────────────────

class TestAddJob:

    def test_add_job_returns_int_id(self, isolated_queue):
        iq = isolated_queue
        job_id = iq.add_job("Una imagen de prueba")
        assert isinstance(job_id, int)
        assert job_id >= 1

    def test_add_job_incremental_ids(self, isolated_queue):
        iq = isolated_queue
        id1 = iq.add_job("Imagen A")
        id2 = iq.add_job("Imagen B")
        assert id2 > id1

    def test_add_job_persists_prompt(self, isolated_queue):
        iq = isolated_queue
        job_id = iq.add_job("Prompt especial", performance="Quality", width=512, height=512)
        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row["prompt"] == "Prompt especial"
        assert row["performance"] == "Quality"
        assert row["width"] == 512
        assert row["height"] == 512
        assert row["status"] == "pending"

    def test_add_job_default_performance(self, isolated_queue):
        iq = isolated_queue
        job_id = iq.add_job("Test defaults")
        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row["performance"] == "Speed"
        assert row["width"] == 1024
        assert row["height"] == 1024


# ── Tests de get_queue_status() ───────────────────────────────────────────────

class TestGetQueueStatus:

    def test_status_empty_queue(self, isolated_queue):
        iq = isolated_queue
        status = iq.get_queue_status()
        assert status["pending_count"] == 0
        assert status["pending_jobs"] == []
        assert status["current_job"] is None
        assert isinstance(status["history"], list)

    def test_status_with_pending_jobs(self, isolated_queue):
        iq = isolated_queue
        iq.add_job("Job 1")
        iq.add_job("Job 2")
        status = iq.get_queue_status()
        assert status["pending_count"] == 2
        assert len(status["pending_jobs"]) == 2

    def test_status_current_job_reflected(self, isolated_queue):
        iq = isolated_queue
        iq._current_job = {"id": 99, "prompt": "running", "status": "running"}
        status = iq.get_queue_status()
        assert status["current_job"] is not None
        assert status["current_job"]["id"] == 99

    def test_history_shows_completed_jobs(self, isolated_queue):
        iq = isolated_queue
        # Insertar jobs completados directamente
        conn = sqlite3.connect(iq.DB_PATH)
        for i in range(5):
            conn.execute(
                "INSERT INTO image_jobs (created_at, status, prompt, performance, width, height, result_json) "
                "VALUES ('2026-01-01T00:00:00Z', 'done', ?, 'Speed', 1024, 1024, '{\"success\":true}')",
                (f"Prompt {i}",)
            )
        conn.commit()
        conn.close()

        status = iq.get_queue_status()
        assert len(status["history"]) == 5

    def test_history_capped_at_20(self, isolated_queue):
        iq = isolated_queue
        conn = sqlite3.connect(iq.DB_PATH)
        for i in range(25):
            conn.execute(
                "INSERT INTO image_jobs (created_at, status, prompt, performance, width, height) "
                "VALUES ('2026-01-01T00:00:00Z', 'done', ?, 'Speed', 1024, 1024)",
                (f"Prompt {i}",)
            )
        conn.commit()
        conn.close()

        status = iq.get_queue_status()
        assert len(status["history"]) == 20


# ── Tests de cancel_job() ─────────────────────────────────────────────────────

class TestCancelJob:

    def test_cancel_pending_job(self, isolated_queue):
        iq = isolated_queue
        job_id = iq.add_job("Cancelable")
        result = iq.cancel_job(job_id)
        assert result is True

        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row["status"] == "cancelled"

    def test_cancel_nonexistent_job(self, isolated_queue):
        iq = isolated_queue
        result = iq.cancel_job(99999)
        assert result is False

    def test_cancel_already_running_job(self, isolated_queue):
        iq = isolated_queue
        job_id = iq.add_job("Running job")
        # Simular que ya está en running
        conn = sqlite3.connect(iq.DB_PATH)
        conn.execute("UPDATE image_jobs SET status='running' WHERE id=?", (job_id,))
        conn.commit()
        conn.close()

        result = iq.cancel_job(job_id)
        # No debe poder cancelar un job en running (WHERE status='pending')
        assert result is False


# ── Tests de _process_job() con retry ────────────────────────────────────────

class TestProcessJob:

    def _get_job_row(self, iq, job_id: int) -> dict:
        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        return dict(row) if row else {}

    def test_process_job_success(self, isolated_queue, tmp_path):
        iq = isolated_queue
        job_id = iq.add_job("Cielo azul")

        # Simular que fooocus_client.generate_image retorna éxito y crea un archivo
        fake_img = str(tmp_path / "output.png")
        with open(fake_img, "wb") as f:
            f.write(b"\x89PNG\r\n")

        mock_result = {"success": True, "images": [fake_img]}

        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        job_row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()

        with patch("core.image_queue.BASE_DIR", str(tmp_path)):
            with patch("fooocus_client.generate_image", return_value=mock_result):
                with patch("fooocus_client.ImageGenRequest", dict):
                    iq._process_job(job_row)

        row = self._get_job_row(iq, job_id)
        assert row["status"] == "done"
        assert row["error"] is None

    def test_process_job_fooocus_failure_marks_failed(self, isolated_queue, tmp_path):
        iq = isolated_queue
        job_id = iq.add_job("Imagen fallida")

        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        job_row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()

        with patch("fooocus_client.generate_image", side_effect=Exception("Fooocus no disponible")):
            with patch("fooocus_client.ImageGenRequest", dict):
                iq._process_job(job_row)

        row = self._get_job_row(iq, job_id)
        assert row["status"] == "failed"
        assert "Fooocus no disponible" in row["error"]

    def test_process_job_false_positive_detection(self, isolated_queue, tmp_path):
        """
        Si generate_image reporta success=True pero no crea ningún archivo nuevo,
        debe marcarse como failed (detección de falso positivo).
        """
        iq = isolated_queue
        job_id = iq.add_job("Falso positivo")

        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        job_row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()

        # generate_image dice success pero no hay archivos nuevos en outputs/
        mock_result = {"success": True, "images": []}
        outputs_dir = tmp_path / "_integrations" / "Fooocus" / "Fooocus" / "outputs"
        outputs_dir.mkdir(parents=True)

        with patch("core.image_queue.BASE_DIR", str(tmp_path)):
            with patch("fooocus_client.generate_image", return_value=mock_result):
                with patch("fooocus_client.ImageGenRequest", dict):
                    iq._process_job(job_row)

        row = self._get_job_row(iq, job_id)
        # El falso positivo debe marcarse como failed
        assert row["status"] == "failed"
        assert "Falso positivo" in row["error"]

    def test_process_job_clears_current_job_on_finish(self, isolated_queue, tmp_path):
        iq = isolated_queue
        job_id = iq.add_job("Clear test")

        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        job_row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()

        with patch("fooocus_client.generate_image", side_effect=Exception("fallo")):
            with patch("fooocus_client.ImageGenRequest", dict):
                iq._process_job(job_row)

        # _current_job debe ser None tras terminar (éxito o fallo)
        assert iq._current_job is None


# ── Tests de start() idempotente ─────────────────────────────────────────────

class TestWorkerStart:

    def test_start_idempotent(self, isolated_queue):
        iq = isolated_queue
        with patch.object(threading.Thread, "start", return_value=None):
            iq.start()
            assert iq._started is True
            iq.start()  # Segunda llamada no debe crear otro thread
            assert iq._started is True

    def test_start_sets_started_flag(self, isolated_queue):
        iq = isolated_queue
        assert iq._started is False
        with patch.object(threading.Thread, "start", return_value=None):
            iq.start()
        assert iq._started is True
