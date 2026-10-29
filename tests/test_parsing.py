import math

import pandas as pd
import pytest

from pipeline.parsing import clean_lower, clean_text, parse_dict, parse_list, to_bool


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Acme   Corp ", "Acme Corp"),
        ("", None),
        ("   ", None),
        (None, None),
        (math.nan, None),
        (pd.NA, None),
    ],
)
def test_clean_text(value, expected):
    assert clean_text(value) == expected


def test_clean_lower():
    assert clean_lower(" Year ") == "year"
    assert clean_lower("") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("True", True),
        ("false", False),
        (True, True),
        (1, True),
        (0, False),
        ("", None),
        (None, None),
        ("quizás", None),
        (2, None),
    ],
)
def test_to_bool(value, expected):
    assert to_bool(value) is expected


def test_parse_list_valida_y_sin_duplicados():
    assert parse_list("['python', ' sql ', 'python', '']") == ["python", "sql"]


def test_parse_list_vacia_y_ausente():
    assert parse_list("[]") == []
    assert parse_list("") is None
    assert parse_list(None) is None
    assert parse_list(math.nan) is None


@pytest.mark.parametrize("malo", ["[sin cerrar", "{'a': 1}", "'solo texto'", "42"])
def test_parse_list_invalida_devuelve_none(malo):
    assert parse_list(malo) is None


def test_parse_list_no_ejecuta_codigo():
    # ast.literal_eval rechaza expresiones; eval() las ejecutaría
    assert parse_list("__import__('os').getcwd()") is None


def test_parse_dict_valido():
    crudo = "{'programming': ['python', 'sql'], 'databases': ['postgresql']}"
    assert parse_dict(crudo) == {
        "programming": ["python", "sql"],
        "databases": ["postgresql"],
    }


def test_parse_dict_valor_suelto_e_invalido():
    assert parse_dict("{'cloud': 'aws'}") == {"cloud": ["aws"]}
    assert parse_dict("['no', 'es', 'dict']") is None
    assert parse_dict("{roto") is None
    assert parse_dict(None) is None