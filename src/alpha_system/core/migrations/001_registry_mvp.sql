CREATE TABLE IF NOT EXISTS dataset_versions (
    data_version TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source_uri TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    config_hash TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS factor_registry (
    factor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS factor_versions (
    factor_id TEXT NOT NULL,
    factor_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (factor_id, factor_version)
);

CREATE TABLE IF NOT EXISTS factor_validation_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    label_versions_json TEXT NOT NULL DEFAULT '{}',
    engine_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS label_versions (
    label_id TEXT NOT NULL,
    label_version TEXT NOT NULL,
    label_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (label_id, label_version)
);

CREATE TABLE IF NOT EXISTS study_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    label_versions_json TEXT NOT NULL DEFAULT '{}',
    engine_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS strategy_registry (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS strategy_versions (
    strategy_id TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (strategy_id, strategy_version)
);

CREATE TABLE IF NOT EXISTS grid_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    label_versions_json TEXT NOT NULL DEFAULT '{}',
    engine_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ml_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    label_versions_json TEXT NOT NULL DEFAULT '{}',
    engine_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    git_commit TEXT,
    git_dirty INTEGER,
    code_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    data_version TEXT NOT NULL,
    factor_versions_json TEXT NOT NULL DEFAULT '{}',
    label_versions_json TEXT NOT NULL DEFAULT '{}',
    engine_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    decision_status TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    status_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS artifact_manifest (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    run_table TEXT NOT NULL,
    artifact_key TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    content_hash TEXT NOT NULL DEFAULT '',
    artifact_role TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status_message TEXT NOT NULL DEFAULT '',
    UNIQUE (run_id, artifact_key, artifact_path)
);

CREATE TABLE IF NOT EXISTS promotion_decisions (
    decision_id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    subject_version TEXT NOT NULL DEFAULT '',
    run_id TEXT NOT NULL DEFAULT '',
    decision_status TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    reviewer TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    artifact_paths_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    status_message TEXT NOT NULL DEFAULT ''
);
