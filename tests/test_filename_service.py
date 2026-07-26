"""Tests del servicio de nombres de archivo."""

from __future__ import annotations

from pathlib import Path

from separador_nominas.filename_service import (
    build_output_path,
    build_page_filename,
    digit_width_for_pages,
    get_available_path,
    sanitize_base_name,
    suggest_base_name_from_pdf,
    suggest_output_directory,
)


class TestDigitWidth:
    def test_single_digit_for_few_pages(self) -> None:
        assert digit_width_for_pages(1) == 1
        assert digit_width_for_pages(9) == 1

    def test_two_digits_up_to_99(self) -> None:
        assert digit_width_for_pages(10) == 2
        assert digit_width_for_pages(99) == 2

    def test_three_digits_from_100(self) -> None:
        assert digit_width_for_pages(100) == 3
        assert digit_width_for_pages(999) == 3

    def test_zero_or_negative_defaults_to_one(self) -> None:
        assert digit_width_for_pages(0) == 1
        assert digit_width_for_pages(-5) == 1


class TestSanitizeBaseName:
    def test_removes_invalid_windows_chars(self) -> None:
        assert sanitize_base_name('Nomina<>:"/\\|?*Test') == "Nomina_Test"

    def test_trims_spaces(self) -> None:
        assert sanitize_base_name("  Nominas Julio  ") == "Nominas_Julio"

    def test_collapses_internal_spaces(self) -> None:
        assert sanitize_base_name("Nominas   Julio") == "Nominas_Julio"

    def test_empty_after_sanitize(self) -> None:
        assert sanitize_base_name("   ") == ""
        assert sanitize_base_name("<>:\"/\\|?*") == ""

    def test_reserved_windows_name(self) -> None:
        assert sanitize_base_name("CON") == "CON_file"
        assert sanitize_base_name("nul") == "nul_file"

    def test_long_name_is_truncated(self) -> None:
        long_name = "A" * 300
        result = sanitize_base_name(long_name)
        assert len(result) <= 180
        assert result

    def test_trailing_dots_and_spaces_removed(self) -> None:
        assert sanitize_base_name("nomina... ") == "nomina"


class TestBuildPageFilename:
    def test_one_digit(self) -> None:
        assert build_page_filename("Nominas", 1, 5) == "Nominas_1.pdf"
        assert build_page_filename("Nominas", 5, 5) == "Nominas_5.pdf"

    def test_two_digits(self) -> None:
        assert build_page_filename("Nominas_Julio_2026", 4, 18) == (
            "Nominas_Julio_2026_04.pdf"
        )

    def test_three_digits(self) -> None:
        assert build_page_filename("Nomina", 7, 120) == "Nomina_007.pdf"

    def test_empty_base_uses_default(self) -> None:
        assert build_page_filename("", 1, 1) == "nomina_1.pdf"

    def test_special_chars_cleaned(self) -> None:
        name = build_page_filename("Nómina: Test", 1, 1)
        assert ":" not in name
        assert name.endswith("_1.pdf")


class TestGetAvailablePath:
    def test_returns_same_when_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "Nomina_001.pdf"
        assert get_available_path(target) == target

    def test_appends_suffix_when_exists(self, tmp_path: Path) -> None:
        existing = tmp_path / "Nomina_001.pdf"
        existing.write_bytes(b"%PDF")
        available = get_available_path(existing)
        assert available == tmp_path / "Nomina_001_2.pdf"

    def test_increments_until_free(self, tmp_path: Path) -> None:
        (tmp_path / "Nomina_001.pdf").write_bytes(b"%PDF")
        (tmp_path / "Nomina_001_2.pdf").write_bytes(b"%PDF")
        available = get_available_path(tmp_path / "Nomina_001.pdf")
        assert available == tmp_path / "Nomina_001_3.pdf"


class TestSuggestions:
    def test_suggest_base_name(self) -> None:
        assert suggest_base_name_from_pdf("C:/x/Nominas_Julio_2026.pdf") == (
            "Nominas_Julio_2026"
        )

    def test_suggest_output_directory(self) -> None:
        path = Path("C:/Nominas/Nominas_Julio_2026.pdf")
        suggested = suggest_output_directory(path)
        assert suggested.name == "Nominas_Julio_2026_separadas"
        assert suggested.parent == path.parent

    def test_build_output_path_avoids_overwrite(self, tmp_path: Path) -> None:
        existing = tmp_path / "base_1.pdf"
        existing.write_bytes(b"%PDF")
        result = build_output_path(tmp_path, "base", 1, 1, avoid_overwrite=True)
        assert result == tmp_path / "base_1_2.pdf"
