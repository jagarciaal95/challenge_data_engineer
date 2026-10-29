"""CSV crudo -> DataFrame tipado con las columnas de raw_jobs."""
from __future__ import annotations
import pandas as pd
from pipeline.parsing import clean_lower, clean_text, parse_dict, parse_list, to_bool


COLUMNS = [
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "job_work_from_home",
    "search_location",
    "job_posted_date",
    "job_no_degree_mention",
    "job_health_insurance",
    "job_country",
    "salary_rate",
    "salary_year_avg",
    "salary_hour_avg",
    "company_name",
    "job_skills",
    "job_type_skills",
]
TEXT_COLS = [
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "search_location",
    "job_country",
    "company_name",
]
BOOL_COLS = ["job_work_from_home", "job_no_degree_mention", "job_health_insurance"]
NUM_COLS = ["salary_year_avg", "salary_hour_avg"]


def prepare_chunk(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Columnas ausentes en el CSV: {missing}")

    out = pd.DataFrame(index=df.index)
    for col in TEXT_COLS:
        out[col] = df[col].map(clean_text)
    for col in BOOL_COLS:
        out[col] = df[col].map(to_bool).astype("boolean")
    out["job_posted_date"] = pd.to_datetime(df["job_posted_date"], errors="coerce")
    for col in NUM_COLS:
        out[col] = pd.to_numeric(df[col], errors="coerce")
    out["salary_rate"] = df["salary_rate"].map(clean_lower)
    out["job_skills"] = df["job_skills"].map(parse_list)
    out["job_type_skills"] = df["job_type_skills"].map(parse_dict)
    return out[COLUMNS]