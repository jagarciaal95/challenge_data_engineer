import pandas as pd
import pandera.pandas as pa
import pytest

from pipeline.clean import COLUMNS, prepare_chunk
from pipeline.ingest import iter_rows
from pipeline.validate import validate_chunk


def _fila(**cambios) -> pd.DataFrame:
    fila = {
        "job_title_short": "Data Scientist",
        "job_title": "  Senior   Data Scientist ",
        "job_location": "Bogota, Colombia",
        "job_via": "via LinkedIn",
        "job_schedule_type": "Full-time",
        "job_work_from_home": "False",
        "search_location": "Colombia",
        "job_posted_date": "2023-03-01 10:15:00",
        "job_no_degree_mention": "True",
        "job_health_insurance": "False",
        "job_country": "Colombia",
        "salary_rate": "Year",
        "salary_year_avg": "100000.0",
        "salary_hour_avg": "",
        "company_name": " Acme ",
        "job_skills": "['python', 'sql']",
        "job_type_skills": "{'programming': ['python', 'sql']}",
    }
    fila.update(cambios)
    return pd.DataFrame([fila])


def test_prepare_chunk_tipos_y_limpieza():
    out = prepare_chunk(_fila())
    assert list(out.columns) == COLUMNS
    r = out.iloc[0]
    assert r["job_title"] == "Senior Data Scientist"
    assert r["company_name"] == "Acme"
    assert r["salary_rate"] == "year"
    assert r["job_skills"] == ["python", "sql"]
    assert r["job_type_skills"] == {"programming": ["python", "sql"]}
    assert pd.isna(r["salary_hour_avg"])


def test_prepare_chunk_columna_ausente():
    with pytest.raises(ValueError, match="Columnas ausentes"):
        prepare_chunk(_fila().drop(columns=["job_skills"]))


def test_validate_acepta_bloque_limpio():
    validate_chunk(prepare_chunk(_fila()))


def test_validate_rechaza_salario_negativo():
    with pytest.raises(pa.errors.SchemaErrors):
        validate_chunk(prepare_chunk(_fila(salary_year_avg="-5")))


def test_validate_rechaza_salary_rate_desconocido():
    with pytest.raises(pa.errors.SchemaErrors):
        validate_chunk(prepare_chunk(_fila(salary_rate="decada")))


def test_validate_acepta_titulo_vacio():
    # Decisión de diseño: raw conserva la fila; la capa 3NF la excluye
    validate_chunk(prepare_chunk(_fila(job_title="")))


def test_iter_rows_convierte_vacios_a_none():
    df = prepare_chunk(_fila(job_skills="", job_type_skills=""))
    (fila,) = list(iter_rows(df))
    assert len(fila) == len(COLUMNS)
    assert fila[-2] is None and fila[-1] is None
    assert fila[13] is None  # salary_hour_avg
