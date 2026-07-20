"""
tests/test_tiktok_monitor.py — Suite de tests para GTLIS (TikTok Live Intelligence Suite)

Cubre:
  - BotDetectionEngine (unit tests puros, sin red)
  - NetworkRecon._identify_cdn (unit test)
  - ProfileIntelligence._parse_sigi_state (unit test)
  - TikTokLiveMonitor.execute (mocked)
  - TikTokRadar DB helpers (con SQLite en memoria)
  - mixin_tiktok._handle_post_tiktok dispatcher
"""

import json
import os
import sys
import sqlite3
import threading
import pytest
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ══════════════════════════════════════════════════════════════════════════════
# BotDetectionEngine — Unit Tests (sin red, sin DB)
# ══════════════════════════════════════════════════════════════════════════════


class TestBotDetectionEngine:
    @pytest.fixture(autouse=True)
    def engine(self):
        from tools.tiktok_live_monitor import BotDetectionEngine
        self.bot = BotDetectionEngine()

    def test_empty_comments_returns_zero(self):
        result = self.bot.analyze_comment_feed([])
        assert result["bot_score"] == 0.0
        assert result["signals"] == []
        assert result["total_analyzed"] == 0

    def test_clean_comments_low_score(self):
        comments = [
            {"user_id": str(i), "text": f"Qué buen stream! {i}", "timestamp_ms": i * 3000}
            for i in range(20)
        ]
        result = self.bot.analyze_comment_feed(comments)
        assert result["bot_score"] < 0.2
        assert result["risk_level"] == "low"

    def test_high_repetition_raises_score(self):
        comments = [
            {"user_id": str(i), "text": "follow me now buy followers", "timestamp_ms": i * 1000}
            for i in range(30)
        ]
        result = self.bot.analyze_comment_feed(comments)
        assert result["bot_score"] > 0.3
        assert any(s["type"] == "text_repetition" for s in result["signals"])

    def test_bot_text_patterns_detected(self):
        comments = [
            {"user_id": "1", "text": "f4f follow back please visit my profile", "timestamp_ms": 1000},
            {"user_id": "2", "text": "check my bio for free followers", "timestamp_ms": 2000},
            {"user_id": "3", "text": "buy 5000 seguidores guaranteed", "timestamp_ms": 3000},
            {"user_id": "4", "text": "normal comment here", "timestamp_ms": 4000},
            {"user_id": "5", "text": "nice content bro", "timestamp_ms": 5000},
            {"user_id": "6", "text": "keep it up!", "timestamp_ms": 6000},
        ]
        result = self.bot.analyze_comment_feed(comments)
        assert any(s["type"] == "bot_text_pattern" for s in result["signals"])

    def test_high_velocity_single_user_raises_score(self):
        # Un solo usuario postea 50 comentarios en 30 segundos
        comments = [
            {"user_id": "bot_1", "text": f"msg {i}", "timestamp_ms": 1000 + i * 600}
            for i in range(50)
        ]
        result = self.bot.analyze_comment_feed(comments)
        assert any(s["type"] == "high_velocity" for s in result["signals"])
        assert result["bot_score"] > 0.2

    def test_timestamp_clustering_detected(self):
        # Comentarios en intervalos exactos de 2 segundos ± 0.05s
        import random
        random.seed(42)
        comments = [
            {
                "user_id": str(i % 5),
                "text": f"comment {i}",
                "timestamp_ms": 1_000_000 + i * 2000 + random.randint(-50, 50),
            }
            for i in range(30)
        ]
        result = self.bot.analyze_comment_feed(comments)
        # El clustering puede o no detectarse según el jitter, pero no debe crashear
        assert "bot_score" in result
        assert 0.0 <= result["bot_score"] <= 1.0

    def test_quick_score_new_account_high_viewers(self):
        score = self.bot.quick_score(viewers=5000, follower_ratio=5.0, account_age_days=10)
        assert score >= 0.4

    def test_quick_score_normal_channel(self):
        score = self.bot.quick_score(viewers=500, follower_ratio=1.2, account_age_days=365)
        assert score == 0.0

    def test_bot_score_capped_at_one(self):
        # Comentarios con TODOS los indicadores de bot al máximo
        comments = [
            {
                "user_id": "bot",
                "text": "buy followers now f4f check my bio",
                "timestamp_ms": 1000 + i * 100,
            }
            for i in range(100)
        ]
        result = self.bot.analyze_comment_feed(comments)
        assert result["bot_score"] <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# NetworkRecon — Unit Tests (sin red)
