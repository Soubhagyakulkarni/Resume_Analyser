CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    required_skills_json TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    application_url TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_jobs_active_updated
    ON jobs (active, updated_at DESC);
