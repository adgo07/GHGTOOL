PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS database_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    active_unit_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounting_units (
    unit_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    unit_name TEXT NOT NULL,
    unit_type TEXT NOT NULL CHECK (unit_type IN ('WHOLE_SITE', 'PROCESS', 'OTHER')),
    position INTEGER NOT NULL,
    form_state_json TEXT NOT NULL,
    result_snapshot_json TEXT,
    record_ids_json TEXT NOT NULL,
    input_fingerprint TEXT
);

CREATE INDEX IF NOT EXISTS idx_accounting_units_project_position
    ON accounting_units(project_id, position, unit_id);
