"""
Tests unitarios para core/video_pipeline.py — V15.2 PRO
Cubre: cola SQLite, add_job, cancel_job, get_queue_status,
       _generate_script (fallback), _generate_audio (mock),
       _assemble_clip (ffmpeg ausente), start() idempotente.
"""
import os
import json
import sqlite3
import tempfile
import threading
import pytest
from unittest.mock import patch, MagicMock


# ── Fixture: entorno aislado ──────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_video_env(tmp_path, monkeypatch):
    """Redirige DB_PATH, OUTPUT_DIR y FFMPEG_EXE a rutas temporales."""
    import core.video_pipeline as vp

    db_path    = str(tmp_path / "_video_queue.sqlite")
    output_dir = str(tmp_path / "_videos")
    os.makedirs(output_dir, exist_ok=True)

    monkeypatch.setattr(vp, "DB_PATH",     db_path)
    monkeypatch.setattr(vp, "OUTPUT_DIR",  output_dir)
    monkeypatch.setattr(vp, "FFMPEG_EXE",  str(tmp_path / "ffmpeg_fake.exe"))
    monkeypatch.setattr(vp, "_started",    False)
    monkeypatch.setattr(vp, "_current_job", None)
    monkeypatch.setattr(vp, "_db_initialized", False)

    # Evitar llamadas de red reales (auto-investigación web y análisis de competidores)
    try:
        import core.web_search
        monkeypatch.setattr(core.web_search, "search_and_scrape", MagicMock(return_value=""))
    except Exception:
        pass
    try:
        import core.market_researcher
        monkeypatch.setattr(core.market_researcher, "analyze_competitors", MagicMock(return_value=""))
    except Exception:
        pass

    vp._init_db()
    yield vp


# ── Tests de cola ─────────────────────────────────────────────────────────────

