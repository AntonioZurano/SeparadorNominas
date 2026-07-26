"""Tests de validaciones."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from separador_nominas.exceptions import (
    CorruptedPdfError,
    DestinationNotSelectedError,
    EmptyBaseNameError,
    EmptyPdfError,
    InvalidDestinationError,
    InvalidPdfExtensionError,
    PdfNotFoundError,
    PdfNotSelectedError,
)
from separador_nominas.validators import (
    get_pdf_page_count,
    validate_base_name,
    validate_destination_dir,
    validate_pdf_path,
)


def _write_blank_pdf(path: Path, pages: int = 1) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


class TestValidatePdfPath:
    def test_none_raises(self) -> None:
        with pytest.raises(PdfNotSelectedError):
            validate_pdf_path(None)

    def test_empty_raises(self) -> None:
        with pytest.raises(PdfNotSelectedError):
            validate_pdf_path("  ")

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PdfNotFoundError):
            validate_pdf_path(tmp_path / "no_existe.pdf")

    def test_wrong_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "archivo.txt"
        path.write_text("hola", encoding="utf-8")
        with pytest.raises(InvalidPdfExtensionError):
            validate_pdf_path(path)

    def test_directory_instead_of_file(self, tmp_path: Path) -> None:
        with pytest.raises(PdfNotFoundError):
            validate_pdf_path(tmp_path)

    def test_valid_pdf(self, tmp_path: Path) -> None:
        pdf = _write_blank_pdf(tmp_path / "ok.pdf", pages=2)
        result = validate_pdf_path(pdf)
        assert result == pdf.resolve()
        assert get_pdf_page_count(pdf) == 2

    def test_corrupted_pdf(self, tmp_path: Path) -> None:
        bad = tmp_path / "roto.pdf"
        bad.write_text("esto no es un pdf", encoding="utf-8")
        with pytest.raises(CorruptedPdfError):
            validate_pdf_path(bad)

    def test_empty_pdf(self, tmp_path: Path) -> None:
        path = tmp_path / "vacio.pdf"
        writer = PdfWriter()
        with path.open("wb") as handle:
            writer.write(handle)
        with pytest.raises(EmptyPdfError):
            validate_pdf_path(path)


class TestValidateDestination:
    def test_not_selected(self) -> None:
        with pytest.raises(DestinationNotSelectedError):
            validate_destination_dir(None)

    def test_existing_dir(self, tmp_path: Path) -> None:
        result = validate_destination_dir(tmp_path)
        assert result == tmp_path.resolve()

    def test_missing_without_create(self, tmp_path: Path) -> None:
        missing = tmp_path / "nueva"
        with pytest.raises(InvalidDestinationError):
            validate_destination_dir(missing, create_if_missing=False)

    def test_missing_with_create(self, tmp_path: Path) -> None:
        missing = tmp_path / "nueva"
        result = validate_destination_dir(missing, create_if_missing=True)
        assert result.exists()
        assert result.is_dir()

    def test_file_as_destination(self, tmp_path: Path) -> None:
        file_path = tmp_path / "archivo.txt"
        file_path.write_text("x", encoding="utf-8")
        with pytest.raises(InvalidDestinationError):
            validate_destination_dir(file_path)


class TestValidateBaseName:
    def test_empty(self) -> None:
        with pytest.raises(EmptyBaseNameError):
            validate_base_name("")
        with pytest.raises(EmptyBaseNameError):
            validate_base_name("   ")

    def test_only_invalid_chars(self) -> None:
        with pytest.raises(EmptyBaseNameError):
            validate_base_name("<>:\"/\\|?*")

    def test_valid(self) -> None:
        assert validate_base_name("  Nominas Julio  ") == "Nominas_Julio"
