-- =====================================================================
-- Modelo relacional en 3NF
-- =====================================================================

CREATE TABLE IF NOT EXISTS companies (
    company_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS countries (
    country_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE
);

-- El país depende de la búsqueda (search_location), no de la ubicación de la oferta.
CREATE TABLE IF NOT EXISTS search_locations (
    search_location_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    search_location_name TEXT NOT NULL UNIQUE,
    country_id           INTEGER REFERENCES countries (country_id)
);

CREATE TABLE IF NOT EXISTS locations (
    location_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS platforms (
    platform_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS job_title_categories (
    title_category_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title_category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS schedule_types (
    schedule_type_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schedule_type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skill_types (
    skill_type_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    skill_type_name TEXT NOT NULL UNIQUE
);

-- Una skill puede pertenecer a varias categorías (p. ej. mongodb, sas).
CREATE TABLE IF NOT EXISTS skill_type_map (
    skill_id      INTEGER NOT NULL REFERENCES skills (skill_id),
    skill_type_id INTEGER NOT NULL REFERENCES skill_types (skill_type_id),
    PRIMARY KEY (skill_id, skill_type_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id               BIGINT PRIMARY KEY,          -- = raw_id (trazabilidad)
    job_title            TEXT NOT NULL,
    title_category_id    INTEGER REFERENCES job_title_categories (title_category_id),
    company_id           INTEGER REFERENCES companies (company_id),
    location_id          INTEGER REFERENCES locations (location_id),
    search_location_id   INTEGER REFERENCES search_locations (search_location_id),
    platform_id          INTEGER REFERENCES platforms (platform_id),
    posted_at            TIMESTAMP,
    is_remote            BOOLEAN,
    no_degree_mention    BOOLEAN,
    has_health_insurance BOOLEAN,
    salary_rate          TEXT,
    salary_year_avg      NUMERIC(14, 2) CHECK (salary_year_avg IS NULL OR salary_year_avg >= 0),
    salary_hour_avg      NUMERIC(10, 2) CHECK (salary_hour_avg IS NULL OR salary_hour_avg >= 0)
);

CREATE TABLE IF NOT EXISTS job_schedule_types (
    job_id           BIGINT  NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    schedule_type_id INTEGER NOT NULL REFERENCES schedule_types (schedule_type_id),
    PRIMARY KEY (job_id, schedule_type_id)
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id   BIGINT  NOT NULL REFERENCES jobs (job_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills (skill_id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company   ON jobs (company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_location  ON jobs (location_id);
CREATE INDEX IF NOT EXISTS idx_jobs_search    ON jobs (search_location_id);
CREATE INDEX IF NOT EXISTS idx_jobs_title_cat ON jobs (title_category_id);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs (posted_at);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills (skill_id);