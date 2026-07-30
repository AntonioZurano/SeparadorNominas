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
