-- Migration 001: Baseline del schema REAL de _video_queue.sqlite (v0 → v1)
-- Documenta el estado exacto de video_jobs tal como existe en producción.

CREATE TABLE IF NOT EXISTS video_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic           TEXT    NOT NULL,
    n_scenes        INTEGER NOT NULL DEFAULT 6,
    voice_speed     INTEGER NOT NULL DEFAULT 150,
    voice_id        TEXT    NOT NULL DEFAULT '',
    style           TEXT    NOT NULL DEFAULT 'documental',
    narration_lang  TEXT    NOT NULL DEFAULT 'es',
    transitions     INTEGER NOT NULL DEFAULT 1,
    status          TEXT    NOT NULL DEFAULT 'pending',
    progress        INTEGER NOT NULL DEFAULT 0,
    current_step    TEXT,
    output_path     TEXT,
    error           TEXT,
    created_at      TEXT    NOT NULL,
    started_at      TEXT,
    finished_at     TEXT,
    resolution      TEXT    NOT NULL DEFAULT '1024x1024',
    subtitles       INTEGER NOT NULL DEFAULT 1,
    title           TEXT    NOT NULL DEFAULT '',
    bgm_type        TEXT    NOT NULL DEFAULT 'ninguna',
    quality         TEXT    NOT NULL DEFAULT 'hd',
    use_lore        INTEGER NOT NULL DEFAULT 1,
    fps             INTEGER NOT NULL DEFAULT 24,
    scene_duration  INTEGER NOT NULL DEFAULT 8,
    duration_mode   TEXT    NOT NULL DEFAULT 'auto',
    bgm_volume      REAL    NOT NULL DEFAULT 0.1,
    codec           TEXT    NOT NULL DEFAULT 'libx264',
    ken_burns       INTEGER NOT NULL DEFAULT 1,
    intro_card      INTEGER NOT NULL DEFAULT 0,
    color_grade     TEXT    NOT NULL DEFAULT 'auto',
    thumbnail_path  TEXT    NOT NULL DEFAULT '',
    animation_effect TEXT   NOT NULL DEFAULT 'auto',
    animation_level INTEGER NOT NULL DEFAULT 1,
    youtube_video_id TEXT   NOT NULL DEFAULT '',
    youtube_url     TEXT    NOT NULL DEFAULT '',
    uploaded_at     TEXT    NOT NULL DEFAULT '',
    upload_status   TEXT    NOT NULL DEFAULT 'pending',
    shorts_path     TEXT    NOT NULL DEFAULT '',
    shorts_video_id TEXT    NOT NULL DEFAULT '',
    seo_tags        TEXT    NOT NULL DEFAULT '',
    seo_description TEXT    NOT NULL DEFAULT '',
    niche_id        TEXT    NOT NULL DEFAULT '',
    cloned_from     INTEGER NOT NULL DEFAULT 0,
    clone_lang      TEXT    NOT NULL DEFAULT '',
    job_type        TEXT    NOT NULL DEFAULT 'tts',
    audio_track_path TEXT   NOT NULL DEFAULT '',
    lyrics_text     TEXT    NOT NULL DEFAULT '',
    input_video_path TEXT   NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_vj_status      ON video_jobs (status);
CREATE INDEX IF NOT EXISTS idx_vj_niche       ON video_jobs (niche_id);
CREATE INDEX IF NOT EXISTS idx_vj_created_at  ON video_jobs (created_at);
CREATE INDEX IF NOT EXISTS idx_vj_upload_status ON video_jobs (upload_status);
