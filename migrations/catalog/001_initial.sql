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

CREATE TABLE IF NOT EXISTS catalog_manifest (
    catalog_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    data_version TEXT NOT NULL,
    app_compatibility TEXT NOT NULL,
    canonical_format TEXT NOT NULL CHECK (canonical_format = 'JSON'),
    generated_from TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_documents (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('OFFICIAL_STANDARD', 'GOVERNMENT_PUBLICATION', 'SCIENTIFIC_REFERENCE', 'OTHER')
    ),
    document_no TEXT NOT NULL,
    document_name TEXT NOT NULL,
    publisher TEXT NOT NULL,
    publication_date TEXT NOT NULL,
    effective_from TEXT,
    effective_to TEXT,
    region TEXT NOT NULL,
    version TEXT NOT NULL,
    official_url TEXT,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('VERIFIED', 'VERIFIED_WITH_INTERPRETATION', 'PENDING_SOURCE', 'DEPRECATED')
    ),
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subject_catalog (
    subject_id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL CHECK (
        subject_type IN ('FUEL', 'ELECTRICITY', 'HEAT', 'GAS', 'PROCESS', 'GWP', 'SYSTEM')
    ),
    name TEXT NOT NULL,
    aliases_json TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS standard_catalog (
    standard_id TEXT PRIMARY KEY,
    standard_number TEXT NOT NULL,
    standard_name TEXT NOT NULL,
    standard_type TEXT NOT NULL CHECK (standard_type IN ('COMMON_RULES', 'INDUSTRY')),
    version TEXT NOT NULL,
    official_status TEXT NOT NULL CHECK (official_status IN ('ACTIVE', 'UPCOMING', 'ABOLISHED', 'UNKNOWN')),
    publication_date TEXT NOT NULL,
    implementation_date TEXT NOT NULL,
    ics TEXT NOT NULL,
    ccs TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    competent_authority TEXT NOT NULL,
    technical_committee TEXT NOT NULL,
    official_source_id TEXT NOT NULL REFERENCES source_documents(source_id),
    official_source_url TEXT NOT NULL,
    base_standard_ids_json TEXT NOT NULL,
    parameter_refs_json TEXT NOT NULL,
    emission_source_refs_json TEXT NOT NULL,
    calculation_status TEXT NOT NULL CHECK (
        calculation_status IN ('COMMON_RULES_ONLY', 'PLANNED', 'IMPLEMENTED')
    ),
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parameter_definitions (
    parameter_id TEXT PRIMARY KEY,
    parameter_type TEXT NOT NULL CHECK (
        parameter_type IN (
            'EMISSION_FACTOR',
            'GWP',
            'LOWER_HEATING_VALUE',
            'CARBON_CONTENT_PER_HEAT',
            'OXIDATION_RATE',
            'COMPOSITION',
            'PROCESS_CO2_FACTOR',
            'ELECTRICITY_EMISSION_FACTOR',
            'HEAT_EMISSION_FACTOR',
            'PROCESS_DEFAULT_PARAMETER',
            'STEAM_ENTHALPY',
            'SYSTEM_CONVERSION'
        )
    ),
    name TEXT NOT NULL,
    canonical_unit TEXT NOT NULL,
    subject_id TEXT NOT NULL REFERENCES subject_catalog(subject_id),
    source_id TEXT NOT NULL REFERENCES source_documents(source_id),
    source_location TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('VERIFIED', 'VERIFIED_WITH_INTERPRETATION', 'PENDING_SOURCE', 'DEPRECATED')
    ),
    applicable_standard_ids_json TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS factor_values (
    factor_id TEXT PRIMARY KEY,
    parameter_id TEXT NOT NULL REFERENCES parameter_definitions(parameter_id),
    subject_id TEXT NOT NULL REFERENCES subject_catalog(subject_id),
    value TEXT NOT NULL,
    unit TEXT NOT NULL,
    source_value TEXT NOT NULL,
    source_unit TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    normalized_unit TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES source_documents(source_id),
    source_location TEXT NOT NULL,
    factor_year INTEGER NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    value_type TEXT NOT NULL CHECK (
        value_type IN (
            'STANDARD_SPECIFIED',
            'STANDARD_DEFAULT',
            'GOVERNMENT_PUBLISHED',
            'SCIENTIFIC_REFERENCE',
            'MEASURED',
            'DERIVED',
            'SYSTEM_CONSTANT',
            'HISTORICAL'
        )
    ),
    review_status TEXT NOT NULL CHECK (
        review_status IN ('VERIFIED', 'VERIFIED_WITH_INTERPRETATION', 'PENDING_SOURCE', 'DEPRECATED')
    ),
    applicable_standard_ids_json TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS factor_applicable_standards (
    factor_id TEXT NOT NULL REFERENCES factor_values(factor_id),
    standard_id TEXT NOT NULL REFERENCES standard_catalog(standard_id),
    PRIMARY KEY (factor_id, standard_id)
);

CREATE TABLE IF NOT EXISTS conversion_rules (
    conversion_id TEXT PRIMARY KEY,
    from_unit TEXT NOT NULL,
    to_unit TEXT NOT NULL,
    multiplier TEXT NOT NULL,
    offset TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES source_documents(source_id),
    source_location TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK (
        review_status IN ('VERIFIED', 'VERIFIED_WITH_INTERPRETATION', 'PENDING_SOURCE', 'DEPRECATED')
    ),
    notes TEXT NOT NULL
);
