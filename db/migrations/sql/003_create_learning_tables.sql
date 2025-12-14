-- 003_create_learning_tables.sql
BEGIN;

-- Learning tables for INKA (for systems preferring DB persistence instead of files)
CREATE TABLE IF NOT EXISTS learning_rules (
    id BIGSERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by VARCHAR(64) NULL,
    version INT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS learning_faq (
    id BIGSERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by VARCHAR(64) NULL
);

CREATE TABLE IF NOT EXISTS learning_style (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by VARCHAR(64) NULL
);

CREATE TABLE IF NOT EXISTS inka_action_log (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    role TEXT NULL,
    action TEXT NOT NULL,
    detail JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMIT;
