ALTER TABLE accounting_records ADD COLUMN raw_input_snapshot_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE accounting_records ADD COLUMN effective_rule_set_json TEXT NOT NULL DEFAULT '{"rule_ids":[]}';
ALTER TABLE accounting_records ADD COLUMN deleted_at TEXT;
ALTER TABLE accounting_records ADD COLUMN deleted_by TEXT;
ALTER TABLE accounting_records ADD COLUMN deleted_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_accounting_records_active_created
    ON accounting_records (deleted_at, created_at DESC, record_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_record_time
    ON audit_log (record_id, occurred_at, audit_id);