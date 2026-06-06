-- ============================================================================
-- DMD — Dubai Medical Directory PostgreSQL schema
-- Generated: 2026-06-06 (cron health check 567b5bee)
-- Source: DHA Sheryan Registry — 101 080 rows, 65 593 unique DHA IDs
-- CSV: data/dha_professionals_full.csv (9.5 MB)
-- ============================================================================

-- Drop in reverse-dependency order (safe re-run)
DROP TABLE IF EXISTS dmd.facility_summary     CASCADE;
DROP TABLE IF EXISTS dmd.professional        CASCADE;
DROP TABLE IF EXISTS dmd.specialty_catalog   CASCADE;
DROP TABLE IF EXISTS dmd.license_type_lookup CASCADE;
DROP TABLE IF EXISTS dmd.category_lookup     CASCADE;
DROP TABLE IF EXISTS dmd.ingestion_log       CASCADE;

CREATE SCHEMA IF NOT EXISTS dmd;
SET search_path TO dmd, public;

-- ----------------------------------------------------------------------------
-- Lookups
-- ----------------------------------------------------------------------------
CREATE TABLE dmd.category_lookup (
    category_id   SMALLSERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE dmd.license_type_lookup (
    license_type  CHAR(3)  PRIMARY KEY,    -- FTL, REG, PTL, TRL
    description   TEXT
);

CREATE TABLE dmd.specialty_catalog (
    specialty_id  SERIAL PRIMARY KEY,
    specialty     TEXT NOT NULL UNIQUE
);

-- ----------------------------------------------------------------------------
-- Main table — one row per DHA professional (uniqueness on dhaUniqueId)
-- ----------------------------------------------------------------------------
CREATE TABLE dmd.professional (
    dha_unique_id      CHAR(8)     PRIMARY KEY,        -- e.g. "00216930"
    full_name          TEXT        NOT NULL,
    category           TEXT        NOT NULL,
    specialty          TEXT        NOT NULL,
    license_type       CHAR(3)     NOT NULL,
    facility_name      TEXT,                            -- nullable 30.2%
    license_count      SMALLINT    NOT NULL DEFAULT 1,
    facility_count     SMALLINT    NOT NULL DEFAULT 0,
    has_photo          BOOLEAN     NOT NULL DEFAULT FALSE,

    -- denormalised search fields
    search_text        TSVECTOR,                        -- generated below

    -- provenance
    source_dataset     TEXT        NOT NULL DEFAULT 'DHA Sheryan Registry',
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- FK
    CONSTRAINT fk_pro_cat  FOREIGN KEY (category)
        REFERENCES dmd.category_lookup(category_name)     ON UPDATE CASCADE,
    CONSTRAINT fk_pro_lic  FOREIGN KEY (license_type)
        REFERENCES dmd.license_type_lookup(license_type)  ON UPDATE CASCADE
);

CREATE INDEX idx_professional_category  ON dmd.professional(category);
CREATE INDEX idx_professional_specialty ON dmd.professional(specialty);
CREATE INDEX idx_professional_facility  ON dmd.professional(facility_name);
CREATE INDEX idx_professional_license   ON dmd.professional(license_type);
CREATE INDEX idx_professional_name_trgm ON dmd.professional
    USING GIN (full_name gin_trgm_ops);
CREATE INDEX idx_professional_search     ON dmd.professional
    USING GIN (search_text);

-- Generated search vector (name + specialty + facility)
CREATE OR REPLACE FUNCTION dmd.tsv_professional() RETURNS trigger AS $$
BEGIN
    NEW.search_text :=
        setweight(to_tsvector('simple', COALESCE(NEW.full_name, '')),    'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.specialty, '')),   'B') ||
        setweight(to_tsvector('simple', COALESCE(NEW.facility_name,'')), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_professional_tsv
    BEFORE INSERT OR UPDATE ON dmd.professional
    FOR EACH ROW EXECUTE FUNCTION dmd.tsv_professional();

-- ----------------------------------------------------------------------------
-- Aggregated facility summary (for landing pages & "Top 20" widgets)
-- ----------------------------------------------------------------------------
CREATE TABLE dmd.facility_summary AS
    SELECT
        facility_name,
        COUNT(*)                          AS professional_count,
        COUNT(DISTINCT category)          AS category_count,
        COUNT(DISTINCT specialty)         AS specialty_count,
        MIN(ingested_at)                  AS first_seen
    FROM dmd.professional
    WHERE facility_name IS NOT NULL
    GROUP BY facility_name;

CREATE INDEX idx_facility_summary_count ON dmd.facility_summary(professional_count DESC);

-- ----------------------------------------------------------------------------
-- Ingestion audit log
-- ----------------------------------------------------------------------------
CREATE TABLE dmd.ingestion_log (
    log_id        BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at   TIMESTAMPTZ,
    rows_attempt  INTEGER,
    rows_inserted INTEGER,
    rows_skipped  INTEGER,
    csv_path      TEXT,
    status        TEXT NOT NULL DEFAULT 'running'   -- running|ok|failed
);

-- ----------------------------------------------------------------------------
-- Seed lookups
-- ----------------------------------------------------------------------------
INSERT INTO dmd.license_type_lookup(license_type, description) VALUES
    ('FTL', 'Full Time License'),
    ('REG', 'Registered'),
    ('PTL', 'Part Time License'),
    ('TRL', 'Temporary License')
ON CONFLICT DO NOTHING;

-- pre-warm categories observed in dataset
INSERT INTO dmd.category_lookup(category_name) VALUES
    ('Nurse and Midwife'),
    ('Allied Health'),
    ('Physician'),
    ('Dentist'),
    ('Traditional Complementary and Integrative Medicine Practitioners (TCIM)')
ON CONFLICT DO NOTHING;

-- Enable trigram for fuzzy name search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
