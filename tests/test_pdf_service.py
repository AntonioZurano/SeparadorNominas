"""Tests del servicio de separación PDF."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from separador_nominas.exceptions import (
    CorruptedPdfError,
    EmptyBaseNameError,
    PdfNotFoundError,
)
from separador_nominas.pdf_service import split_pdf


def _write_pdf(path: Path, pages: int) -> Path:
    writer = PdfWriter()
    for index in range(pages):
        writer.add_blank_page(width=300 + index, height=400)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


class TestSplitPdf:
    def test_single_page(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "uno.pdf", 1)
        dest = tmp_path / "out"
        result = split_pdf(source, dest, "Nomina")

        assert result.files_created == 1
        assert result.page_count == 1
        assert len(result.output_files) == 1
        out = result.output_files[0]
        assert out.name == "Nomina_1.pdf"
        assert out.exists()
        assert len(PdfReader(str(out)).pages) == 1

    def test_multiple_pages_order_and_count(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "varios.pdf", 5)
        dest = tmp_path / "out"
        progress: list[tuple[int, int]] = []

        def on_progress(current: int, total: int, _path: Path) -> None:
            progress.append((current, total))

        result = split_pdf(
            source, dest, "Nominas", progress_callback=on_progress
        )

        assert result.files_created == 5
        assert [p.name for p in result.output_files] == [
            "Nominas_1.pdf",
            "Nominas_2.pdf",
            "Nominas_3.pdf",
            "Nominas_4.pdf",
            "Nominas_5.pdf",
        ]
        assert progress == [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]

        for path in result.output_files:
            assert len(PdfReader(str(path)).pages) == 1

    def test_two_digit_padding(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "diez.pdf", 10)
        dest = tmp_path / "out"
        result = split_pdf(source, dest, "Doc")
        assert result.output_files[0].name == "Doc_01.pdf"
        assert result.output_files[9].name == "Doc_10.pdf"

    def test_missing_source(self, tmp_path: Path) -> None:
        with pytest.raises(PdfNotFoundError):
            split_pdf(tmp_path / "no.pdf", tmp_path / "out", "x")

    def test_corrupted_source(self, tmp_path: Path) -> None:
        bad = tmp_path / "malo.pdf"
        bad.write_text("no-pdf", encoding="utf-8")
        with pytest.raises(CorruptedPdfError):
            split_pdf(bad, tmp_path / "out", "x")

    def test_creates_destination(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "src.pdf", 2)
        dest = tmp_path / "nueva" / "sub"
        result = split_pdf(source, dest, "N")
        assert dest.exists()
        assert result.files_created == 2

    def test_existing_output_not_overwritten(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "src.pdf", 1)
        dest = tmp_path / "out"
        dest.mkdir()
        existing = dest / "N_1.pdf"
        existing.write_bytes(b"%PDF-existing")

        result = split_pdf(source, dest, "N")
        assert result.output_files[0].name == "N_1_2.pdf"
        assert existing.read_bytes() == b"%PDF-existing"
        assert result.output_files[0].exists()

    def test_empty_base_name(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "src.pdf", 1)
        with pytest.raises(EmptyBaseNameError):
            split_pdf(source, tmp_path / "out", "   ")

    def test_each_output_has_one_page(self, tmp_path: Path) -> None:
        source = _write_pdf(tmp_path / "src.pdf", 3)
        result = split_pdf(source, tmp_path / "out", "P")
        for path in result.output_files:
            reader = PdfReader(str(path))
            assert len(reader.pages) == 1
