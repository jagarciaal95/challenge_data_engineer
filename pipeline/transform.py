"""Fase 2: raw_jobs -> modelo 3NF mediante SQL, en una sola transacción."""

from __future__ import annotations

import logging

import psycopg

from pipeline.config import TRANSFORM_FILE
from pipeline.db import run_sql_file

log = logging.getLogger(__name__)

TABLES = [
    "raw_jobs",
    "jobs",
    "companies",
    "locations",
    "search_locations",
    "countries",
    "platforms",
    "job_title_categories",
    "schedule_types",
    "job_schedule_types",
    "skills",
    "job_skills",
    "skill_types",
    "skill_type_map",
]


def transform_to_3nf(conn: psycopg.Connection) -> None:
    try:
        run_sql_file(conn, TRANSFORM_FILE)
        conn.commit()
    except Exception:
        conn.rollback()
        log.exception("Transformación fallida; transacción revertida")
        raise
    log_row_counts(conn)


def log_row_counts(conn: psycopg.Connection) -> None:
    for table in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        log.info("%-22s %10d filas", table, count)
