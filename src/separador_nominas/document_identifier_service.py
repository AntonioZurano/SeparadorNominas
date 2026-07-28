"""Detección, normalización y validación de DNI y NIE españoles."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Letras de control (módulo 23).
_CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX_VALUE = {"X": 0, "Y": 1, "Z": 2}

_DOC_CANDIDATE = re.compile(
    r"(?<![A-Z0-9])([XYZ]?\d{7,8}[-\s]?[A-Z])(?![A-Z0-9])",
    re.IGNORECASE,
)
_LABEL_NEAR = re.compile(
    r"(?:D\.?\s*N\.?\s*I\.?|N\.?\s*I\.?\s*F\.?|N\.?\s*I\.?\s*E\.?|"
    r"DOCUMENTO|DOC\.?\s*IDENTIDAD)\s*[:\-]?\s*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DocumentIdMatch:
    """Candidato de documento detectado en una página."""

    normalized: str
    kind: str  # "dni" | "nie"
    format_valid: bool
    check_letter_valid: bool | None
    raw: str


def normalize_document_id(value: str | None) -> str | None:
    """Normaliza un DNI/NIE: mayúsculas, sin espacios, guiones ni puntos."""
    if value is None:
        return None
    cleaned = str(value).strip().upper()
    cleaned = cleaned.replace(" ", "").replace("-", "").replace(".", "")
    if not cleaned:
        return None
    return cleaned


def _control_letter_for_number(number: int) -> str:
    return _CONTROL_LETTERS[number % 23]


def validate_document_id(value: str | None) -> DocumentIdMatch | None:
    """
    Valida formato y, si procede, la letra de control.

    Returns:
        ``DocumentIdMatch`` o ``None`` si el valor no tiene forma de DNI/NIE.
    """
    normalized = normalize_document_id(value)
    if normalized is None:
        return None

    if re.fullmatch(r"\d{8}[A-Z]", normalized):
        number = int(normalized[:8])
        expected = _control_letter_for_number(number)
        letter_ok = normalized[8] == expected
        return DocumentIdMatch(
            normalized=normalized,
            kind="dni",
            format_valid=True,
            check_letter_valid=letter_ok,
            raw=str(value),
        )

    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", normalized):
        prefix = normalized[0]
        number = _NIE_PREFIX_VALUE[prefix] * 10_000_000 + int(normalized[1:8])
        expected = _control_letter_for_number(number)
        letter_ok = normalized[8] == expected
        return DocumentIdMatch(
            normalized=normalized,
            kind="nie",
            format_valid=True,
            check_letter_valid=letter_ok,
            raw=str(value),
        )

    return None


def _is_likely_company_cif(normalized: str) -> bool:
    """Heurística ligera: CIF empieza por letra de sociedad + 7 dígitos + control."""
    return bool(re.fullmatch(r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]", normalized))


def extract_document_ids(page_text: str) -> tuple[DocumentIdMatch, ...]:
    """
    Extrae candidatos DNI/NIE del texto de una página.

    Prioriza coincidencias cercanas a etiquetas conocidas. No registra valores.
    """
    text = page_text or ""
    if not text.strip():
        return ()

    labeled_hits: list[DocumentIdMatch] = []
    other_hits: list[DocumentIdMatch] = []
    seen: set[str] = set()

    for match in _DOC_CANDIDATE.finditer(text):
        raw = match.group(1)
        validated = validate_document_id(raw)
        if validated is None:
            continue
        if _is_likely_company_cif(validated.normalized):
            continue
        if validated.normalized in seen:
            continue
        seen.add(validated.normalized)

        start = max(0, match.start() - 40)
        prefix = text[start : match.start()]
        if _LABEL_NEAR.search(prefix):
            labeled_hits.append(validated)
        else:
            other_hits.append(validated)

    ordered = labeled_hits + other_hits
    return tuple(ordered)


def pick_primary_document(
    matches: tuple[DocumentIdMatch, ...],
) -> tuple[DocumentIdMatch | None, list[str]]:
    """
    Elige el documento principal de la página y genera códigos de advertencia.

    Preferencia: primer candidato con letra válida; si no, el primero con formato.
    """
    warnings: list[str] = []
    if not matches:
        return None, warnings

    if len(matches) > 1:
        warnings.append("multiple_documents")

    preferred = next(
        (item for item in matches if item.check_letter_valid is True),
        matches[0],
    )
    if preferred.check_letter_valid is False:
        warnings.append("invalid_check_letter")
    return preferred, warnings
