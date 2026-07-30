"""Tests de lectura e importación de Excel."""

from __future__ import annotations

from pathlib import Path

import pytest

from separador_nominas.exceptions import (
    InvalidSpreadsheetExtensionError,
    SpreadsheetEmptyError,
    SpreadsheetNotFoundError,
)
from separador_nominas.spreadsheet_service import (
    cell_value_to_document_text,
    detect_column_mapping,
    import_department_assignments,
    list_sheet_names,
    validate_spreadsheet_path,
)
from tests.spreadsheet_fixtures import write_xls, write_xlsx


def test_validate_path_extension(tmp_path: Path) -> None:
    bad = tmp_path / "datos.csv"
    bad.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(InvalidSpreadsheetExtensionError):
        validate_spreadsheet_path(bad)
    with pytest.raises(SpreadsheetNotFoundError):
        validate_spreadsheet_path(tmp_path / "noexiste.xlsx")


def test_import_xlsx_with_headers(tmp_path: Path) -> None:
    path = write_xlsx(
        tmp_path / "deps.xlsx",
        [
            ["DNI/NIE", "Departamento"],
            ["12345678Z", "Almacén"],
            ["23456789D", "Administración"],
            ["12345678Z", "Almacén"],  # duplicado mismo depto
        ],
    )
    result = import_department_assignments(path)
    assert len(result.assignments) == 2
    assert "Almacén" in result.departments
    assert any(w.issue_code == "duplicate_same_department" for w in result.warnings)


def test_import_xlsx_conflict(tmp_path: Path) -> None:
    path = write_xlsx(
        tmp_path / "conflict.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["12345678Z", "Producción"],
        ],
    )
    result = import_department_assignments(path)
    assert result.assignments == ()
    assert len(result.conflicts) == 1
    assert result.conflicts[0].document_id == "12345678Z"


def test_import_without_headers_fallback_ab(tmp_path: Path) -> None:
    path = write_xlsx(
        tmp_path / "nohdr.xlsx",
        [
            ["12345678Z", "Almacén"],
            ["23456789D", "Admin"],
        ],
    )
    result = import_department_assignments(path)
    assert len(result.assignments) == 2
    assert result.document_column_index == 0


def test_detect_inverted_headers(tmp_path: Path) -> None:
    mapping = detect_column_mapping(["Departamento", "DNI"])
    assert mapping.department_column_index == 0
    assert mapping.document_column_index == 1
    assert mapping.header_row_used is True


def test_list_sheets_and_select(tmp_path: Path) -> None:
    path = write_xlsx(
        tmp_path / "multi.xlsx",
        [["DNI", "Departamento"], ["12345678Z", "A"]],
        sheet_name="Principal",
        extra_sheets={
            "Otra": [["DNI", "Departamento"], ["23456789D", "B"]],
        },
    )
    names = list_sheet_names(path)
    assert "Principal" in names and "Otra" in names
    other = import_department_assignments(path, sheet_name="Otra")
    assert other.assignments[0].document_id == "23456789D"


def test_invalid_and_empty(tmp_path: Path) -> None:
    empty = write_xlsx(tmp_path / "empty.xlsx", [])
    with pytest.raises(SpreadsheetEmptyError):
        import_department_assignments(empty)

    path = write_xlsx(
        tmp_path / "bad.xlsx",
        [["DNI", "Departamento"], ["12345678A", "Almacén"]],
    )
    result = import_department_assignments(path)
    assert any(e.issue_code == "invalid_check_letter" for e in result.errors)


def test_numeric_cell_warning(tmp_path: Path) -> None:
    text, code = cell_value_to_document_text(12345678)
    assert text == "12345678"
    assert code == "numeric_cell_ambiguous"
    text2, code2 = cell_value_to_document_text(1.23e7)
    assert text2 == "12300000"
    assert code2 == "numeric_cell_ambiguous"
    text3, code3 = cell_value_to_document_text(12.34)
    assert text3 is None
    assert code3 == "scientific_or_float_ambiguous"


def test_department_equivalence(tmp_path: Path) -> None:
    path = write_xlsx(
        tmp_path / "eq.xlsx",
        [
            ["DNI", "Departamento"],
            ["12345678Z", "Almacén"],
            ["23456789D", "ALMACEN"],
        ],
    )
    result = import_department_assignments(path)
    assert len(result.departments) == 1
    assert result.assignments[0].department_key == result.assignments[1].department_key


def test_import_xls(tmp_path: Path) -> None:
    pytest.importorskip("xlwt")
    path = write_xls(
        tmp_path / "deps.xls",
        [
            ["DNI/NIE", "Departamento"],
            ["12345678Z", "Almacén"],
            ["X1234567L", "Producción"],
        ],
    )
    result = import_department_assignments(path)
    assert len(result.assignments) == 2
    assert result.sheet_name == "Hoja1"
