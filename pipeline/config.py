"""Configuración leída desde variables de entorno (.env). Sin credenciales en el código."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
RAW_DDL_FILE = SQL_DIR / "raw_jobs.sql"
SCHEMA_FILE = SQL_DIR / "schema.sql"
TRANSFORM_FILE = SQL_DIR / "transform_3nf.sql"

REQUIRED_VARS = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    dbname: str
    user: str
    password: str = field(repr=False)

    @property
    def conninfo(self) -> str:
        return make_conninfo(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
        )


def load_settings() -> Settings:
    load_dotenv()
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"Faltan variables de entorno: {', '.join(missing)}. "
            "Copia .env.example a .env y complétalo."
        )
    return Settings(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
