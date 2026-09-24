PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pending_record_links (
    record_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    workspace_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pending_record_links_project
    ON pending_record_links(project_id, created_at, record_id);
