-- ==============================================================================
-- Schema initialization for GradCafe analytics database
-- Module 6: Deploy Anywhere Assignment
-- Johns Hopkins University - Software Concepts (EN.605.601)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS applicants (
    p_id INTEGER PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

CREATE INDEX IF NOT EXISTS idx_applicants_date_added ON applicants (date_added);
CREATE INDEX IF NOT EXISTS idx_applicants_status ON applicants (status);
CREATE INDEX IF NOT EXISTS idx_applicants_degree ON applicants (degree);

-- Ingestion watermarks table for idempotent incremental scraping
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Seed default watermark entry for gradcafe scraper
INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
VALUES ('gradcafe_scraper', NULL, now())
ON CONFLICT (source) DO NOTHING;
