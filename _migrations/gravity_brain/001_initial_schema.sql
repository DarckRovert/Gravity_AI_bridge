-- Migration 001: Baseline del schema REAL de gravity_brain.db (v0 → v1)
-- Este script documenta el estado exacto de las tablas existentes.
-- CREATE TABLE IF NOT EXISTS no rompe si ya existen.

CREATE TABLE IF NOT EXISTS strategic_decisions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT    NOT NULL DEFAULT (datetime('now')),
    category     TEXT    NOT NULL DEFAULT 'system',
    title        TEXT    NOT NULL,
    description  TEXT,
    rationale    TEXT,
    action_taken TEXT,
    outcome      TEXT    DEFAULT 'pending',
    outcome_detail TEXT,
    outcome_ts   TEXT,
    impact_score REAL    DEFAULT 0.0,
    metadata     TEXT    DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS system_patterns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL DEFAULT (datetime('now')),
    pattern_key TEXT    NOT NULL UNIQUE,
    pattern_val TEXT    NOT NULL,
    hits        INTEGER DEFAULT 1,
    last_seen   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Índices para el OODA loop (consultas frecuentes)
CREATE INDEX IF NOT EXISTS idx_sd_category  ON strategic_decisions (category);
CREATE INDEX IF NOT EXISTS idx_sd_outcome   ON strategic_decisions (outcome);
CREATE INDEX IF NOT EXISTS idx_sd_ts        ON strategic_decisions (ts);
CREATE INDEX IF NOT EXISTS idx_sp_key       ON system_patterns (pattern_key);
CREATE INDEX IF NOT EXISTS idx_sp_last_seen ON system_patterns (last_seen);
