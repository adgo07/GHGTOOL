-- Mutable project-only state; canonical input is isolated from records.sqlite.
ALTER TABLE accounting_units ADD COLUMN canonical_input_json TEXT;
ALTER TABLE accounting_units ADD COLUMN ingress_provenance_json TEXT;