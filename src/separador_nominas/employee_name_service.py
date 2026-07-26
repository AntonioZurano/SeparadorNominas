"""Reconocimiento del nombre del trabajador a partir del texto de una página."""

from __future__ import annotations

from separador_nominas.name_normalization import normalize_employee_name
from separador_nominas.recognition_models import PageRecognitionResult
from separador_nominas.recognition_rules import (
    extract_candidates_from_labeled_lines,
    filter_person_candidates,
)


def recognize_page(
    *,
    page_index: int,
    page_text: str,
) -> PageRecognitionResult:
    """
    Intenta reconocer un único nombre fiable en el texto de una página.

    Política 1.1.0: solo ``confidence=high`` con exactamente un candidato válido.
    En cualquier otro caso la página queda no reconocida (``none``).
    """
    page_number = page_index + 1
    text = (page_text or "").strip()
    has_text = bool(text)

    if not has_text:
        return PageRecognitionResult(
            page_index=page_index,
            page_number=page_number,
            has_text=False,
            detected_name=None,
            display_name=None,
            normalized_key=None,
            confidence="none",
            warning_code="no_text",
        )

    raw_candidates = extract_candidates_from_labeled_lines(text)
    people = filter_person_candidates(raw_candidates)

    if not people:
        return PageRecognitionResult(
            page_index=page_index,
            page_number=page_number,
            has_text=True,
            detected_name=None,
            display_name=None,
            normalized_key=None,
            confidence="none",
            warning_code="no_candidate",
        )

    if len(people) > 1:
        return PageRecognitionResult(
            page_index=page_index,
            page_number=page_number,
            has_text=True,
            detected_name=None,
            display_name=None,
            normalized_key=None,
            confidence="none",
            warning_code="ambiguous_candidates",
        )

    detected = people[0]
    normalized = normalize_employee_name(detected)
    if normalized is None:
        return PageRecognitionResult(
            page_index=page_index,
            page_number=page_number,
            has_text=True,
            detected_name=None,
            display_name=None,
            normalized_key=None,
            confidence="none",
            warning_code="invalid_normalized_name",
        )

    return PageRecognitionResult(
        page_index=page_index,
        page_number=page_number,
        has_text=True,
        detected_name=detected,
        display_name=normalized.display_name,
        normalized_key=normalized.normalized_key,
        confidence="high",
        warning_code=None,
    )