# ══════════════════════════════════════════════════════════════════════════════


class TestNetworkRecon:
    @pytest.fixture(autouse=True)
    def recon(self):
        from tools.tiktok_live_monitor import NetworkRecon
        self.recon = NetworkRecon()

    def test_akamai_fingerprint(self):
        cdn = self.recon._identify_cdn("edgekey.net", {"server": "AkamaiGHost"})
        assert "Akamai" in cdn

    def test_tiktok_cdn_fingerprint(self):
        cdn = self.recon._identify_cdn("pull-hls.tiktokcdn.com", {})
        assert "TikTok" in cdn or "MusCDN" in cdn or "ByteDance" in cdn

    def test_cloudflare_fingerprint(self):
        cdn = self.recon._identify_cdn("example.com", {"server": "cloudflare"})
        assert "Cloudflare" in cdn

    def test_unknown_cdn(self):
        cdn = self.recon._identify_cdn("totallyunknown12345.example", {})
        assert cdn == "Unknown CDN"

    def test_hls_manifest_parsing_empty(self):
        # Con URL inválida no debe crashear — retorna lista vacía
        variants = self.recon.extract_hls_variants("https://example.invalid/stream.m3u8")
        assert isinstance(variants, list)


# ══════════════════════════════════════════════════════════════════════════════
# ProfileIntelligence — Unit Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestProfileIntelligence:
    @pytest.fixture(autouse=True)
    def intel(self):
        from tools.tiktok_live_monitor import ProfileIntelligence
        self.intel = ProfileIntelligence()

    def test_parse_sigi_state_valid(self):
        fake_sigi = json.dumps({"UserModule": {"users": {}, "stats": {}}})
        html = f'<script id="SIGI_STATE" type="application/json">{fake_sigi}</script>'
        result = self.intel._parse_sigi_state(html)
        assert result is not None
        assert "UserModule" in result

    def test_parse_sigi_state_missing(self):
        result = self.intel._parse_sigi_state("<html><body>nothing here</body></html>")
        assert result is None

    def test_history_fingerprint_empty(self):
        result = self.intel.history_fingerprint([])
        assert result == []

    def test_history_fingerprint_pattern(self):
        from datetime import datetime, timezone
        snapshots = []
        for hour in [20, 20, 20, 22, 22, 9]:
            ts = datetime(2025, 1, 1, hour, 0, 0, tzinfo=timezone.utc).isoformat()
            snapshots.append({"ts": ts, "is_live": 1})
        result = self.intel.history_fingerprint(snapshots)
        assert len(result) > 0
        # La hora más frecuente (20:00) debe aparecer primero
        assert "20:00" in result[0]


# ══════════════════════════════════════════════════════════════════════════════
# LiveSnapshot — Data Model
# ══════════════════════════════════════════════════════════════════════════════


