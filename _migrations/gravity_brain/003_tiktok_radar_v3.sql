-- Migration 003: TikTok Live Intelligence Suite (GTLIS) — v2 → v3
-- Añade columnas vitales para guardar los ID nativos del canal y la telemetría urbana

ALTER TABLE tiktok_snapshots ADD COLUMN room_id TEXT DEFAULT '';
ALTER TABLE tiktok_snapshots ADD COLUMN user_id TEXT DEFAULT '';
ALTER TABLE tiktok_snapshots ADD COLUMN geo_city TEXT DEFAULT '';
