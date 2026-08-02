"""Casos E2E de validación para la beta 2.5.0 (Excel departamentos)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from pypdf import PdfReader

from separador_nominas.department_assignment_service import (
    apply_spreadsheet_to_session,
)
from separador_nominas.department_normalization import to_department_key
from separador_nominas.group_export_service import export_classification_session
from separador_nominas.session_service import SessionService
from separador_nominas.spreadsheet_models import SpreadsheetClassificationState
from separador_nominas.spreadsheet_service import import_department_assignments
from separador_nominas.worker_recognition_service import analyze_classification_pdf
from tests.pdf_fixtures import write_text_pdf
from tests.spreadsheet_fixtures import write_xls, write_xlsx


def _page(name: str, dni: str) -> list[str]:
    return [f"NOMBRE Y APELLIDOS: {name}", f"DNI: {dni}"]


def test_e2e_xlsx_export_page_order(tmp_path: Path) -> None:
    """Cruce xlsx + export conjunta: páginas en orden global del PDF."""
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _page("Ana", "11111111H"),
            _page("Juan", "22222222J"),
            _page("Luis", "33333333P"),
            _page("Ana", "11111111H"),
        ],
    )
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI/NIE", "Departamento"],
            ["11111111H", "Almacén"],
            ["22222222J", "Almacén"],
            ["33333333P", "Administración"],
        ],
    )

    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    applied = apply_spreadsheet_to_session(session, imported)

    assert applied.summary.matched_workers == 3
    assert applied.groups_created == 2

    dest = tmp_path / "out"
    export_classification_session(
        session, dest, unclassified_mode="combined_folder"
    )

    almacen = next(
        p
        for p in dest.iterdir()
        if p.is_dir() and to_department_key(p.name) == "almacen"
    )
    combined = next(almacen.glob("Nominas_*.pdf"))
    assert len(PdfReader(str(combined)).pages) == 3


def test_e2e_xls_import_and_match(tmp_path: Path) -> None:
    """Mismo flujo con libro .xls (xlrd)."""
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _page("Ana", "11111111H"),
            _page("Juan", "22222222J"),
            ["SIN DOCUMENTO"],
        ],
    )
    try:
        xls = write_xls(
            tmp_path / "deps.xls",
            [
                ["DNI", "Departamento"],
                ["11111111H", "Almacén"],
                ["22222222J", "Producción"],
                ["99999999R", "Dirección"],
            ],
        )
    except ImportError:
        pytest.skip("xlwt no disponible para generar .xls de prueba")

    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xls)
    applied = apply_spreadsheet_to_session(session, imported)

    assert applied.summary.matched_workers == 2
    assert applied.summary.unmatched_spreadsheet_rows == 1
    assert applied.groups_created == 2

    dest = tmp_path / "out"
    export_classification_session(
        session, dest, unclassified_mode="combined_folder"
    )
    assert (dest / "No_clasificadas" / "Nominas_no_clasificadas.pdf").exists()


def test_duplicate_same_department_single_assignment(tmp_path: Path) -> None:
    """Dos filas Excel mismo DNI y mismo depto → una asignación + aviso."""
    pdf = write_text_pdf(tmp_path / "src.pdf", [_page("Ana", "12345678Z")])
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["12345678Z", "Almacén"],
        ],
    )
    imported = import_department_assignments(xlsx)
    assert len(imported.assignments) == 1
    assert any(
        w.issue_code == "duplicate_same_department" for w in imported.warnings
    )

    session = analyze_classification_pdf(pdf)
    applied = apply_spreadsheet_to_session(session, imported)
    assert applied.workers_assigned == 1
    assert applied.summary.conflicts_pending == 0


def test_conflict_no_auto_assignment(tmp_path: Path) -> None:
    """Conflicto de departamentos: sin asignación automática."""
    pdf = write_text_pdf(tmp_path / "src.pdf", [_page("Ana", "12345678Z")])
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["12345678Z", "Producción"],
        ],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    applied = apply_spreadsheet_to_session(session, imported)

    assert imported.conflicts
    assert applied.workers_assigned == 0
    assert applied.summary.conflicts_pending == 1
    assert applied.unresolved_conflicts


def test_no_match_pdf_excel_and_missing_dni(tmp_path: Path) -> None:
    """Sin coincidencia PDF↔Excel y páginas sin DNI van a no clasificadas."""
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _page("Ana", "11111111H"),
            ["SIN DOCUMENTO"],
        ],
    )
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI", "Departamento"],
            ["22222222J", "Almacén"],
        ],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    applied = apply_spreadsheet_to_session(session, imported)

    assert applied.summary.matched_workers == 0
    assert applied.summary.unmatched_spreadsheet_rows == 1
    assert applied.summary.unmatched_pdf_workers >= 1

    dest = tmp_path / "out"
    export_classification_session(
        session, dest, unclassified_mode="combined_folder"
    )
    unclassified = dest / "No_clasificadas" / "Nominas_no_clasificadas.pdf"
    assert unclassified.exists()
    assert len(PdfReader(str(unclassified)).pages) == 2


def test_clear_session_empties_spreadsheet_state(tmp_path: Path) -> None:
    """Tras clear_session no queda estado Excel en memoria."""
    pdf = write_text_pdf(tmp_path / "src.pdf", [_page("Ana", "12345678Z")])
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [["DNI", "Departamento"], ["12345678Z", "Almacén"]],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)
    apply_spreadsheet_to_session(session, imported)

    service = SessionService()
    service.set_session(session)
    service.set_spreadsheet_state(
        SpreadsheetClassificationState(
            source_spreadsheet=xlsx,
            sheet_name="Hoja1",
            import_result=imported,
        )
    )
    assert service.has_session()
    assert service.spreadsheet_state is not None

    service.clear_session()
    assert not service.has_session()
    assert service.spreadsheet_state is None
    assert service.session is None


def test_match_logs_omit_department_and_dni(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Logs del cruce no incluyen DNI ni nombres de departamento."""
    pdf = write_text_pdf(tmp_path / "src.pdf", [_page("Ana", "12345678Z")])
    xlsx = write_xlsx(
        tmp_path / "deps.xlsx",
        [["DNI", "Departamento"], ["12345678Z", "Almacén Norte"]],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(xlsx)

    with caplog.at_level(logging.INFO, logger="separador_nominas"):
        apply_spreadsheet_to_session(session, imported)

    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "12345678Z" not in joined
    assert "Almacén Norte" not in joined
    assert "Almacen Norte" not in joined
