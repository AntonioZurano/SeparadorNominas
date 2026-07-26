"""Reglas locales de reconocimiento de nombres en texto de nóminas."""

from __future__ import annotations

import re

from separador_nominas.constants import EMPLOYEE_NAME_LABELS

# Fragmentos que suelen indicar empresa, conceptos o ruido (no persona).
NEGATIVE_NAME_FRAGMENTS: tuple[str, ...] = (
    "S.L.",
    "S.A.",
    "S.L.U.",
    "S.COOP",
    "SOCIEDAD",
    "EMPRESA",
    "CIF",
    "NIF",
    "NIE",
    "NOMINA",
    "NÓMINA",
    "SEGURIDAD SOCIAL",
    "IBAN",
    "CCC",
    "BANCO",
    "CAIXA",
    "CATEGORIA",
    "CATEGORÍA",
    "CONVENIO",
    "DOMICILIO",
    "CALLE",
    "AVENIDA",
    "PLAZA",
    "C/",
    "AVDA",
    "TOTAL",
    "LIQUIDO",
    "LÍQUIDO",
    "DEVENGOS",
    "DEDUCCIONES",
)

# Letras usadas para límites de token (evita NIE ⊂ NIETO, CIF ⊂ …).
_LETTER_CLASS = "A-ZÁÉÍÓÚÜÑ"


def _negative_fragment_pattern(fragment: str) -> re.Pattern[str]:
    """Compila un patrón que exige el fragmento como token, no como subcadena."""
    escaped = re.escape(fragment.upper())
    return re.compile(
        rf"(?<![{_LETTER_CLASS}]){escaped}(?![{_LETTER_CLASS}])",
        re.IGNORECASE,
    )


_NEGATIVE_FRAGMENT_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    _negative_fragment_pattern(fragment) for fragment in NEGATIVE_NAME_FRAGMENTS
)

_LABEL_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}

# Nombre candidato: 2 a 5 palabras con letras (permite acentos y guiones simples).
_NAME_CANDIDATE = re.compile(
    r"^[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑa-záéíóúüñ'-]+"
    r"(?:\s+[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑa-záéíóúüñ'-]+){1,4}$"
)


def _label_pattern(label: str) -> re.Pattern[str]:
    cached = _LABEL_PATTERN_CACHE.get(label)
    if cached is not None:
        return cached
    escaped = re.escape(label)
    pattern = re.compile(
        rf"(?im)^\s*{escaped}\s*[:\-]?\s*(.*)$"
    )
    _LABEL_PATTERN_CACHE[label] = pattern
    return pattern


def split_text_lines(text: str) -> list[str]:
    """Divide el texto extraído en líneas no vacías."""
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def looks_like_person_name(candidate: str) -> bool:
    """Valida forma tipográfica básica de un nombre de persona."""
    cleaned = re.sub(r"\s+", " ", candidate.strip())
    if len(cleaned) < 5 or len(cleaned) > 80:
        return False
    if any(char.isdigit() for char in cleaned):
        return False
    return bool(_NAME_CANDIDATE.match(cleaned))


def contains_negative_fragment(candidate: str) -> bool:
    """
    True si el candidato parece empresa, concepto o ruido.

    Los fragmentos se buscan como tokens (no subcadenas), de modo que
    ``NIE`` no rechaza el apellido ``Nieto``.
    """
    return any(pattern.search(candidate) for pattern in _NEGATIVE_FRAGMENT_PATTERNS)


def extract_candidates_from_labeled_lines(text: str) -> list[str]:
    """
    Busca candidatos tras etiquetas conocidas (misma línea o siguiente).

    Respeta el orden de ``EMPLOYEE_NAME_LABELS``.
    """
    lines = split_text_lines(text)
    if not lines:
        return []

    candidates: list[str] = []
    upper_lines = [line.upper() for line in lines]

    for label in EMPLOYEE_NAME_LABELS:
        pattern = _label_pattern(label)
        for index, line in enumerate(lines):
            match = pattern.match(line)
            if match is None:
                # Etiqueta sola en la línea → mirar la siguiente.
                if upper_lines[index].rstrip(":").strip() == label:
                    if index + 1 < len(lines):
                        nxt = lines[index + 1].strip()
                        if nxt and not contains_negative_fragment(nxt):
                            candidates.append(nxt)
                    continue
                continue

            same_line = match.group(1).strip()
            if same_line:
                candidates.append(same_line)
            elif index + 1 < len(lines):
                nxt = lines[index + 1].strip()
                if nxt:
                    candidates.append(nxt)

        if candidates:
            break

    return candidates


def filter_person_candidates(candidates: list[str]) -> list[str]:
    """Filtra candidatos válidos de persona y elimina duplicados preservando orden."""
    accepted: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        cleaned = re.sub(r"\s+", " ", raw.strip())
        if not cleaned or contains_negative_fragment(cleaned):
            continue
        if not looks_like_person_name(cleaned):
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        accepted.append(cleaned)
    return accepted
