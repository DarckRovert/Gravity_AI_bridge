"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — TIKTOK LIVE RADAR V1.0                                         ║
║  Daemon de monitoreo continuo de canales TikTok Live                         ║
║                                                                              ║
║  Patrón: extiende HighFrequencyRadar — un hilo por canal en watchlist        ║
║  Persiste snapshots en gravity_brain.db (tabla tiktok_snapshots)             ║
║  Genera alertas en tiempo real (tabla tiktok_alerts)                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from collections import deque
import os
import sys
import json
import time
import sqlite3
import threading
import concurrent.futures
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_CORE_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from core.logger import log
from tools.tiktok_live_monitor import get_monitor, LiveSnapshot
from core.tiktok_osint_engine import TikTokOSINTEngine
from core.tiktok_audio_transcriber import AudioTranscriber

# ── Constants ──────────────────────────────────────────────────────────────────
_LOCAL_APP_DATA = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")),
    "Gravity", "Databases",
)
os.makedirs(_LOCAL_APP_DATA, exist_ok=True)

_DB_PATH = os.path.join(_LOCAL_APP_DATA, "gravity_brain.db")

# Umbrales para generar alertas
VIEWER_SPIKE_MULTIPLIER = 2.5   # 2.5x viewers vs snapshot anterior = spike
BOT_SCORE_ALERT_THRESHOLD = 0.5  # bot_score > 0.5 → alerta
MIN_POLL_INTERVAL = 15           # segundos mínimos entre polls
MAX_WATCHED_CHANNELS = 50        # límite de canales en watchlist


# ── DB Helpers ────────────────────────────────────────────────────────────────

_thread_local = threading.local()

def _get_conn() -> sqlite3.Connection:
    """Abre y mantiene conexión a gravity_brain.db con WAL mode (thread-local)."""
    if not hasattr(_thread_local, "conn"):
        conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000") # 64MB cache
        conn.row_factory = sqlite3.Row
        _thread_local.conn = conn
    return _thread_local.conn


def _persist_snapshot(snap: LiveSnapshot, conn: Optional[sqlite3.Connection] = None) -> int:
    """Guarda un LiveSnapshot en tiktok_snapshots. Retorna el ID insertado."""
    if conn is None:
        conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO tiktok_snapshots
            (username, ts, is_live, viewers, title, stream_url,
             codec_video, codec_audio, bitrate_kbps, resolution, fps,
             cdn_provider, cdn_ip, geo_country, geo_city, room_id, user_id, bot_score, engagement, raw_meta)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                snap.username,
                snap.ts,
                1 if snap.is_live else 0,
                snap.viewers,
                snap.title,
                snap.stream_url,
                snap.codec_video,
                snap.codec_audio,
                snap.bitrate_kbps,
                snap.resolution,
                snap.fps,
                snap.cdn_provider,
                snap.cdn_ip,
                snap.geo_country,
                snap.geo_city,
                snap.room_id,
                snap.user_id,
                snap.bot_score,
                snap.engagement,
                json.dumps(snap.raw_meta, ensure_ascii=False),
            ),
        )
        conn.commit()
        return cur.lastrowid or 0
    except sqlite3.OperationalError as e:
        # Tabla no existe aún (migración pendiente) — loguear y continuar
        log.warning(f"[TikTokRadar·DB] Tabla no disponible aún: {e}")
        return 0


