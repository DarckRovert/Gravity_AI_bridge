-- Migration 002: TikTok Live Intelligence Suite (GTLIS) — v1 → v2
-- Tabla de snapshots del radar TikTok. Cada registro = 1 captura de un canal en un instante.

CREATE TABLE IF NOT EXISTS tiktok_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL,
    ts            TEXT    NOT NULL DEFAULT (datetime('now')),  -- ISO-8601 UTC
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
    bot_score     REAL    NOT NULL DEFAULT 0.0,  -- 0.0=limpio, 1.0=alta sospecha de bots
    engagement    REAL    NOT NULL DEFAULT 0.0,  -- (likes+comments)/viewers * 100
    raw_meta      TEXT    DEFAULT '{}'            -- JSON completo de yt-dlp / ffprobe
);

-- Tabla de canales en watchlist del radar
CREATE TABLE IF NOT EXISTS tiktok_watchlist (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT    NOT NULL UNIQUE,
    added_ts     TEXT    NOT NULL DEFAULT (datetime('now')),
    interval_sec INTEGER NOT NULL DEFAULT 60,    -- frecuencia de polling en segundos
    active       INTEGER NOT NULL DEFAULT 1,     -- 1=monitoreando, 0=pausado
    notes        TEXT    DEFAULT ''
);

-- Tabla de alertas generadas por el radar
CREATE TABLE IF NOT EXISTS tiktok_alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL,
    ts          TEXT    NOT NULL DEFAULT (datetime('now')),
    alert_type  TEXT    NOT NULL,  -- 'viewer_spike', 'bot_detected', 'stream_start', 'stream_end'
    severity    TEXT    NOT NULL DEFAULT 'info',  -- 'info', 'warning', 'critical'
    message     TEXT    NOT NULL,
    snapshot_id INTEGER REFERENCES tiktok_snapshots(id),
    acknowledged INTEGER NOT NULL DEFAULT 0
);

-- Índices para queries frecuentes del radar y el dashboard
CREATE INDEX IF NOT EXISTS idx_tiktok_snap_user_ts  ON tiktok_snapshots (username, ts);
CREATE INDEX IF NOT EXISTS idx_tiktok_snap_is_live  ON tiktok_snapshots (is_live, ts);
CREATE INDEX IF NOT EXISTS idx_tiktok_watch_active  ON tiktok_watchlist (active);
CREATE INDEX IF NOT EXISTS idx_tiktok_alert_user_ts ON tiktok_alerts (username, ts);
CREATE INDEX IF NOT EXISTS idx_tiktok_alert_ack     ON tiktok_alerts (acknowledged);
