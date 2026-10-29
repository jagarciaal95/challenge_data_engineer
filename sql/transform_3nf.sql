-- =====================================================================
-- raw_jobs -> modelo 3NF. Idempotente: reconstruye todas las tablas.
-- Se ejecuta en una sola transaccion (la gestiona Python).
-- =====================================================================

TRUNCATE job_schedule_types, job_skills, skill_type_map, jobs, skills, skill_types,
         schedule_types, search_locations, locations, countries, companies,
         platforms, job_title_categories
    RESTART IDENTITY;

-- 1) Deduplicacion y estandarizacion -----------------------------------
-- El CSV no trae ID: la clave de negocio es (titulo, empresa, ubicacion,
-- plataforma, fecha). Se conserva la fila con menor raw_id (determinista).
-- Se excluyen las ofertas sin titulo.
CREATE TEMP TABLE stg_jobs ON COMMIT DROP AS
SELECT raw_id, job_title, job_title_short, company_name, job_location,
       search_location, job_country, platform, job_schedule_type,
       job_posted_date, job_work_from_home, job_no_degree_mention,
       job_health_insurance, salary_rate, salary_year_avg, salary_hour_avg
FROM (
    SELECT raw_id, job_title, job_title_short, company_name, job_location,
           search_location, job_country, job_schedule_type, job_posted_date,
           job_work_from_home, job_no_degree_mention, job_health_insurance,
           salary_rate, salary_year_avg, salary_hour_avg,
           -- "via LinkedIn" -> "LinkedIn"
           NULLIF(btrim(regexp_replace(job_via, '^\s*via\s+', '', 'i')), '') AS platform,
           ROW_NUMBER() OVER (
               PARTITION BY job_title, company_name, job_location, job_via, job_posted_date
               ORDER BY raw_id
           ) AS rn
    FROM raw_jobs
    WHERE job_title IS NOT NULL
) t
WHERE rn = 1;

CREATE INDEX ON stg_jobs (raw_id);

-- 2) Dimensiones simples -------------------------------------------------
INSERT INTO companies (company_name)
SELECT DISTINCT company_name FROM stg_jobs WHERE company_name IS NOT NULL ORDER BY 1;

INSERT INTO locations (location_name)
SELECT DISTINCT job_location FROM stg_jobs WHERE job_location IS NOT NULL ORDER BY 1;

INSERT INTO platforms (platform_name)
SELECT DISTINCT platform FROM stg_jobs WHERE platform IS NOT NULL ORDER BY 1;

INSERT INTO job_title_categories (title_category_name)
SELECT DISTINCT job_title_short FROM stg_jobs WHERE job_title_short IS NOT NULL ORDER BY 1;

INSERT INTO countries (country_name)
SELECT DISTINCT job_country FROM stg_jobs WHERE job_country IS NOT NULL ORDER BY 1;

-- 3) Busquedas: job_country depende de search_location (verificado en los datos)
INSERT INTO search_locations (search_location_name, country_id)
SELECT s.search_location, c.country_id
FROM (
    SELECT search_location, MAX(job_country) AS country
    FROM stg_jobs
    WHERE search_location IS NOT NULL
    GROUP BY search_location
) s
LEFT JOIN countries c ON c.country_name = s.country
ORDER BY s.search_location;

-- 4) Horarios: el texto original combina varios valores ("A, B, and C")
-- Se parte en valores atomicos y se unifican dos valores en otro idioma
-- (supuesto: "Pekerjaan tetap" = Full-time, "Kontraktor" = Contractor).
CREATE TEMP TABLE stg_schedules ON COMMIT DROP AS
SELECT DISTINCT s.raw_id,
       CASE btrim(p.part)
            WHEN 'Pekerjaan tetap' THEN 'Full-time'
            WHEN 'Kontraktor'      THEN 'Contractor'
            ELSE btrim(p.part)
       END AS schedule_type
FROM stg_jobs s,
     LATERAL regexp_split_to_table(s.job_schedule_type, '\s*,\s*(?:and\s+)?|\s+and\s+') AS p(part)
WHERE s.job_schedule_type IS NOT NULL
  AND btrim(p.part) <> '';

INSERT INTO schedule_types (schedule_type_name)
SELECT DISTINCT schedule_type FROM stg_schedules ORDER BY 1;

-- 5) Skills -----------------------------------------------------------------
CREATE TEMP TABLE stg_job_skills ON COMMIT DROP AS
SELECT DISTINCT s.raw_id, lower(btrim(u.skill)) AS skill_name
FROM stg_jobs s
JOIN raw_jobs r ON r.raw_id = s.raw_id,
     LATERAL unnest(r.job_skills) AS u(skill)
WHERE NULLIF(btrim(u.skill), '') IS NOT NULL;

CREATE TEMP TABLE stg_type_skills ON COMMIT DROP AS
SELECT DISTINCT lower(btrim(k.key)) AS skill_type_name, lower(btrim(v.skill)) AS skill_name
FROM stg_jobs s
JOIN raw_jobs r ON r.raw_id = s.raw_id,
     LATERAL jsonb_each(CASE WHEN jsonb_typeof(r.job_type_skills) = 'object'
                             THEN r.job_type_skills ELSE '{}'::jsonb END) AS k,
     LATERAL jsonb_array_elements_text(CASE WHEN jsonb_typeof(k.value) = 'array'
                                            THEN k.value ELSE '[]'::jsonb END) AS v(skill)
WHERE NULLIF(btrim(v.skill), '') IS NOT NULL
  AND NULLIF(btrim(k.key), '') IS NOT NULL;

INSERT INTO skills (skill_name)
SELECT skill_name FROM stg_job_skills
UNION
SELECT skill_name FROM stg_type_skills
ORDER BY 1;

INSERT INTO skill_types (skill_type_name)
SELECT DISTINCT skill_type_name FROM stg_type_skills ORDER BY 1;

INSERT INTO skill_type_map (skill_id, skill_type_id)
SELECT sk.skill_id, st.skill_type_id
FROM stg_type_skills ts
JOIN skills sk      ON sk.skill_name = ts.skill_name
JOIN skill_types st ON st.skill_type_name = ts.skill_type_name;

-- 6) Hechos -------------------------------------------------------------------
INSERT INTO jobs (job_id, job_title, title_category_id, company_id, location_id,
                  search_location_id, platform_id, posted_at, is_remote,
                  no_degree_mention, has_health_insurance, salary_rate,
                  salary_year_avg, salary_hour_avg)
SELECT s.raw_id, s.job_title, tc.title_category_id, c.company_id, l.location_id,
       sl.search_location_id, p.platform_id, s.job_posted_date, s.job_work_from_home,
       s.job_no_degree_mention, s.job_health_insurance, s.salary_rate,
       s.salary_year_avg, s.salary_hour_avg
FROM stg_jobs s
LEFT JOIN job_title_categories tc ON tc.title_category_name = s.job_title_short
LEFT JOIN companies c             ON c.company_name = s.company_name
LEFT JOIN locations l             ON l.location_name = s.job_location
LEFT JOIN search_locations sl     ON sl.search_location_name = s.search_location
LEFT JOIN platforms p             ON p.platform_name = s.platform;

INSERT INTO job_schedule_types (job_id, schedule_type_id)
SELECT ss.raw_id, st.schedule_type_id
FROM stg_schedules ss
JOIN schedule_types st ON st.schedule_type_name = ss.schedule_type;

INSERT INTO job_skills (job_id, skill_id)
SELECT js.raw_id, sk.skill_id
FROM stg_job_skills js
JOIN skills sk ON sk.skill_name = js.skill_name;
