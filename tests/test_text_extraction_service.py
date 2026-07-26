"""Tests del servicio de extracción de texto PDF."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from separador_nominas.exceptions import EmptyPdfError, PdfNotFoundError
from separador_nominas.text_extraction_service import (
    extract_text_from_page,
    extract_texts_from_pdf,
)
from tests.pdf_fixtures import write_text_pdf


class TestExtractTextsFromPdf:
    def test_extracts_labeled_text(self, tmp_path: Path) -> None:
        source = write_text_pdf(
            tmp_path / "con_texto.pdf",
            [["TRABAJADOR: Persona Ejemplo Uno", "Periodo: 2026-01"]],
        )
        texts = extract_texts_from_pdf(source)

        assert len(texts) == 1
        assert "TRABAJADOR" in texts[0]
        assert "Persona Ejemplo Uno" in texts[0]

    def test_blank_page_returns_empty_string(self, tmp_path: Path) -> None:
        source = write_text_pdf(tmp_path / "vacio.pdf", [[]])
        texts = extract_texts_from_pdf(source)

        assert texts == ("",)

    def test_multiple_pages_order(self, tmp_path: Path) -> None:
        source = write_text_pdf(
            tmp_path / "varios.pdf",
            [
                ["Pagina Alfa"],
                ["Pagina Beta"],
                [],
            ],
        )
        texts = extract_texts_from_pdf(source)

        assert len(texts) == 3
        assert "Alfa" in texts[0]
        assert "Beta" in texts[1]
        assert texts[2] == ""

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PdfNotFoundError):
            extract_texts_from_pdf(tmp_path / "no_existe.pdf")

    def test_empty_pdf_raises(self, tmp_path: Path) -> None:
        empty = tmp_path / "sin_paginas.pdf"
        writer = PdfWriter()
        with empty.open("wb") as handle:
            writer.write(handle)

        with pytest.raises(EmptyPdfError):
            extract_texts_from_pdf(empty)


class TestExtractTextFromPage:
    def test_page_helper_with_blank(self, tmp_path: Path) -> None:
        source = write_text_pdf(tmp_path / "blank.pdf", [[]])
        from pypdf import PdfReader

        page = PdfReader(str(source)).pages[0]
        assert extract_text_from_page(page) == ""
