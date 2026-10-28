from __future__ import annotations

import logging
from pathlib import Path

import psycopg

from pipeline.config import RAW_DDL_FILE, Settings

log = logging.getLogger(__name__)


def connect(settings: Settings) -> psycopg.Connection:
    return psycopg.connect(settings.conninfo)


def run_sql_file(conn: psycopg.Connection, path: Path) -> None:
    log.info("Ejecutando %s", path.name)
    conn.execute(path.read_text(encoding="utf-8"))


def create_raw_table(conn: psycopg.Connection) -> None:
    run_sql_file(conn, RAW_DDL_FILE)
    conn.commit()