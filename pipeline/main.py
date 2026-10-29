from __future__ import annotations
import argparse
import logging
from pathlib import Path
from pipeline.config import ROOT, load_settings
from pipeline.db import connect, create_raw_table
from pipeline.ingest import load_csv_to_raw
from pipeline.logging_config import setup_logging

log = logging.getLogger("pipeline")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="CSV -> raw_jobs")
    p.add_argument("--csv", type=Path, default=ROOT / "data" / "data_jobs.csv")
    p.add_argument("--chunksize", type=int, default=50_000)
    p.add_argument("--nrows", type=int, default=None, help="Limitar filas (para pruebas)")
    return parser


def main(argv: list[str] | None = None) -> None:
    setup_logging()
    args = build_parser().parse_args(argv)
    settings = load_settings()

    with connect(settings) as conn:
        create_raw_table(conn)
        if args.command == "ingest":
            load_csv_to_raw(conn, args.csv, args.chunksize, args.nrows)
    log.info("Pipeline finalizado")


if __name__ == "__main__":
    main()