"""Normalización de nombres de trabajador para UI, agrupación y archivos."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from separador_nominas.filename_service import sanitize_base_name


@dataclass(frozen=True)
class NormalizedEmployeeName:
    """Tres representaciones del nombre de un trabajador."""

    display_name: str
    normalized_key: str
    safe_filename_stem: str


_MULTI_SPACE = re.compile(r"\s+")
_KEY_ALLOWED = re.compile(r"[^a-z\s]")


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def to_display_name(raw_name: str) -> str:
    """Convierte un nombre detectado a Title Case razonable para la UI."""
    cleaned = _MULTI_SPACE.sub(" ", raw_name.strip())
    if not cleaned:
        return ""
    return cleaned.title()


def to_normalized_key(raw_name: str) -> str:
    """
    Clave exacta de agrupación: minúsculas, sin acentos, solo letras y espacios.
    """
    cleaned = _MULTI_SPACE.sub(" ", raw_name.strip())
    if not cleaned:
        return ""
    without_accents = _strip_accents(cleaned).lower()
    key = _KEY_ALLOWED.sub("", without_accents)
    return _MULTI_SPACE.sub(" ", key).strip()


def to_safe_filename_stem(raw_name: str) -> str:
    """Nombre de archivo seguro reutilizando el saneamiento de Windows."""
    display = to_display_name(raw_name) or raw_name
    sanitized = sanitize_base_name(display.replace(" ", "_"))
    return sanitized


def normalize_employee_name(raw_name: str) -> NormalizedEmployeeName | None:
    """
    Normaliza un nombre bruto.

    Returns:
        ``NormalizedEmployeeName`` o ``None`` si no hay clave útil.
    """
    if raw_name is None:
        return None
    raw = str(raw_name).strip()
    if not raw:
        return None

    key = to_normalized_key(raw)
    if not key:
        return None

    display = to_display_name(raw)
    stem = to_safe_filename_stem(raw)
    if not stem:
        return None

    return NormalizedEmployeeName(
        display_name=display,
        normalized_key=key,
        safe_filename_stem=stem,
    )
