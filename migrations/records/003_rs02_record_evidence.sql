ALTER TABLE accounting_records ADD COLUMN trace_snapshot_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE accounting_records ADD COLUMN provenance_snapshot_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE accounting_records ADD COLUMN reporting_snapshot_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE accounting_records ADD COLUMN report_qualification_json TEXT NOT NULL DEFAULT '{}';
