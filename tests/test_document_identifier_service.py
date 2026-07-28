"""Tests de detección y validación de DNI/NIE."""

from __future__ import annotations

from separador_nominas.document_identifier_service import (
    extract_document_ids,
    normalize_document_id,
    pick_primary_document,
    validate_document_id,
)


def test_normalize_spaces_hyphens_and_case() -> None:
    assert normalize_document_id(" 12345678-z ") == "12345678Z"
    assert normalize_document_id("x-1234567-l") == "X1234567L"


def test_valid_dni_check_letter() -> None:
    match = validate_document_id("12345678Z")
    assert match is not None
    assert match.kind == "dni"
    assert match.format_valid is True
    assert match.check_letter_valid is True


def test_invalid_dni_check_letter() -> None:
    match = validate_document_id("12345678A")
    assert match is not None
    assert match.format_valid is True
    assert match.check_letter_valid is False


def test_invalid_format_returns_none() -> None:
    assert validate_document_id("1234") is None
    assert validate_document_id("") is None
    assert validate_document_id(None) is None


def test_nie_x_y_z() -> None:
    for value in ("X1234567L", "Y7654321G", "Z1234567R"):
        match = validate_document_id(value)
        assert match is not None
        assert match.kind == "nie"
        assert match.check_letter_valid is True


def test_extract_from_labeled_text() -> None:
    text = "NOMBRE: Ana Garcia\nDNI: 12345678Z\n"
    matches = extract_document_ids(text)
    assert len(matches) >= 1
    assert matches[0].normalized == "12345678Z"


def test_pick_primary_warns_multiple_and_bad_letter() -> None:
    matches = extract_document_ids("DNI 12345678A NIE X1234567L")
    primary, warnings = pick_primary_document(matches)
    assert primary is not None
    assert "multiple_documents" in warnings or primary.normalized in {
        "12345678A",
        "X1234567L",
    }


def test_lowercase_nie_in_text() -> None:
    matches = extract_document_ids("documento: x1234567l")
    assert any(m.normalized == "X1234567L" for m in matches)
