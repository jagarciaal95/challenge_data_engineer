"""Validación de cada chunk con Pandera antes de cargarlo."""

from __future__ import annotations

import logging

import pandas as pd
import pandera.pandas as pa

log = logging.getLogger(__name__)

VALID_SALARY_RATES = {"year", "hour", "month", "week", "day"}


def is_str(s: pd.Series) -> bool:
    return bool(s.dropna().map(lambda v: isinstance(v, str)).all())


def text(nullable: bool = True) -> pa.Column:
    # Sin dtype fijo: según la versión de pandas, el texto es object o str.
    return pa.Column(nullable=nullable, checks=pa.Check(is_str))


SCHEMA = pa.DataFrameSchema(
    {
        "job_title_short": text(),
        "job_title": text(),
        "job_location": text(),
        "job_via": text(),
        "job_schedule_type": text(),
        "job_work_from_home": pa.Column("boolean", nullable=True),
        "search_location": text(),
        "job_posted_date": pa.Column(pa.DateTime, nullable=True),
        "job_no_degree_mention": pa.Column("boolean", nullable=True),
        "job_health_insurance": pa.Column("boolean", nullable=True),
        "job_country": text(),
        "salary_rate": pa.Column(
            nullable=True,
            checks=pa.Check(lambda s: s.dropna().isin(VALID_SALARY_RATES).all()),
        ),
        "salary_year_avg": pa.Column(float, nullable=True, checks=pa.Check.ge(0)),
        "salary_hour_avg": pa.Column(float, nullable=True, checks=pa.Check.ge(0)),
        "company_name": text(),
        "job_skills": pa.Column(
            object,
            nullable=True,
            checks=pa.Check(lambda s: s.dropna().map(lambda v: isinstance(v, list)).all()),
        ),
        "job_type_skills": pa.Column(
            object,
            nullable=True,
            checks=pa.Check(lambda s: s.dropna().map(lambda v: isinstance(v, dict)).all()),
        ),
    },
    strict=True,
)


def validate_chunk(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        log.error("Validación fallida:\n%s", exc.failure_cases.head(20))
        raise
