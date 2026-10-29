from pipeline.config import load_settings
from pipeline.db import connect

QUERIES = {
    "Filas totales": "SELECT COUNT(*) FROM raw_jobs",
    "Con skills": "SELECT COUNT(job_skills) FROM raw_jobs",
    "Con type_skills": "SELECT COUNT(job_type_skills) FROM raw_jobs",
    "Tipos": "SELECT pg_typeof(job_skills)::text, pg_typeof(job_type_skills)::text FROM raw_jobs LIMIT 1",
    "salary_rate": "SELECT salary_rate, COUNT(*) FROM raw_jobs GROUP BY 1 ORDER BY 2 DESC",
    "Rango de fechas": "SELECT MIN(job_posted_date), MAX(job_posted_date) FROM raw_jobs",
}

with connect(load_settings()) as conn:
    for title, sql in QUERIES.items():
        print(f"\n== {title}")
        for row in conn.execute(sql).fetchall():
            print(row)