def _create_alert(
    username: str,
    alert_type: str,
    severity: str,
    message: str,
    snapshot_id: int = 0,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Registra una alerta en tiktok_alerts."""
    if conn is None:
        conn = _get_conn()
    try:
        # Buscar si ya existe una alerta no reconocida (activa) del mismo tipo para este canal
        prev = conn.execute(
            """
            SELECT id FROM tiktok_alerts
            WHERE username = ? AND alert_type = ? AND acknowledged = 0
            LIMIT 1
            """,
            (username, alert_type),
        ).fetchone()

        if prev:
            # Si existe, actualizamos su timestamp, mensaje y snapshot_id en lugar de duplicarla
            conn.execute(
                """
                UPDATE tiktok_alerts
                SET ts = datetime('now'), message = ?, snapshot_id = ?, severity = ?
                WHERE id = ?
                """,
                (message, snapshot_id, severity, prev["id"]),
            )
        else:
            # Si no existe, la creamos normalmente
            conn.execute(
                """
                INSERT INTO tiktok_alerts (username, alert_type, severity, message, snapshot_id)
                VALUES (?,?,?,?,?)
                """,
                (username, alert_type, severity, message, snapshot_id),
            )
        conn.commit()
    except sqlite3.OperationalError as e:
        log.warning(f"[TikTokRadar·DB] No se pudo procesar alerta: {e}")


def _load_watchlist() -> List[Dict[str, Any]]:
    """Carga los canales activos desde tiktok_watchlist."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT username, interval_sec FROM tiktok_watchlist WHERE active=1 LIMIT ?",
            (MAX_WATCHED_CHANNELS,),
        ).fetchall()
        return [{"username": r["username"], "interval": r["interval_sec"]} for r in rows]
    except sqlite3.OperationalError:
        return []


def _add_to_watchlist(username: str, interval_sec: int = 60, notes: str = "") -> bool:
    """Agrega un canal a la watchlist. Retorna True si fue insertado/actualizado."""
    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO tiktok_watchlist (username, interval_sec, notes, active)
            VALUES (?,?,?,1)
            ON CONFLICT(username) DO UPDATE SET active=1, interval_sec=excluded.interval_sec
            """,
            (username.lstrip("@"), interval_sec, notes),
        )
        conn.commit()
        return True
    except Exception as e:
        log.error(f"[TikTokRadar·DB] Error añadiendo a watchlist: {e}")
        return False


def _remove_from_watchlist(username: str) -> bool:
    """Desactiva un canal en la watchlist (soft delete)."""
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE tiktok_watchlist SET active=0 WHERE username=?",
            (username.lstrip("@"),),
        )
        conn.commit()
        return True
    except Exception as e:
        log.error(f"[TikTokRadar·DB] Error removiendo de watchlist: {e}")
        return False


def _get_last_snapshot(username: str) -> Optional[Dict[str, Any]]:
    """Retorna el snapshot más reciente de un canal."""
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT * FROM tiktok_snapshots
            WHERE username=?
            ORDER BY ts DESC LIMIT 1
            """,
            (username,),
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.OperationalError:
        return None


