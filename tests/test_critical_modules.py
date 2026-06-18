"""
╔══════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — TEST SUITE V16.0 PRO                                        ║
║  Cobertura crítica: audit_log, image_queue, security_monitor,        ║
║  engine_watchdog, game_server_manager, mixin_post (LLM route)        ║
╚══════════════════════════════════════════════════════════════════════╝

Ejecutar:
    pytest tests/ -v

Dependencias de test:
    pytest, pytest-mock (incluidas en requirements.txt)
"""

import json
import os
import sys
import sqlite3
import threading
import time
import hashlib
import tempfile
from collections import deque
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Asegurar que la raíz del proyecto está en sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ══════════════════════════════════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════════════════════════════════

class TestAuditLog:
    """Tests para core/audit_log.py — V3 con rotación dual y deque."""

    def _make_logger(self, tmp_path):
        from core.audit_log import AuditLogger
        return AuditLogger(log_path=str(tmp_path / "test_audit.jsonl"))

    def test_record_crea_entrada_valida(self, tmp_path):
        logger = self._make_logger(tmp_path)
        logger.record("s1", "ollama", "llama3", 100, 200, 0.0, 350.0)

        lines = (tmp_path / "test_audit.jsonl").read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["session_id"] == "s1"
        assert entry["provider"] == "ollama"
        assert entry["model"] == "llama3"
        assert entry["input_tokens"] == 100
        assert entry["output_tokens"] == 200
        assert entry["total_tokens"] == 300
        assert entry["cost_usd"] == 0.0
        assert entry["latency_ms"] == 350.0
        assert "timestamp" in entry

    def test_get_recent_retorna_ultimas_n_entradas(self, tmp_path):
        logger = self._make_logger(tmp_path)
        for i in range(20):
            logger.record(f"s{i}", "provider", "model", i, i, 0.0, 100.0)
        recent = logger.get_recent(5)
        assert len(recent) == 5
        # Las últimas deben tener los IDs más altos
        assert recent[-1]["session_id"] == "s19"

    def test_get_recent_archivo_inexistente_retorna_lista_vacia(self, tmp_path):
        logger = self._make_logger(tmp_path)
        result = logger.get_recent(10)
        assert result == []

    def test_rotacion_por_lineas(self, tmp_path):
        """Cuando se llega a MAX_LINES el archivo debe rotar."""
        logger = self._make_logger(tmp_path)
        # Forzar rotación reduciendo el umbral temporalmente
        import core.audit_log as al_module
        original_max = al_module.MAX_LINES
        al_module.MAX_LINES = 5
        try:
            for i in range(7):
                logger.record(f"s{i}", "p", "m", 1, 1, 0.0, 1.0)
            # Debe existir al menos un .bak
            baks = list(tmp_path.glob("*.bak.*.jsonl"))
            assert len(baks) >= 1
        finally:
            al_module.MAX_LINES = original_max

    def test_rotacion_por_bytes(self, tmp_path):
        """Cuando el archivo supera MAX_BYTES debe rotar."""
        import core.audit_log as al_module
        original_max = al_module.MAX_BYTES
        al_module.MAX_BYTES = 200  # 200 bytes — muy pequeño para forzar rotación rápida
        try:
            logger = self._make_logger(tmp_path)
            logger._line_count = 0
            for i in range(10):
                logger.record(f"s{i}", "provider_nombre_largo", "modelo_nombre_largo", 1000, 2000, 0.05, 1234.5)
            baks = list(tmp_path.glob("*.bak.*.jsonl"))
            assert len(baks) >= 1
        finally:
            al_module.MAX_BYTES = original_max

    def test_linea_count_se_actualiza_en_record(self, tmp_path):
        logger = self._make_logger(tmp_path)
        assert logger._line_count == 0
        logger.record("s1", "p", "m", 1, 1, 0.0, 1.0)
        assert logger._line_count == 1
        logger.record("s2", "p", "m", 1, 1, 0.0, 1.0)
        assert logger._line_count == 2

    def test_get_recent_usa_deque_no_falla_con_archivo_grande(self, tmp_path):
        """get_recent no debe cargar todo el archivo — solo las últimas N líneas."""
        log_path = tmp_path / "test_audit.jsonl"
        # Generar 1000 líneas directamente
        with open(log_path, "w") as f:
            for i in range(1000):
                f.write(json.dumps({"session_id": f"s{i}", "provider": "p",
                                    "model": "m", "input_tokens": i,
                                    "output_tokens": i, "total_tokens": i * 2,
                                    "latency_ms": 1.0, "cost_usd": 0.0,
                                    "timestamp": "2026-04-20T00:00:00Z"}) + "\n")
        from core.audit_log import AuditLogger
        logger = AuditLogger(log_path=str(log_path))
        recent = logger.get_recent(10)
        assert len(recent) == 10
        assert recent[-1]["session_id"] == "s999"


