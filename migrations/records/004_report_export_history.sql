CREATE TABLE IF NOT EXISTS report_export_history (
    export_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL REFERENCES accounting_records(record_id),
    exported_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'DOCX',
    template_version TEXT NOT NULL DEFAULT '1.0.0',
    document_filename TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    supplementary_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_export_history_record_time
    ON report_export_history (record_id, exported_at, export_id);

CREATE TRIGGER IF NOT EXISTS report_export_history_no_update
BEFORE UPDATE ON report_export_history
BEGIN
    SELECT RAISE(ABORT, 'report export history is append-only');
END;

CREATE TRIGGER IF NOT EXISTS report_export_history_no_delete
BEFORE DELETE ON report_export_history
BEGIN
    SELECT RAISE(ABORT, 'report export history is append-only');
END;
