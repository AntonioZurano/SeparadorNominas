"""Normalización de nombres de departamento (display, clave, carpeta)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from separador_nominas.filename_service import sanitize_base_name


@dataclass(frozen=True)
class NormalizedDepartment:
    """Formas normalizadas de un nombre de departamento."""

    display_name: str
    department_key: str
    safe_folder_name: str


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def to_display_name(raw: str | None) -> str | None:
    """Nombre legible: strip y colapso de espacios."""
    if raw is None:
        return None
    text = " ".join(str(raw).strip().split())
    return text or None


def to_department_key(raw: str | None) -> str | None:
    """Clave comparable: casefold, sin tildes, espacios colapsados."""
    display = to_display_name(raw)
    if display is None:
        return None
    key = _strip_accents(display).casefold()
    key = " ".join(key.split())
    return key or None


def to_safe_folder_name(raw: str | None) -> str | None:
    """Nombre de carpeta seguro para Windows."""
    display = to_display_name(raw)
    if display is None:
        return None
    safe = sanitize_base_name(display)
    return safe or None


def normalize_department(raw: str | None) -> NormalizedDepartment | None:
    """Normaliza un departamento o ``None`` si no es usable."""
    display = to_display_name(raw)
    key = to_department_key(raw)
    safe = to_safe_folder_name(raw)
    if display is None or key is None or safe is None:
        return None
    return NormalizedDepartment(
        display_name=display,
        department_key=key,
        safe_folder_name=safe,
    )