def _get_recent_alerts(username: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retorna las alertas más recientes, opcionalmente filtradas por canal."""
    try:
        conn = _get_conn()
        if username:
            rows = conn.execute(
                "SELECT * FROM tiktok_alerts WHERE username=? ORDER BY ts DESC LIMIT ?",
                (username, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tiktok_alerts ORDER BY ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


# ── History Helper ──────────────────────────────────────────────────────────────

def _get_history(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retorna el historial de snapshots de un canal."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            """
            SELECT id, ts, is_live, viewers, title, bot_score, engagement,
                   codec_video, resolution, cdn_provider, geo_country, geo_city, room_id, user_id
            FROM tiktok_snapshots
            WHERE username=?
            ORDER BY ts DESC LIMIT ?
            """,
            (username, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []


def _get_last_live_snapshot(username: str) -> Optional[Dict[str, Any]]:
    """Retorna el snapshot en vivo (is_live = 1) más reciente de un canal."""
    try:
        conn = _get_conn()
        row = conn.execute(
            """
            SELECT * FROM tiktok_snapshots
            WHERE username=? AND is_live=1
            ORDER BY ts DESC LIMIT 1
            """,
            (username.lstrip("@"),),
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.OperationalError:
        return None


class CommentCollector:
    """Recolecta comentarios de TikTok Live en segundo plano usando la biblioteca TikTokLive."""
    def __init__(self, username: str) -> None:
        self.username = username.lstrip("@")
        self.comments: deque = deque(maxlen=200)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.client: Optional[Any] = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"GTLISChat-{self.username}",
            daemon=True
        )
        self._thread.start()
        log.info(f"[TikTokRadar·Chat] 💬 Recolector de chat iniciado para @{self.username}")

    def stop(self) -> None:
        self.running = False
        if self.client:
            try:
                import asyncio
                if self.client.loop and self.client.loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.client.loop)
            except Exception as e:
                log.debug(f"[TikTokRadar·Chat] Error deteniendo cliente para @{self.username}: {e}")

    def _run_loop(self) -> None:
        import asyncio
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import CommentEvent

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.client = TikTokLiveClient(unique_id=self.username)

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent) -> None:
            if not self.running:
                return
            self.comments.append({
                "user_id": event.user.unique_id,
                "text": event.comment,
                "timestamp_ms": int(time.time() * 1000)
            })

        try:
            loop.run_until_complete(self.client.start())
        except Exception as e:
            log.warning(f"[TikTokRadar·Chat] Cliente chat finalizado para @{self.username}: {e}")
        finally:
            try:
                loop.run_until_complete(self.client.disconnect())
            except Exception:
                pass
            loop.close()
            log.info(f"[TikTokRadar·Chat] 💬 Recolector de chat detenido para @{self.username}")


# ── TikTokRadar Daemon ────────────────────────────────────────────────────────

class TikTokRadar:
    """
    Daemon principal del GTLIS.
    Gestiona la watchlist de canales usando un ThreadPoolExecutor escalable.
    
    Puede ser iniciado como servicio background vía service_loader de Gravity,
    o controlado dinámicamente por los endpoints REST del bridge_server.
    """

    def __init__(self) -> None:
        self._watchers: Dict[str, Dict[str, Any]] = {}
        self._chat_collectors: Dict[str, CommentCollector] = {}
        self._audio_transcribers: Dict[str, AudioTranscriber] = {}
        self._lock = threading.RLock()
        self._running = False
        self._supervisor_thread: Optional[threading.Thread] = None
        self._pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._monitor = get_monitor()

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia el radar: carga watchlist desde DB y arranca workers."""
        if self._running:
            return
        self._running = True
        self._pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=32, thread_name_prefix="GTLISPool"
        )

        # Cargar watchlist inicial
        self._sync_watchlist()

        # Supervisor central
        self._supervisor_thread = threading.Thread(
            target=self._supervisor_loop,
            name="GTLISSupervisor",
            daemon=True,
        )
        self._supervisor_thread.start()
        with self._lock:
            count = len(self._watchers)
        log.info(f"[TikTokRadar] ✅ Radar iniciado — {count} canal(es) en pool (max_workers=32)")

    def stop(self) -> None:
        """Detiene el radar gracefully."""
        self._running = False
        if self._pool:
            self._pool.shutdown(wait=False)
        with self._lock:
            for username, collector in list(self._chat_collectors.items()):
                try:
                    collector.stop()
                except Exception as e:
                    log.debug(f"[TikTokRadar] Error deteniendo collector para {username}: {e}")
            self._chat_collectors.clear()
            for username, transcriber in list(self._audio_transcribers.items()):
                try:
                    transcriber.stop()
                except Exception as e:
                    log.debug(f"[TikTokRadar] Error deteniendo audio transcriber para {username}: {e}")
            self._audio_transcribers.clear()
            self._watchers.clear()
        log.info("[TikTokRadar] ■ Radar detenido")

    def _supervisor_loop(self) -> None:
        """Loop principal: asigna tareas de polling si pasó el intervalo, y sincroniza DB."""
        last_sync = 0.0
        while self._running:
            now = time.time()
            
            # Sincronización con la DB cada 60s
            if now - last_sync > 60:
                try:
                    self._sync_watchlist()
                    last_sync = now
                except Exception as exc:
                    log.error(f"[TikTokRadar·Supervisor] Error sync: {exc}")
            
            # Polling dispatcher
            with self._lock:
                for username, state in list(self._watchers.items()):
                    if not self._running: break
                    if state.get("is_polling", False):
                        continue
                    
                    interval = state["interval"]
                    last_check = state["last_check"]
                    
                    if now - last_check >= interval:
                        state["is_polling"] = True
                        try:
                            self._pool.submit(self._tick, username, state)
                        except Exception as e:
                            state["is_polling"] = False
                            log.error(f"[TikTokRadar] Pool submit error para {username}: {e}")

            time.sleep(1)

    def _sync_watchlist(self) -> None:
        """Agrega/elimina canales del pool según la DB."""
        db_channels = {ch["username"]: ch["interval"] for ch in _load_watchlist()}
        with self._lock:
            # Añadir/Actualizar
            for username, interval in db_channels.items():
                if username not in self._watchers:
                    self._watchers[username] = {
                        "interval": max(interval, MIN_POLL_INTERVAL),
                        "last_check": 0.0,
                        "is_polling": False,
                        "was_live": False,
                        "last_viewers": 0,
                        "last_snapshot": None
                    }
                    log.info(f"[TikTokRadar] ▶ Monitoreando a @{username} (cada {interval}s)")
                else:
                    self._watchers[username]["interval"] = max(interval, MIN_POLL_INTERVAL)
            
            # Remover eliminados
            to_remove = [u for u in self._watchers if u not in db_channels]
            for username in to_remove:
                del self._watchers[username]
                log.info(f"[TikTokRadar] ■ Removido @{username}")

    def _tick(self, username: str, state_ref: Dict[str, Any]) -> None:
        """Trabajo de recolección para un canal ejecutado por el ThreadPool."""
        try:
            snap = self._monitor.probe(username)
            snap_id = _persist_snapshot(snap)
            self._detect_and_alert(username, snap, snap_id, state_ref)
            
            with self._lock:
                state_ref["was_live"] = snap.is_live
                if snap.is_live:
                    state_ref["last_viewers"] = snap.viewers
                    # Iniciar colector de chat si está en vivo y no existe
                    if username not in self._chat_collectors:
                        self._chat_collectors[username] = CommentCollector(username)
                        self._chat_collectors[username].start()
                    # Iniciar transcriptor de audio si hay stream_url disponible
                    log.info(f"[TikTokRadar·Debug] @{username} is_live=True. stream_url={bool(snap.stream_url)}, in_audio={username in self._audio_transcribers}")
                    if username not in self._audio_transcribers and snap.stream_url:
                        try:
                            transcriber = AudioTranscriber(username, snap.stream_url, model_size="base")
                            transcriber.start()
                            self._audio_transcribers[username] = transcriber
                        except Exception as ae:
                            log.warning(f"[TikTokRadar] No se pudo iniciar audio para @{username}: {ae}")
                else:
                    # Detener colector de chat si estaba corriendo
                    if username in self._chat_collectors:
                        self._chat_collectors[username].stop()
                        del self._chat_collectors[username]
                    # Detener transcriptor de audio
                    if username in self._audio_transcribers:
                        self._audio_transcribers[username].stop()
                        del self._audio_transcribers[username]
                state_ref["last_snapshot"] = snap
                
            status = "🔴 EN VIVO" if snap.is_live else "⚫ offline"
            vstr = f"| viewers={snap.viewers:,}" if snap.is_live else ""
            log.debug(f"[TikTokRadar·{username}] {status} {vstr} | bot={snap.bot_score:.2f}")
        except Exception as exc:
            log.error(f"[TikTokRadar·{username}] Error en tick: {exc}")
        finally:
            with self._lock:
                state_ref["last_check"] = time.time()
                state_ref["is_polling"] = False

    def _detect_and_alert(self, username: str, snap: LiveSnapshot, snap_id: int, state_ref: Dict[str, Any]) -> None:
        """Detecta anomalías basándose en el estado previo del pool."""
        was_live = state_ref.get("was_live", False)
        last_viewers = state_ref.get("last_viewers", 0)

        # Stream start
        if snap.is_live and not was_live:
            _create_alert(
                username=username, alert_type="stream_start", severity="info",
                message=f"@{username} comenzó un live: '{snap.title}'", snapshot_id=snap_id
            )
            log.info(f"[TikTokRadar] 🟢 STREAM_START @{username}: {snap.title}")
            
        # Stream end
        elif not snap.is_live and was_live:
            _create_alert(
                username=username, alert_type="stream_end", severity="info",
                message=f"@{username} terminó su live.", snapshot_id=snap_id
            )
            log.info(f"[TikTokRadar] 🔴 STREAM_END @{username}")

        # Spikes / Bots
        if snap.is_live:
            if last_viewers > 100 and snap.viewers > last_viewers * VIEWER_SPIKE_MULTIPLIER:
                delta = snap.viewers - last_viewers
                _create_alert(
                    username=username, alert_type="viewer_spike", severity="warning",
                    message=f"Spike de viewers detectado en @{username}: +{delta:,}", snapshot_id=snap_id
                )
            if snap.bot_score >= BOT_SCORE_ALERT_THRESHOLD:
                severity = "critical" if snap.bot_score >= 0.75 else "warning"
                _create_alert(
                    username=username, alert_type="bot_detected", severity=severity,
                    message=f"Probabilidad de bots en @{username}: {snap.bot_score:.2f}", snapshot_id=snap_id
                )

    # ── Watchlist API ──────────────────────────────────────────────────────────

    def get_comments(self, username: str) -> List[Dict[str, Any]]:
        """Retorna la lista de comentarios capturados para un canal en memoria."""
        username = username.lstrip("@").lower()
        with self._lock:
            for name, collector in self._chat_collectors.items():
                if name.lower() == username:
                    return list(collector.comments)
        return []

    def get_audio_transcript(self, username: str) -> List[Dict[str, Any]]:
        """Retorna las líneas de transcripción de audio capturadas para un canal en vivo."""
        username = username.lstrip("@").lower()
        with self._lock:
            for name, transcriber in self._audio_transcribers.items():
                if name.lower() == username:
                    return transcriber.get_lines()
        return []

    def watch(self, username: str, interval_sec: int = 60, notes: str = "") -> Dict[str, Any]:
        username = username.lstrip("@")
        success = _add_to_watchlist(username, interval_sec, notes)
        if success and self._running:
            self._sync_watchlist()
        return {"success": success, "username": username}

    def unwatch(self, username: str) -> Dict[str, Any]:
        username = username.lstrip("@")
        success = _remove_from_watchlist(username)
        if success and self._running:
            self._sync_watchlist()
            with self._lock:
                if username in self._chat_collectors:
                    self._chat_collectors[username].stop()
                    del self._chat_collectors[username]
        return {"success": success, "username": username}

    def run_full_osint(self, username: str) -> str:
        engine = TikTokOSINTEngine()
        radar_status = self.get_status()
        radar_data = None
        for channel in radar_status.get("channels", []):
            if channel["username"].lower() == username.lower().strip("@"):
                radar_data = channel
                break
        crossover = engine.run_identity_crossover(username)
        pol = engine.extract_pattern_of_life(username)
        return engine.generate_dossier(username, radar_data, crossover, pol)

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado completo del radar."""
        with self._lock:
            channels = []
            for username, state in self._watchers.items():
                last = _get_last_snapshot(username)
                channels.append({
                    "username": username,
                    "active": True,
                    "interval_sec": state["interval"],
                    "is_live": bool(last and last.get("is_live")),
                    "viewers": last.get("viewers", 0) if last else 0,
                    "title": last.get("title", "") if last else "",
                    "stream_url": last.get("stream_url", "") if last else "",
                    "cdn_provider": last.get("cdn_provider", "unknown") if last else "unknown",
                    "cdn_ip": last.get("cdn_ip", "") if last else "",
                    "geo_country": last.get("geo_country", "") if last else "",
                    "geo_city": last.get("geo_city", "") if last else "",
                    "engagement": last.get("engagement", 0.0) if last else 0.0,
                    "bot_score": last.get("bot_score", 0.0) if last else 0.0,
                    "last_check": last.get("ts", "") if last else "",
                    "room_id": last.get("room_id", "") if last else "",
                    "user_id": last.get("user_id", "") if last else "",
                    "codec_video": last.get("codec_video", "") if last else "",
                    "codec_audio": last.get("codec_audio", "") if last else "",
                    "bitrate_kbps": last.get("bitrate_kbps", 0) if last else 0,
                    "resolution": last.get("resolution", "") if last else "",
                    "fps": last.get("fps", 0.0) if last else 0.0,
                    "error": json.loads(last.get("raw_meta", "{}")).get("error", "") if (last and last.get("raw_meta")) else "",
                })
        return {
            "running": self._running,
            "total_channels": len(self._watchers),
            "live_now": sum(1 for c in channels if c["is_live"]),
            "channels": channels,
            "recent_alerts": _get_recent_alerts(limit=10),
        }

    def get_comments(self, username: str) -> List[Dict[str, Any]]:
        """Retorna los comentarios recolectados en memoria para un canal."""
        username = username.lstrip("@")
        with self._lock:
            collector = self._chat_collectors.get(username)
            if collector:
                return list(collector.comments)
        return []

    def get_report(self, username: str) -> Dict[str, Any]:
        username = username.lstrip("@")
        history = _get_history(username, limit=50)
        alerts = _get_recent_alerts(username=username, limit=20)
        last = history[0] if history else None

        live_count = sum(1 for s in history if s.get("is_live"))
        avg_viewers = sum(s.get("viewers", 0) for s in history if s.get("is_live")) / max(live_count, 1)
        max_viewers = max((s.get("viewers", 0) for s in history), default=0)
        avg_bot_score = sum(s.get("bot_score", 0.0) for s in history) / max(len(history), 1)

        schedule_hints = self._monitor._profile.history_fingerprint(
            [{"ts": s["ts"], "is_live": s.get("is_live")} for s in history]
        )

        return {
            "username": username,
            "ts_report": datetime.now(timezone.utc).isoformat(),
            "snapshots_total": len(history),
            "live_sessions_detected": live_count,
            "avg_viewers_when_live": round(avg_viewers),
            "max_viewers": max_viewers,
            "avg_bot_score": round(avg_bot_score, 3),
            "live_schedule_hints": schedule_hints,
            "current_status": {
                "is_live": bool(last and last.get("is_live")),
                "viewers": last.get("viewers", 0) if last else 0,
                "title": last.get("title", "") if last else "",
                "cdn_provider": last.get("cdn_provider", "") if last else "",
                "geo_country": last.get("geo_country", "") if last else "",
            },
            "alerts": alerts,
            "history": history[:20],  # Últimos 20 snapshots
        }


# ── Singleton & service_loader entrypoint ─────────────────────────────────────

_radar_instance: Optional[TikTokRadar] = None
_radar_lock = threading.Lock()


def get_radar() -> TikTokRadar:
    """Retorna el singleton del TikTokRadar (thread-safe)."""
    global _radar_instance
    if _radar_instance is None:
        with _radar_lock:
            if _radar_instance is None:
                _radar_instance = TikTokRadar()
                _radar_instance.start()
    return _radar_instance


def start_service() -> None:
    """
    Entrypoint para core.service_loader.
    Inicia el radar solo si hay canales en la watchlist.
    """
    radar = get_radar()
    channels = _load_watchlist()
    if channels:
        radar.start()
        log.info(f"[TikTokRadar] Servicio iniciado con {len(channels)} canal(es)")
    else:
        log.info("[TikTokRadar] Servicio en standby — watchlist vacía. Agregar canales vía API.")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TikTok Live Radar — GTLIS")
    sub = parser.add_subparsers(dest="cmd")

    p_watch = sub.add_parser("watch", help="Monitorear un canal")
    p_watch.add_argument("username")
    p_watch.add_argument("--interval", type=int, default=60)

    p_report = sub.add_parser("report", help="Ver reporte de un canal")
    p_report.add_argument("username")

    p_status = sub.add_parser("status", help="Estado del radar")

    args = parser.parse_args()
    radar = get_radar()

    if args.cmd == "watch":
        radar.start()
        result = radar.watch(args.username, args.interval)
        print(json.dumps(result, indent=2))
        print(f"\nMonitoreando @{args.username}... (Ctrl+C para detener)")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            radar.stop()

    elif args.cmd == "report":
        print(json.dumps(radar.get_report(args.username), indent=2, ensure_ascii=False))

    elif args.cmd == "status":
        print(json.dumps(radar.get_status(), indent=2, ensure_ascii=False))

    else:
        parser.print_help()
