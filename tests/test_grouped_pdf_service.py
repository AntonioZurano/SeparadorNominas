"""Tests de análisis y escritura de PDFs agrupados."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from separador_nominas.constants import UNRECOGNIZED_FOLDER_NAME
from separador_nominas.grouped_pdf_service import (
    analyze_payroll_pdf,
    write_grouped_pdfs,
)
from tests.pdf_fixtures import write_text_pdf


def _sample_payroll_pdf(path: Path) -> Path:
    """PDF sintético: Ana×2, Pedro×2, Laura×1, vacía×1."""
    return write_text_pdf(
        path,
        [
            ["TRABAJADOR: Ana Perez Garcia", "Nomina ordinaria"],
            ["TRABAJADOR: Pedro Ruiz Martin", "Nomina ordinaria"],
            ["TRABAJADOR: Ana Perez Garcia", "Paga extra"],
            ["TRABAJADOR: Pedro Ruiz Martin", "Paga extra"],
            ["EMPLEADO: Laura Gomez Diaz"],
            [],
        ],
    )


class TestGroupedPdfService:
    def test_analyze_and_write_integration(self, tmp_path: Path) -> None:
        source = _sample_payroll_pdf(tmp_path / "nominas.pdf")
        analysis = analyze_payroll_pdf(source)

        assert analysis.page_count == 6
        assert len(analysis.groups) == 3
        assert analysis.unrecognized_page_numbers == (6,)

        by_key = {g.normalized_key: g for g in analysis.groups}
        assert by_key["ana perez garcia"].page_numbers == (1, 3)
        assert by_key["pedro ruiz martin"].page_numbers == (2, 4)
        assert by_key["laura gomez diaz"].page_numbers == (5,)

        dest = tmp_path / "salida"
        result = write_grouped_pdfs(analysis, dest)

        assert result.recognized_worker_count == 3
        assert len(result.output_files) == 3
        assert len(result.unrecognized_files) == 1
        assert result.unrecognized_files[0].parent.name == UNRECOGNIZED_FOLDER_NAME
        assert result.unrecognized_files[0].name == "Pagina_6.pdf"

        ana = next(p for p in result.output_files if "Ana" in p.name)
        assert len(PdfReader(str(ana)).pages) == 2

    def test_collision_avoids_overwrite(self, tmp_path: Path) -> None:
        source = write_text_pdf(
            tmp_path / "uno.pdf",
            [["TRABAJADOR: Ana Perez Garcia"]],
        )
        analysis = analyze_payroll_pdf(source)
        dest = tmp_path / "out"
        first = write_grouped_pdfs(analysis, dest)
        second = write_grouped_pdfs(analysis, dest)

        assert first.output_files[0].exists()
        assert second.output_files[0].exists()
        assert first.output_files[0] != second.output_files[0]
        assert second.output_files[0].stem.endswith("_2")