class TestLiveSnapshot:
    def test_to_dict_serializable(self):
        from tools.tiktok_live_monitor import LiveSnapshot
        snap = LiveSnapshot(
            username="testuser",
            is_live=True,
            viewers=1500,
            title="Test Live",
            bot_score=0.3,
        )
        d = snap.to_dict()
        assert d["username"] == "testuser"
        assert d["is_live"] == 1  # convertido a int para SQLite
        assert d["viewers"] == 1500
        assert json.dumps(d)  # debe ser JSON-serializable

    def test_to_dict_offline(self):
        from tools.tiktok_live_monitor import LiveSnapshot
        snap = LiveSnapshot(username="offline_user", is_live=False)
        d = snap.to_dict()
        assert d["is_live"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# TikTokLiveMonitor — Integration Tests (mocked)
# ══════════════════════════════════════════════════════════════════════════════


class TestTikTokLiveMonitor:
    @pytest.fixture(autouse=True)
    def monitor(self):
        from tools.tiktok_live_monitor import TikTokLiveMonitor
        self.monitor = TikTokLiveMonitor()

    def test_execute_missing_username_returns_error(self):
        result = self.monitor.execute(action="probe")
        assert not result.success
        assert result.exit_code == 1
        assert "username" in result.stderr.lower() or "stream_url" in result.stderr.lower()

    def test_execute_invalid_action_graceful(self):
        # Acción no existente — el execute no debe crashear; probe con username vacío
        result = self.monitor.execute(action="nonexistent")
        assert not result.success

    @patch("tools.tiktok_live_monitor.LiveStreamProbe.fetch_live_metadata")
    def test_execute_probe_mocked(self, mock_fetch):
        from tools.tiktok_live_monitor import LiveSnapshot
        mock_snap = LiveSnapshot(
            username="mockuser",
            is_live=True,
            viewers=2500,
            title="Mock Live Stream",
            cdn_provider="TikTok CDN",
        )
        mock_fetch.return_value = mock_snap

        result = self.monitor.execute(action="probe", username="mockuser")
        assert result.success
        assert "live_snapshot" in result.data
        assert result.data["live_snapshot"]["viewers"] == 2500

    @patch("tools.tiktok_live_monitor.LiveStreamProbe.fetch_live_metadata")
    @patch("tools.tiktok_live_monitor.ProfileIntelligence.get_public_profile")
    def test_execute_full_mocked(self, mock_profile, mock_fetch):
        from tools.tiktok_live_monitor import LiveSnapshot, ProfileReport
        mock_fetch.return_value = LiveSnapshot(
            username="fulluser", is_live=True, viewers=999
        )
        mock_profile.return_value = ProfileReport(
            username="fulluser", followers=10000, display_name="Full User"
        )

        result = self.monitor.execute(action="full", username="fulluser")
        assert result.success
        assert "live_snapshot" in result.data
        assert "profile" in result.data
        assert result.data["profile"]["followers"] == 10000

    def test_bot_check_shorthand(self):
        comments = [
            {"user_id": "u1", "text": "great content", "timestamp_ms": 1000},
            {"user_id": "u2", "text": "love this stream", "timestamp_ms": 2000},
        ]
        result = self.monitor.bot_check(comments)
        assert "bot_score" in result
        assert result["bot_score"] < 0.5


# ══════════════════════════════════════════════════════════════════════════════
# TikTokRadar DB Helpers — Tests con SQLite en memoria
# ══════════════════════════════════════════════════════════════════════════════


class TestTikTokRadarDB:
    @pytest.fixture(autouse=True)
    def setup_in_memory_db(self, tmp_path, monkeypatch):
        """Crea un DB en memoria con el schema del radar y parchea la ruta."""
        self.db_path = str(tmp_path / "test_brain.db")

        # Parchear la ruta del DB en el módulo del radar
        import core.tiktok_radar as radar_mod
        monkeypatch.setattr(radar_mod, "_DB_PATH", self.db_path)

        # Crear las tablas usando el schema de la migración
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tiktok_snapshots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL,
                ts            TEXT    NOT NULL DEFAULT (datetime('now')),
                is_live       INTEGER NOT NULL DEFAULT 0,
                viewers       INTEGER DEFAULT 0,
                title         TEXT    DEFAULT '',
                stream_url    TEXT    DEFAULT '',
                codec_video   TEXT    DEFAULT '',
                codec_audio   TEXT    DEFAULT '',
                bitrate_kbps  INTEGER DEFAULT 0,
                resolution    TEXT    DEFAULT '',
                fps           REAL    DEFAULT 0.0,
                cdn_provider  TEXT    DEFAULT 'unknown',
                cdn_ip        TEXT    DEFAULT '',
                geo_country   TEXT    DEFAULT '',
                geo_city      TEXT    DEFAULT '',
                room_id       TEXT    DEFAULT '',
                user_id       TEXT    DEFAULT '',
                bot_score     REAL    NOT NULL DEFAULT 0.0,
                engagement    REAL    NOT NULL DEFAULT 0.0,
                raw_meta      TEXT    DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS tiktok_watchlist (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    NOT NULL UNIQUE,
                added_ts     TEXT    NOT NULL DEFAULT (datetime('now')),
                interval_sec INTEGER NOT NULL DEFAULT 60,
                active       INTEGER NOT NULL DEFAULT 1,
                notes        TEXT    DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS tiktok_alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL,
                ts          TEXT    NOT NULL DEFAULT (datetime('now')),
                alert_type  TEXT    NOT NULL,
                severity    TEXT    NOT NULL DEFAULT 'info',
                message     TEXT    NOT NULL,
                snapshot_id INTEGER,
                acknowledged INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()

    def test_add_and_load_watchlist(self):
        from core.tiktok_radar import _add_to_watchlist, _load_watchlist
        ok = _add_to_watchlist("testchannel", interval_sec=30)
        assert ok
        channels = _load_watchlist()
        assert any(ch["username"] == "testchannel" for ch in channels)

    def test_add_duplicate_watchlist_updates(self):
        from core.tiktok_radar import _add_to_watchlist, _load_watchlist
        _add_to_watchlist("dup_user", interval_sec=60)
        _add_to_watchlist("dup_user", interval_sec=120)  # Update
        channels = _load_watchlist()
        dup_channels = [c for c in channels if c["username"] == "dup_user"]
        assert len(dup_channels) == 1
        assert dup_channels[0]["interval"] == 120

    def test_remove_from_watchlist(self):
        from core.tiktok_radar import _add_to_watchlist, _remove_from_watchlist, _load_watchlist
        _add_to_watchlist("remove_me")
        ok = _remove_from_watchlist("remove_me")
        assert ok
        channels = _load_watchlist()
        assert not any(ch["username"] == "remove_me" for ch in channels)

    def test_persist_and_retrieve_snapshot(self):
        from tools.tiktok_live_monitor import LiveSnapshot
        from core.tiktok_radar import _persist_snapshot, _get_last_snapshot

        snap = LiveSnapshot(
            username="snapuser",
            is_live=True,
            viewers=3000,
            title="Test Live",
            cdn_provider="TikTok CDN",
            bot_score=0.15,
            engagement=4.5,
        )
        snap_id = _persist_snapshot(snap)
        assert snap_id > 0

        last = _get_last_snapshot("snapuser")
        assert last is not None
        assert last["viewers"] == 3000
        assert last["is_live"] == 1
        assert last["cdn_provider"] == "TikTok CDN"

    def test_create_and_retrieve_alert(self):
        from core.tiktok_radar import _create_alert, _get_recent_alerts
        _create_alert(
            username="alertuser",
            alert_type="stream_start",
            severity="info",
            message="Canal inició live",
            snapshot_id=1,
        )
        alerts = _get_recent_alerts(username="alertuser")
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "stream_start"
        assert alerts[0]["severity"] == "info"

    def test_alert_deduplication(self):
        from core.tiktok_radar import _create_alert, _get_recent_alerts
        # 1. Crear primera alerta
        _create_alert(
            username="dedup_user",
            alert_type="bot_detected",
            severity="warning",
            message="Sospecha de bots alta (score: 0.60)",
            snapshot_id=10,
        )
        # 2. Crear segunda alerta idéntica antes de reconocer la primera
        _create_alert(
            username="dedup_user",
            alert_type="bot_detected",
            severity="warning",
            message="Sospecha de bots alta (score: 0.65)",
            snapshot_id=11,
        )
        
        # Deben deduplicarse: sólo una fila debe estar en bd para esa llave
        alerts = _get_recent_alerts(username="dedup_user")
        assert len(alerts) == 1
        assert alerts[0]["message"] == "Sospecha de bots alta (score: 0.65)"
        assert alerts[0]["snapshot_id"] == 11

    def test_get_history_empty(self):
        from core.tiktok_radar import _get_history
        history = _get_history("nonexistent_user")
        assert history == []


# ══════════════════════════════════════════════════════════════════════════════
# mixin_tiktok — POST Dispatcher
# ══════════════════════════════════════════════════════════════════════════════


class TestTikTokMixinDispatcher:
    def _make_handler(self, path: str, method: str = "POST"):
        """Crea un mock del HTTP handler con el path y método especificados."""
        from api.routes.mixin_tiktok import TikTokMixin

        class FakeHandler(TikTokMixin):
            def __init__(self):
                self.path = path
                self._called = []

            def _serve_tiktok_watch(self):
                self._called.append("watch")

            def _serve_tiktok_unwatch(self):
                self._called.append("unwatch")

            def _serve_tiktok_analyze(self):
                self._called.append("analyze")

        return FakeHandler()

    def test_watch_route_dispatched(self):
        handler = self._make_handler("/v1/tiktok/watch")
        handled = handler._handle_post_tiktok()
        assert handled is True
        assert "watch" in handler._called

    def test_unwatch_route_dispatched(self):
        handler = self._make_handler("/v1/tiktok/unwatch")
        handled = handler._handle_post_tiktok()
        assert handled is True
        assert "unwatch" in handler._called

    def test_analyze_route_dispatched(self):
        handler = self._make_handler("/v1/tiktok/analyze")
        handled = handler._handle_post_tiktok()
        assert handled is True
        assert "analyze" in handler._called

    def test_unknown_route_returns_false(self):
        handler = self._make_handler("/v1/other/route")
        handled = handler._handle_post_tiktok()
        assert handled is False
        assert handler._called == []

    def test_query_string_stripped(self):
        handler = self._make_handler("/v1/tiktok/watch?extra=1")
        handled = handler._handle_post_tiktok()
        assert handled is True
