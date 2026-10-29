"""Funciones puras de parseo y limpieza."""

from __future__ import annotations

import ast
import logging
import math
import re
from typing import Any

log = logging.getLogger(__name__)

_WS = re.compile(r"\s+")
_TRUE = {"true", "t", "1", "yes", "y"}
_FALSE = {"false", "f", "0", "no", "n"}


def is_missing(value: Any) -> bool:
    """True para None, NaN, NA/NaT y textos vacíos o en blanco."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if value.__class__.__name__ in {"NAType", "NaTType"}:
        return True
    return isinstance(value, str) and value.strip() == ""


def clean_text(value: Any) -> str | None:
    """Recorta, colapsa espacios internos y convierte vacíos en None."""
    if is_missing(value):
        return None
    text = _WS.sub(" ", str(value)).strip()
    return text or None


def clean_lower(value: Any) -> str | None:
    """Como clean_text, pero en minúsculas."""
    text = clean_text(value)
    return text.lower() if text else None


def to_bool(value: Any) -> bool | None:
    """'True'/'False'/1/0/bool -> bool. Lo desconocido -> None."""
    if isinstance(value, bool):
        return value
    if is_missing(value):
        return None
    if isinstance(value, int | float):
        return bool(value) if value in (0, 1) else None
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return None


def _literal(value: Any) -> Any:
    """Evalúa de forma segura un texto con sintaxis de lista/dict de Python."""
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            log.debug("No se pudo parsear: %.80s", value)
            return None
    return value


def _clean_items(items: Any) -> list[str]:
    """Limpia cada elemento y quita duplicados conservando el orden."""
    seen: dict[str, None] = {}
    for item in items:
        text = clean_text(item)
        if text is not None:
            seen.setdefault(text, None)
    return list(seen)


def parse_list(value: Any) -> list[str] | None:
    """ "['python', 'sql']" -> ['python', 'sql']"""
    if is_missing(value):
        return None
    parsed = _literal(value)
    if not isinstance(parsed, list | tuple | set):
        return None
    return _clean_items(parsed)


def parse_dict(value: Any) -> dict[str, list[str]] | None:
    """ "{'programming': ['python']}" -> {'programming': ['python']}"""
    if is_missing(value):
        return None
    parsed = _literal(value)
    if not isinstance(parsed, dict):
        return None
    result: dict[str, list[str]] = {}
    for key, items in parsed.items():
        clean_key = clean_text(key)
        if clean_key is None:
            continue
        if isinstance(items, str):
            items = [items]
        if isinstance(items, list | tuple | set):
            result[clean_key] = _clean_items(items)
    return result
