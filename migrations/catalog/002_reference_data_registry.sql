PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS reference_source_tables (
    source_table_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source_documents(source_id),
    display_number TEXT NOT NULL,
    title TEXT NOT NULL,
    source_location TEXT NOT NULL,
    layout TEXT NOT NULL CHECK (layout IN ('flat', 'parameter_matrix', 'provider')),
    columns_json TEXT NOT NULL,
    provider_id TEXT,
    notes TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_data_assets (
    asset_id TEXT PRIMARY KEY,
    asset_version TEXT NOT NULL,
    parameter_id TEXT NOT NULL REFERENCES parameter_definitions(parameter_id),
    subject_id TEXT NOT NULL REFERENCES subject_catalog(subject_id),
    value TEXT NOT NULL,
    unit TEXT NOT NULL,
    source_value TEXT NOT NULL,
    source_unit TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    normalized_unit TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (
        value_type IN (
            'STANDARD_SPECIFIED', 'STANDARD_DEFAULT', 'GOVERNMENT_PUBLISHED',
            'SCIENTIFIC_REFERENCE', 'MEASURED', 'DERIVED', 'SYSTEM_CONSTANT', 'HISTORICAL'
        )
    ),
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_data_bindings (
    binding_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES reference_data_assets(asset_id),
    source_table_id TEXT NOT NULL REFERENCES reference_source_tables(source_table_id),
    binding_type TEXT NOT NULL CHECK (binding_type IN ('FACTOR_SOURCE', 'STANDARD_REFERENCE')),
    factor_id TEXT REFERENCES factor_values(factor_id),
    source_location TEXT NOT NULL,
    applicable_standard_ids_json TEXT NOT NULL,
    factor_year INTEGER NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('VERIFIED', 'VERIFIED_WITH_INTERPRETATION', 'PENDING_SOURCE', 'DEPRECATED')
    ),
    notes TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reference_bindings_asset
    ON reference_data_bindings(asset_id, source_table_id);
CREATE INDEX IF NOT EXISTS idx_reference_bindings_table
    ON reference_data_bindings(source_table_id, asset_id);
