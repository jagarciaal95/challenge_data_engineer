from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

from pipeline.clean import COLUMNS, prepare_chunk
from pipeline.validate import validate_chunk

log = logging.getLogger(__name__)

COPY_TYPES = [
    "text",
    "text",
    "text",
    "text",
    "text",
    "bool",
    "text",
    "timestamp",
    "bool",
    "bool",
    "text",
    "text",
    "float8",
    "float8",
    "text",
    "text[]",
    "jsonb",
]


def iter_rows(df: pd.DataFrame) -> Iterator[tuple[Any, ...]]:
    obj = df.astype(object).where(df.notna(), None)
    for row in obj.itertuples(index=False, name=None):
        values = [v.to_pydatetime() if isinstance(v, pd.Timestamp) else v for v in row]
        values[-1] = Jsonb(values[-1]) if values[-1] is not None else None
        yield tuple(values)


def load_csv_to_raw(
    conn: psycopg.Connection,
    csv_path: Path,
    chunksize: int = 50_000,
    nrows: int | None = None,
) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe {csv_path}. Coloca data_jobs.csv en data/.")

    log.info("Cargando %s (chunksize=%s, nrows=%s)", csv_path, chunksize, nrows)
    conn.execute("TRUNCATE raw_jobs RESTART IDENTITY")

    columns_sql = ", ".join(COLUMNS)
    total = 0
    reader = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize,
        nrows=nrows,
        encoding="utf-8",
    )
    for i, chunk in enumerate(reader, start=1):
        df = validate_chunk(prepare_chunk(chunk))
        with conn.cursor() as cur, cur.copy(f"COPY raw_jobs ({columns_sql}) FROM STDIN") as copy:
            copy.set_types(COPY_TYPES)
            for row in iter_rows(df):
                copy.write_row(row)
        total += len(df)
        log.info("Bloque %d cargado (%d filas acumuladas)", i, total)

    conn.commit()
    log.info("Ingesta completada: %d filas en raw_jobs", total)
    return total
