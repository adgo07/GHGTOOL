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

CREATE TABLE IF NOT EXISTS accounting_records (
    record_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('COMPLETED', 'COMPLETED_WITH_WARNINGS')),
    created_at TEXT NOT NULL,
    standard_id TEXT NOT NULL,
    standard_version TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    input_snapshot_json TEXT NOT NULL,
    calculation_snapshot_json TEXT NOT NULL,
    parameter_snapshot_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    record_id TEXT,
    action TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    details_json TEXT NOT NULL
);