# ══════════════════════════════════════════════════════════════════════
# IMAGE QUEUE
# ══════════════════════════════════════════════════════════════════════

class TestImageQueue:
    """Tests para core/image_queue.py — cola SQLite + worker daemon."""

    @pytest.fixture(autouse=True)
    def patch_db(self, tmp_path, monkeypatch):
        """Redirigir DB_PATH a un archivo temporal para aislamiento total."""
        import core.image_queue as iq
        monkeypatch.setattr(iq, "DB_PATH", str(tmp_path / "test_queue.sqlite"))
        # Resetear estado global para cada test
        monkeypatch.setattr(iq, "_started", False)
        monkeypatch.setattr(iq, "_current_job", None)
        iq._init_db()
        yield

    def test_add_job_retorna_id_entero(self):
        import core.image_queue as iq
        job_id = iq.add_job("un cisne sobre un lago")
        assert isinstance(job_id, int)
        assert job_id >= 1

    def test_add_job_multiples_retorna_ids_incrementales(self):
        import core.image_queue as iq
        id1 = iq.add_job("prompt 1")
        id2 = iq.add_job("prompt 2")
        assert id2 > id1

    def test_get_queue_status_refleja_trabajos_pendientes(self):
        import core.image_queue as iq
        iq.add_job("prompt A")
        iq.add_job("prompt B")
        status = iq.get_queue_status()
        assert status["pending_count"] == 2
        assert len(status["pending_jobs"]) == 2
        assert status["current_job"] is None

    def test_cancel_job_cambia_estado_a_cancelled(self):
        import core.image_queue as iq
        job_id = iq.add_job("cancelar esto")
        result = iq.cancel_job(job_id)
        assert result is True
        status = iq.get_queue_status()
        assert status["pending_count"] == 0
        # El trabajo debe estar en historial como cancelled
        assert any(j["status"] == "cancelled" for j in status["history"])

    def test_cancel_job_inexistente_retorna_false(self):
        import core.image_queue as iq
        result = iq.cancel_job(99999)
        assert result is False

    def test_queue_status_sin_trabajos(self):
        import core.image_queue as iq
        status = iq.get_queue_status()
        assert status["pending_count"] == 0
        assert status["pending_jobs"] == []
        assert status["history"] == []

    def test_add_job_valores_por_defecto(self):
        import core.image_queue as iq
        import sqlite3
        job_id = iq.add_job("test default values")
        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row["performance"] == "Speed"
        assert row["width"] == 1024
        assert row["height"] == 1024
        assert row["status"] == "pending"

    def test_add_job_valores_custom(self):
        import core.image_queue as iq
        import sqlite3
        job_id = iq.add_job("custom", performance="Quality", width=512, height=768)
        conn = sqlite3.connect(iq.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM image_jobs WHERE id=?", (job_id,)).fetchone()
        conn.close()
        assert row["performance"] == "Quality"
        assert row["width"] == 512
        assert row["height"] == 768


# ══════════════════════════════════════════════════════════════════════
# SECURITY MONITOR
# ══════════════════════════════════════════════════════════════════════

class TestSecurityMonitor:
    """Tests para core/security_monitor.py — SHA-256, alertas, estado."""

    def test_sha256_archivo_real(self, tmp_path):
        from core.security_monitor import _sha256
        f = tmp_path / "test.txt"
        f.write_bytes(b"GravityAI")
        result = _sha256(str(f))
        expected = hashlib.sha256(b"GravityAI").hexdigest()
        assert result == expected

    def test_sha256_archivo_inexistente_retorna_none(self):
        from core.security_monitor import _sha256
        result = _sha256("/ruta/que/no/existe/archivo.py")
        assert result is None

    def test_get_state_retorna_dict_con_claves_esperadas(self):
        from core.security_monitor import get_state
        state = get_state()
        for key in ("last_scan", "status", "alerts", "processes",
                    "open_ports", "suspicious_ports", "file_integrity"):
            assert key in state

    def test_record_alert_agrega_a_estado(self):
        from core.security_monitor import _record_alert, _state, _lock
        with _lock:
            _state["alerts"].clear()
        _record_alert("INFO", "Test de alerta unitario")
        with _lock:
            alerts = list(_state["alerts"])
        assert any(a["message"] == "Test de alerta unitario" for a in alerts)

    def test_record_alert_nivel_critico(self):
        from core.security_monitor import _record_alert, _state, _lock
        _record_alert("CRITICAL", "Modificación detectada en core")
        with _lock:
            alerts = list(_state["alerts"])
        critical = [a for a in alerts if a["level"] == "CRITICAL"]
        assert len(critical) >= 1

    def test_alertas_limitadas_a_100(self):
        from core.security_monitor import _record_alert, _state, _lock
        with _lock:
            _state["alerts"].clear()
        for i in range(110):
            _record_alert("INFO", f"Alerta {i}")
        with _lock:
            count = len(_state["alerts"])
        assert count <= 100

    def test_scan_file_integrity_establece_baseline(self, tmp_path, monkeypatch):
        """_scan_file_integrity debe generar el baseline en la primera ejecución."""
        from core import security_monitor as sm
        f = tmp_path / "core_file.py"
        f.write_bytes(b"contenido critico")
        monkeypatch.setattr(sm, "CRITICAL_FILES", [str(f)])
        monkeypatch.setattr(sm, "_baseline_hashes", {})
        result = sm._scan_file_integrity()
        assert "core_file.py" in result
        assert result["core_file.py"]["status"] == "baseline_set"

    def test_scan_file_integrity_detecta_modificacion(self, tmp_path, monkeypatch):
        """Debe detectar cambio en archivo crítico vs baseline."""
        from core import security_monitor as sm
        f = tmp_path / "monitored.py"
        f.write_bytes(b"version original")
        path_str = str(f)
        monkeypatch.setattr(sm, "CRITICAL_FILES", [path_str])
        monkeypatch.setattr(sm, "_baseline_hashes", {
            path_str: hashlib.sha256(b"version diferente al actual").hexdigest()
        })
        result = sm._scan_file_integrity()
        assert result["monitored.py"]["status"] == "MODIFIED"

    def test_scan_file_integrity_ok_si_sin_cambios(self, tmp_path, monkeypatch):
        """Debe retornar ok si el hash no cambió."""
        from core import security_monitor as sm
        f = tmp_path / "stable.py"
        contenido = b"sin cambios"
        f.write_bytes(contenido)
        path_str = str(f)
        correct_hash = hashlib.sha256(contenido).hexdigest()
        monkeypatch.setattr(sm, "CRITICAL_FILES", [path_str])
        monkeypatch.setattr(sm, "_baseline_hashes", {path_str: correct_hash})
        result = sm._scan_file_integrity()
        assert result["stable.py"]["status"] == "ok"

    def test_force_scan_retorna_estado_actualizado(self):
        from core.security_monitor import force_scan
        state = force_scan()
        assert "last_scan" in state
        assert state["last_scan"] is not None
        assert state["status"] in ("ok", "warning", "error")


# ══════════════════════════════════════════════════════════════════════
# ENGINE WATCHDOG
# ══════════════════════════════════════════════════════════════════════

class TestEngineWatchdog:
    """Tests para core/engine_watchdog.py — estado, callbacks, lock."""

    @pytest.fixture(autouse=True)
    def reset_watchdog_state(self, monkeypatch):
        """Resetear el estado global del watchdog antes de cada test."""
        import core.engine_watchdog as ew
        monkeypatch.setattr(ew, "_current_provider_name", None)
        monkeypatch.setattr(ew, "_current_model", None)
        monkeypatch.setattr(ew, "_current_url", None)
        monkeypatch.setattr(ew, "_current_protocol", None)
        monkeypatch.setattr(ew, "_current_api_opts", {})
        monkeypatch.setattr(ew, "_hardware_profile", None)
        monkeypatch.setattr(ew, "_on_switch_callbacks", [])
        monkeypatch.setattr(ew, "_started", False)

    def test_get_active_state_inicial_retorna_nulos(self):
        from core.engine_watchdog import get_active_state
        state = get_active_state()
        assert state["provider"] is None
        assert state["model"] is None
        assert state["hardware"] == {}

    def test_get_active_state_refleja_valores_seteados(self, monkeypatch):
        import core.engine_watchdog as ew
        monkeypatch.setattr(ew, "_current_provider_name", "ollama")
        monkeypatch.setattr(ew, "_current_model", "llama3")
        monkeypatch.setattr(ew, "_current_url", "http://localhost:11434")
        state = ew.get_active_state()
        assert state["provider"] == "ollama"
        assert state["model"] == "llama3"

    def test_get_optimized_options_sin_base(self, monkeypatch):
        import core.engine_watchdog as ew
        monkeypatch.setattr(ew, "_current_api_opts", {"num_ctx": 4096, "temperature": 0.7})
        result = ew.get_optimized_options()
        assert result["num_ctx"] == 4096

    def test_get_optimized_options_merge_con_base(self, monkeypatch):
        import core.engine_watchdog as ew
        monkeypatch.setattr(ew, "_current_api_opts", {"num_ctx": 4096})
        result = ew.get_optimized_options(base_opts={"temperature": 0.5})
        assert result["num_ctx"] == 4096
        assert result["temperature"] == 0.5

    def test_get_optimized_options_base_sobreescribe(self, monkeypatch):
        """Los parámetros base tienen prioridad sobre los del watchdog."""
        import core.engine_watchdog as ew
        monkeypatch.setattr(ew, "_current_api_opts", {"num_ctx": 4096})
        result = ew.get_optimized_options(base_opts={"num_ctx": 2048})
        assert result["num_ctx"] == 2048

    def test_on_provider_switch_registra_callback(self, monkeypatch):
        import core.engine_watchdog as ew
        callbacks = []
        monkeypatch.setattr(ew, "_on_switch_callbacks", callbacks)
        cb = MagicMock()
        ew.on_provider_switch(cb)
        assert cb in callbacks

    def test_persist_settings_escribe_json(self, tmp_path, monkeypatch):
        import core.engine_watchdog as ew
        settings_file = tmp_path / "_settings.json"
        monkeypatch.setattr(ew, "SETTINGS_FILE", str(settings_file))
        monkeypatch.setattr(ew, "_started", False)

        prov = MagicMock()
        prov.name = "ollama"
        prov.protocol = "ollama"
        prov.url = "http://localhost:11434"
        ew._persist_settings(prov, "llama3", {"num_ctx": 4096})

        data = json.loads(settings_file.read_text())
        assert data["provider"] == "ollama"
        assert data["last_model"] == "llama3"

    def test_started_previene_doble_arranque(self, tmp_path, monkeypatch):
        """start() no debe lanzar segundo hilo si ya está iniciado."""
        import core.engine_watchdog as ew
        settings_file = tmp_path / "_settings.json"
        settings_file.write_text("{}")
        monkeypatch.setattr(ew, "SETTINGS_FILE", str(settings_file))
        monkeypatch.setattr(ew, "_started", True)

        with patch("core.engine_watchdog.threading.Thread") as mock_thread:
            result = ew.start()
            mock_thread.assert_not_called()
        assert result is None


# ══════════════════════════════════════════════════════════════════════
# GAME SERVER MANAGER
# ══════════════════════════════════════════════════════════════════════

class TestGameServerManager:
    """Tests para core/game_server_manager.py — sin depender de MySQL ni procesos reales."""

    @pytest.fixture(autouse=True)
    def reset_gsm_state(self, monkeypatch):
        import core.game_server_manager as gsm
        import core.log_buffer as lb
        monkeypatch.setattr(gsm, "_processes", {})
        monkeypatch.setattr(gsm, "_started", False)
        monkeypatch.setattr(gsm, "_watchdog_threads", {})
        monkeypatch.setattr(lb, "_buffers", {})

    def test_is_running_None_retorna_false(self):
        from core.game_server_manager import _is_running
        assert _is_running(None) is False

    def test_is_running_proceso_muerto(self):
        from core.game_server_manager import _is_running
        proc = MagicMock()
        proc.poll.return_value = 0  # código de salida — proceso terminado
        assert _is_running(proc) is False

    def test_is_running_proceso_vivo(self):
        from core.game_server_manager import _is_running
        proc = MagicMock()
        proc.poll.return_value = None  # None = sigue corriendo
        assert _is_running(proc) is True

    def test_tail_log_archivo_inexistente(self):
        from core.game_server_manager import _tail_log
        result = _tail_log("/ruta/falsa/mangosd.log")
        assert len(result) == 1
        assert "no encontrado" in result[0]

    def test_tail_log_retorna_ultimas_n_lineas(self, tmp_path):
        from core.game_server_manager import _tail_log
        log_f = tmp_path / "server.log"
        log_f.write_text("\n".join(f"linea {i}" for i in range(50)))
        result = _tail_log(str(log_f), lines=10)
        assert len(result) == 10
        assert result[-1] == "linea 49"

    def test_get_all_status_servidor_no_iniciado(self, monkeypatch):
        """Servidor configurado pero no iniciado debe aparecer como stopped."""
        from core import game_server_manager as gsm
        fake_config = {"wow_vanilla": {
            "display_name": "WoW Test",
            "auto_restart": True,
        }}
        monkeypatch.setattr(gsm, "_load_config", lambda: fake_config)
        result = gsm.get_all_status()
        assert "wow_vanilla" in result["servers"]
        assert result["servers"]["wow_vanilla"]["status"] == "stopped"
        assert result["servers"]["wow_vanilla"]["world_alive"] is False

    def test_start_servidor_inexistente_retorna_error(self, monkeypatch):
        from core import game_server_manager as gsm
        monkeypatch.setattr(gsm, "_load_config", lambda: {})
        result = gsm.start("servidor_que_no_existe")
        assert result["ok"] is False
        assert "no existe" in result["error"]

    def test_stop_servidor_no_iniciado_retorna_error(self, monkeypatch):
        from core import game_server_manager as gsm
        result = gsm.stop("wow_vanilla")
        assert result["ok"] is False

    def test_send_command_retorna_instruccion_soap(self):
        from core.game_server_manager import send_command
        result = send_command("wow_vanilla", ".server info")
        assert result["ok"] is False
        assert "SOAP" in result["note"]
        assert result["command"] == ".server info"

    def test_get_log_sem_buffer_usa_archivo(self, tmp_path, monkeypatch):
        from core import game_server_manager as gsm
        log_f = tmp_path / "mangosd.log"
        log_f.write_text("linea test\n")
        fake_config = {"wow_vanilla": {"log_file": str(log_f)}}
        monkeypatch.setattr(gsm, "_load_config", lambda: fake_config)
        result = gsm.get_log("wow_vanilla", lines=5)
        assert result["source"] == "file"
        assert "linea test" in result["lines"]

    def test_get_log_con_buffer_usa_memoria(self, monkeypatch):
        from core import game_server_manager as gsm
        from collections import deque
        import core.log_buffer as lb
        buf = deque(["[WORLD] Server starts", "[WORLD] DB OK"], maxlen=500)
        monkeypatch.setattr(lb, "_buffers", {"wow_vanilla": buf})
        result = gsm.get_log("wow_vanilla", lines=5)
        assert result["source"] == "memory_buffer"
        assert "[WORLD] DB OK" in result["lines"]

    def test_public_state_sin_procesos_activos(self):
        from core.game_server_manager import _public_state
        state = {
            "status": "stopped", "display_name": "Test WoW",
            "started_at": None, "stopped_at": None,
            "_world_proc": None, "_realm_proc": None,
            "errors": [], "cfg": {"auto_restart": True}
        }
        result = _public_state(state)
        assert result["world_alive"] is False
        assert result["realm_alive"] is False
        assert result["status"] == "stopped"

    def test_now_retorna_string_iso(self):
        from core.game_server_manager import _now
        result = _now()
        assert result.endswith("Z")
        assert "T" in result


# ══════════════════════════════════════════════════════════════════════
# MIXIN POST (Ruta LLM principal)
# ══════════════════════════════════════════════════════════════════════

class TestMixinPost:
    """Tests para api/routes/mixin_post.py — simulando el handler HTTP."""

    def _make_handler(self, path="/v1/chat/completions", body=None, headers=None):
        """Crea un mock del handler HTTP con los atributos mínimos necesarios."""
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

        # _send_cors no hace nada en tests
        handler._send_cors = MagicMock()
        return handler

    def test_do_POST_ruta_desconocida_retorna_404(self):
        """Rutas no registradas deben devolver 404."""
        from api.routes.mixin_post import PostRoutesMixin

        handler = self._make_handler(path="/ruta/inexistente")
        mixin = PostRoutesMixin()

        with patch.object(PostRoutesMixin, "do_POST", wraps=PostRoutesMixin.do_POST):
            # Inyectar método en handler mock
            handler.__class__ = type("TestHandler", (PostRoutesMixin,), {})
            PostRoutesMixin.do_POST(handler)

        handler.send_response.assert_called_with(404)

    def test_do_POST_fabricaweb_deploy_inicia_thread(self):
        """POST /v1/fabricaweb/deploy debe activar el pipeline en background."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(path="/v1/fabricaweb/deploy", body={"project_path": "my_project"})

        with patch("api.routes.mixin_post.deploy_manager") as mock_deploy:
            mock_deploy.start_deploy.return_value = {"started": True}
            PostRoutesMixin.do_POST(handler)

        mock_deploy.start_deploy.assert_called_once_with("my_project")
        handler.send_response.assert_called_with(200)

    def test_do_POST_queue_add_sin_prompt_retorna_400(self):
        """POST /v1/queue/add sin prompt debe retornar 400."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(path="/v1/queue/add", body={})

        with patch("api.routes.mixin_post.image_queue"):
            PostRoutesMixin.do_POST(handler)

        handler.send_response.assert_called_with(400)

    def test_do_POST_queue_add_con_prompt_encola_trabajo(self):
        """POST /v1/queue/add con prompt válido debe encolar y retornar job_id."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(
            path="/v1/queue/add",
            body={"prompt": "un dragón sobre las montañas"}
        )

        with patch("api.routes.mixin_post.image_queue") as mock_iq:
            mock_iq.add_job.return_value = 42
            PostRoutesMixin.do_POST(handler)

        mock_iq.add_job.assert_called_once()
        handler.send_response.assert_called_with(200)

    def test_do_POST_security_scan_llama_force_scan(self):
        """POST /v1/security/scan debe invocar security_monitor.force_scan()."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(path="/v1/security/scan", body={})

        with patch("api.routes.mixin_post.security_monitor") as mock_sm:
            mock_sm.force_scan.return_value = {"status": "ok", "last_scan": "2026-04-20T00:00:00Z"}
            PostRoutesMixin.do_POST(handler)

        mock_sm.force_scan.assert_called_once()
        handler.send_response.assert_called_with(200)

    def test_do_POST_gameserver_start_llama_start(self):
        """POST /v1/gameserver/start debe llamar game_server_manager.start()."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(
            path="/v1/gameserver/start",
            body={"server": "wow_vanilla"}
        )

        with patch("api.routes.handlers.gameserver_handler.game_server_manager") as mock_gsm:
            mock_gsm.start.return_value = {"ok": True, "status": "running"}
            PostRoutesMixin.do_POST(handler)

        mock_gsm.start.assert_called_once_with("wow_vanilla")

    def test_do_POST_gameserver_stop_llama_stop(self):
        """POST /v1/gameserver/stop debe llamar game_server_manager.stop()."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(
            path="/v1/gameserver/stop",
            body={"server": "wow_vanilla"}
        )

        with patch("api.routes.handlers.gameserver_handler.game_server_manager") as mock_gsm:
            mock_gsm.stop.return_value = {"ok": True, "status": "stopped"}
            PostRoutesMixin.do_POST(handler)

        mock_gsm.stop.assert_called_once_with("wow_vanilla")

    def test_do_POST_completions_sin_provider_retorna_503(self):
        """Si no hay proveedor disponible debe retornar 503."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(
            path="/v1/chat/completions",
            body={"messages": [{"role": "user", "content": "hola"}]},
            headers={"Authorization": ""}
        )

        with patch("api.routes.mixin_post.check_access", return_value=(True, "ok")), \
             patch("api.routes.mixin_post.provider_manager") as mock_pm, \
             patch("api.routes.mixin_post.record_error"):
            mock_pm.get_best.return_value = (None, None)
            mock_pm.scan_all.return_value = []
            PostRoutesMixin.do_POST(handler)

        handler.send_response.assert_called_with(503)

    def test_do_POST_completions_rate_limited_retorna_429(self):
        """Si el rate limiter bloquea, debe retornar 429."""
        from api.routes.mixin_post import PostRoutesMixin
        handler = self._make_handler(
            path="/v1/chat/completions",
            body={"messages": [{"role": "user", "content": "hola"}]},
        )

        with patch("api.routes.mixin_post.check_access",
                   return_value=(False, "rate limit exceeded")), \
             patch("api.routes.mixin_post.record_error"):
            PostRoutesMixin.do_POST(handler)

        handler.send_response.assert_called_with(429)
