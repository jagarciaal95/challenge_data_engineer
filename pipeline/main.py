"""CLI: python -m pipeline.main {ingest,transform,all} [--csv RUTA]"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.config import ROOT, load_settings
from pipeline.db import connect, create_tables
from pipeline.ingest import load_csv_to_raw
from pipeline.logging_config import setup_logging
from pipeline.transform import transform_to_3nf

log = logging.getLogger("pipeline")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("ingest", "CSV -> raw_jobs"),
        ("transform", "raw_jobs -> modelo 3NF"),
        ("all", "ingesta + transformación"),
    ):
        p = sub.add_parser(name, help=helptext)
        if name != "transform":
            p.add_argument("--csv", type=Path, default=ROOT / "data" / "data_jobs.csv")
            p.add_argument("--chunksize", type=int, default=50_000)
            p.add_argument("--nrows", type=int, default=None, help="Limitar filas (pruebas)")
    return parser


def main(argv: list[str] | None = None) -> None:
    setup_logging()
    args = build_parser().parse_args(argv)
    settings = load_settings()

    with connect(settings) as conn:
        create_tables(conn)
        if args.command in ("ingest", "all"):
            load_csv_to_raw(conn, args.csv, args.chunksize, args.nrows)
        if args.command in ("transform", "all"):
            transform_to_3nf(conn)
    log.info("Pipeline finalizado")


if __name__ == "__main__":
    main()