class TestJobQueue:

    def test_add_job_returns_int(self, isolated_video_env):
        vp = isolated_video_env
        job_id = vp.add_job("Historia del jazz", n_scenes=4, voice_speed=150)
        assert isinstance(job_id, int)
        assert job_id >= 1

    def test_add_multiple_jobs_incremental_ids(self, isolated_video_env):
        vp = isolated_video_env
        id1 = vp.add_job("Tema A")
        id2 = vp.add_job("Tema B")
        assert id2 > id1

    def test_get_queue_status_empty(self, isolated_video_env):
        vp = isolated_video_env
        status = vp.get_queue_status()
        assert status["pending_count"] == 0
        assert status["pending_jobs"] == []
        assert status["current_job"] is None
        assert isinstance(status["history"], list)
        assert "ffmpeg_ok" in status

    def test_get_queue_status_pending(self, isolated_video_env):
        vp = isolated_video_env
        vp.add_job("Test pendiente")
        status = vp.get_queue_status()
        assert status["pending_count"] == 1
        assert status["pending_jobs"][0]["topic"] == "Test pendiente"

    def test_cancel_pending_job(self, isolated_video_env):
        vp = isolated_video_env
        job_id = vp.add_job("Cancelable")
        result = vp.cancel_job(job_id)
        assert result is True
        # Verificar en la DB que está cancelado
        conn = sqlite3.connect(vp.DB_PATH)
        row  = conn.execute("SELECT status FROM video_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row[0] == "cancelled"

    def test_cancel_nonexistent_job_returns_false(self, isolated_video_env):
        vp = isolated_video_env
        result = vp.cancel_job(99999)
        assert result is False

    def test_ffmpeg_ok_false_when_missing(self, isolated_video_env):
        vp = isolated_video_env
        status = vp.get_queue_status()
        # FFMPEG_EXE apunta a un archivo que no existe en tmp_path
        assert status["ffmpeg_ok"] is False

    def test_history_limit_20(self, isolated_video_env):
        vp = isolated_video_env
        # Insertar 25 jobs completados directamente en la DB
        conn = sqlite3.connect(vp.DB_PATH)
        for i in range(25):
            conn.execute(
                "INSERT INTO video_jobs (topic, n_scenes, voice_speed, status, created_at) "
                "VALUES (?, 4, 150, 'done', '2026-01-01T00:00:00Z')",
                (f"Tema {i}",)
            )
        conn.commit()
        conn.close()
        status = vp.get_queue_status()
        assert len(status["history"]) == 20


# ── Tests de generación de guión ──────────────────────────────────────────────

class TestScriptGeneration:

    def test_fallback_script_structure(self, isolated_video_env):
        vp = isolated_video_env
        # Sin LLM disponible → fallback a guión de ejemplo
        with patch("urllib.request.urlopen", side_effect=Exception("LLM not running")):
            scenes, anchor, title = vp._generate_script("Inteligencia Artificial", n_scenes=3, style="documental", narration_lang="es")
        assert len(scenes) == 3
        for scene in scenes:
            assert "title" in scene
            assert "image_prompt" in scene
            assert "narration" in scene

    def test_fallback_respects_n_scenes(self, isolated_video_env):
        vp = isolated_video_env
        with patch("urllib.request.urlopen", side_effect=Exception("no llm")):
            scenes, anchor, title = vp._generate_script("Tema X", n_scenes=6, style="documental", narration_lang="es")
        assert len(scenes) == 6

    @patch("core.provider_manager.get_best")
    @patch("core.multi_agent.run_pipeline")
    def test_llm_response_parsed_correctly(self, mock_run_pipeline, mock_get_best, isolated_video_env):
        vp = isolated_video_env
        fake_scenes = [
            {"title": "T1", "character_anchor": "Anchor 1", "image_prompt": "P1", "narration": "N1"},
            {"title": "T2", "character_anchor": "Anchor 2", "image_prompt": "P2", "narration": "N2"},
        ]
        fake_data = {
            "video_title": "Fake Title",
            "scenes": fake_scenes
        }
        mock_get_best.return_value = (MagicMock(name="FalsoProv"), "FalsoModel")
        mock_run_pipeline.return_value = json.dumps(fake_data)

        scenes, anchor, title = vp._generate_script("Test", n_scenes=2, style="documental", narration_lang="es")
        assert len(scenes) == 2
        assert scenes[0]["title"] == "T1"
        assert title == "Fake Title"


# ── Tests TTS ─────────────────────────────────────────────────────────────────

class TestTTS:

    def test_generate_audio_failure_returns_false(self, isolated_video_env, tmp_path, monkeypatch):
        vp = isolated_video_env
        monkeypatch.setattr(vp.os, "name", "posix")
        # pyttsx3 falla → debe retornar False sin lanzar excepción
        with patch("pyttsx3.init", side_effect=Exception("SAPI not available")):
            result = vp._generate_audio("Texto de prueba", str(tmp_path / "out.wav"))
        assert result is False

    def test_generate_audio_success(self, isolated_video_env, tmp_path, monkeypatch):
        vp = isolated_video_env
        monkeypatch.setattr(vp.os, "name", "posix")
        wav = str(tmp_path / "test.wav")
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.id = "spanish_voice"
        mock_voice.name = "Helena"
        mock_voice.languages = ["es_ES"]
        mock_engine.getProperty.return_value = [mock_voice]

        def fake_save(text, path):
            # Simular creación del archivo
            with open(path, "wb") as f:
                f.write(b"\x00" * 1024)

        mock_engine.save_to_file.side_effect = fake_save
        with patch("pyttsx3.init", return_value=mock_engine):
            result = vp._generate_audio("Hola mundo", wav, rate=150)
        assert result is True
        assert os.path.isfile(wav)


# ── Tests de ensamblado de clips ──────────────────────────────────────────────

class TestClipAssembly:

    def test_assemble_clip_no_ffmpeg_returns_false(self, isolated_video_env, tmp_path):
        vp = isolated_video_env
        img = str(tmp_path / "img.png")
        out = str(tmp_path / "clip.mp4")
        # Crear imagen PNG mínima válida
        with open(img, "wb") as f:
            f.write(bytes([
                0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,
                0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,
                0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
                0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
                0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,
                0x54,0x08,0xD7,0x63,0xF8,0xCF,0xC0,0x00,
                0x00,0x00,0x02,0x00,0x01,0xE2,0x21,0xBC,
                0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,
                0x44,0xAE,0x42,0x60,0x82
            ]))
        # FFMPEG_EXE apunta a ruta inexistente → debe retornar False limpiamente
        result = vp._assemble_clip(img, None, out)
        assert result is False


# ── Tests de start() idempotente ──────────────────────────────────────────────

class TestWorkerDaemon:

    def test_start_idempotent(self, isolated_video_env):
        vp = isolated_video_env
        # Mockear _worker_loop para que no enganche un hilo real
        with patch.object(threading.Thread, "start", return_value=None):
            vp.start()
            assert vp._started is True
            # Segunda llamada no debe lanzar error ni crear segundo hilo
            vp.start()
            assert vp._started is True

    def test_get_video_url_empty_path(self, isolated_video_env):
        vp = isolated_video_env
        assert vp.get_video_url("") == ""

    def test_get_video_url_extracts_filename(self, isolated_video_env):
        vp = isolated_video_env
        url = vp.get_video_url("F:/Gravity_AI_bridge/_videos/video_1_test_20260420.mp4")
        assert url == "/v1/video/download?file=video_1_test_20260420.mp4"
