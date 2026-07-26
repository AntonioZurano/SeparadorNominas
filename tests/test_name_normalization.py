"""Tests de normalización de nombres de trabajador."""

from __future__ import annotations

from separador_nominas.name_normalization import (
    normalize_employee_name,
    to_normalized_key,
)


class TestNameNormalization:
    def test_accent_and_case_equivalence(self) -> None:
        a = normalize_employee_name("ANTONIO ZURANO BLÁZQUEZ")
        b = normalize_employee_name("Antonio Zurano Blázquez")
        c = normalize_employee_name("antonio   zurano   blazquez")

        assert a is not None and b is not None and c is not None
        assert a.normalized_key == b.normalized_key == c.normalized_key
        assert a.normalized_key == "antonio zurano blazquez"

    def test_display_title_case(self) -> None:
        result = normalize_employee_name("MARIA LOPEZ SANCHEZ")
        assert result is not None
        assert result.display_name == "Maria Lopez Sanchez"

    def test_safe_filename_stem(self) -> None:
        result = normalize_employee_name("Ana Pérez García")
        assert result is not None
        assert " " not in result.safe_filename_stem
        assert result.safe_filename_stem

    def test_empty_returns_none(self) -> None:
        assert normalize_employee_name("   ") is None
        assert to_normalized_key("") == ""

    def test_punctuation_stripped_from_key(self) -> None:
        key = to_normalized_key("Juan, Pérez.")
        assert key == "juan perez"
