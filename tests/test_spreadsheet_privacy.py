"""Privacidad: logs de importación Excel no incluyen datos personales."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from separador_nominas.spreadsheet_service import import_department_assignments
from tests.spreadsheet_fixtures import write_xlsx


def test_import_logs_are_aggregate_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["23456789D", "Producción"],
        ],
    )
    with caplog.at_level(logging.INFO, logger="separador_nominas"):
        import_department_assignments(path)

    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "12345678Z" not in joined
    assert "23456789D" not in joined
    assert "Almacén" not in joined
    assert "Producción" not in joined
    assert "asignaciones válidas" in joined


def test_session_cleared_after_clear_session(tmp_path: Path) -> None:
    """La sesión Excel no sobrevive a clear_session (sin persistencia)."""
    from separador_nominas.session_service import SessionService
    from separador_nominas.spreadsheet_models import SpreadsheetClassificationState
    from separador_nominas.worker_recognition_service import (
        analyze_classification_pdf,
    )
    from tests.pdf_fixtures import write_text_pdf

    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [["NOMBRE Y APELLIDOS: Ana", "DNI: 12345678Z"]],
    )
    path = write_xlsx(
        tmp_path / "deps.xlsx",
        [["DNI", "Departamento"], ["12345678Z", "Almacén"]],
    )
    session = analyze_classification_pdf(pdf)
    imported = import_department_assignments(path)

    service = SessionService()
    service.set_session(session)
    service.set_spreadsheet_state(
        SpreadsheetClassificationState(
            source_spreadsheet=path,
            sheet_name="Hoja1",
            import_result=imported,
        )
    )
    service.clear_session()
    assert service.session is None
    assert service.spreadsheet_state is None
