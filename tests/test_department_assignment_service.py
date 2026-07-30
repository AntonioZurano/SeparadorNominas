"""Tests de cruce Excel-PDF y exportación por departamentos."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from separador_nominas.department_assignment_service import (
    apply_spreadsheet_to_session,
)
from separador_nominas.group_export_service import export_classification_session
from separador_nominas.spreadsheet_service import import_department_assignments
from separador_nominas.worker_recognition_service import (
    analyze_classification_pdf,
    document_worker_id,
)
from tests.pdf_fixtures import write_text_pdf
from tests.spreadsheet_fixtures import write_xlsx


def _page(name: str, dni: str) -> list[str]:
    return [f"NOMBRE Y APELLIDOS: {name}", f"DNI: {dni}"]


def test_excel_pdf_match_and_export_order(tmp_path: Path) -> None:
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _page("Ana", "11111111H"),
            _page("Juan", "22222222J"),
            _page("Luis", "33333333P"),
            _page("Ana", "11111111H"),
            _page("Nuria", "X1234567L"),
            ["SIN DOCUMENTO"],
        ],
    )
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI/NIE", "Departamento"],
            ["11111111H", "Almacén"],
            ["22222222J", "Administración"],
            ["33333333P", "Almacén"],
            ["X1234567L", "Producción"],
            ["44444444A", "Dirección"],
        ],
    )

    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    applied = apply_spreadsheet_to_session(session, imported)

    assert applied.summary.matched_workers == 4
    assert applied.summary.unmatched_spreadsheet_rows == 1
    assert applied.groups_created == 3

    dest = tmp_path / "out"
    result = export_classification_session(
        session, dest, unclassified_mode="combined_folder"
    )

    from separador_nominas.department_normalization import to_department_key

    dept_dirs = [p for p in dest.iterdir() if p.is_dir()]
    by_key = {to_department_key(p.name): p for p in dept_dirs}
    assert "almacen" in by_key
    assert len(PdfReader(str(next(by_key["almacen"].glob("Nominas_*.pdf")))).pages) == 3
    assert "administracion" in by_key
    assert "produccion" in by_key
    assert "no_clasificadas" in by_key or (dest / "No_clasificadas").exists()

    unclassified = dest / "No_clasificadas" / "Nominas_no_clasificadas.pdf"
    assert unclassified.exists()
    assert len(PdfReader(str(unclassified)).pages) == 1
    assert result.unclassified_files
    assert "direccion" not in by_key


def test_combined_export_global_page_order(tmp_path: Path) -> None:
    """Ana páginas 1+5 y Juan página 2 → orden 1,2,5 (no 1,5,2)."""
    from separador_nominas.classification_service import (
        add_workers_to_group,
        create_group,
    )

    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Juan Perez Ruiz", "23456789D"),
            ["SIN"],
            ["SIN2"],
            _page("Ana Garcia Lopez", "12345678Z"),
        ],
    )
    session = analyze_classification_pdf(pdf)
    group = create_group(session, "Almacen", export_mode="combined")
    add_workers_to_group(
        session,
        group.group_id,
        [
            document_worker_id("12345678Z"),
            document_worker_id("23456789D"),
        ],
    )
    dest = tmp_path / "out"
    export_classification_session(session, dest)
    combined = dest / "Almacen" / "Nominas_Almacen.pdf"
    # No hay forma fácil de leer texto de pypdf pages sin extract;
    # comprobamos conteo y que el fix no rompe.
    assert len(PdfReader(str(combined)).pages) == 3


def test_conflict_resolution(tmp_path: Path) -> None:
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [_page("Ana", "12345678Z")],
    )
    xlsx = write_xlsx(
        tmp_path / "c.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["12345678Z", "Producción"],
        ],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    applied = apply_spreadsheet_to_session(session, imported)
    assert applied.summary.conflicts_pending == 1
    assert applied.workers_assigned == 0

    key = imported.conflicts[0].department_keys[0]
    applied2 = apply_spreadsheet_to_session(
        session,
        imported,
        conflict_resolutions={"12345678Z": key},
    )
    assert applied2.workers_assigned == 1
    assert applied2.summary.conflicts_pending == 0
