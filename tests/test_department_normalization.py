"""Tests de modelos y normalización de departamentos."""

from __future__ import annotations

from separador_nominas.department_normalization import (
    normalize_department,
    to_department_key,
    to_display_name,
)
from separador_nominas.spreadsheet_models import (
    DepartmentAssignment,
    SpreadsheetImportResult,
)


def test_department_key_accent_and_case() -> None:
    assert to_department_key("Almacén") == to_department_key("ALMACEN")
    assert to_department_key(" Almacén ") == "almacen"
    assert to_display_name("  Admin   Central ") == "Admin Central"


def test_normalize_department_safe_folder() -> None:
    dept = normalize_department("Almacén / Norte*")
    assert dept is not None
    assert "almacen" in dept.department_key
    assert "*" not in dept.safe_folder_name
    assert ":" not in dept.safe_folder_name


def test_normalize_department_empty() -> None:
    assert normalize_department(None) is None
    assert normalize_department("   ") is None


def test_department_assignment_frozen() -> None:
    item = DepartmentAssignment(
        document_id="12345678Z",
        department_name="Almacén",
        department_key="almacen",
        source_row=2,
    )
    assert item.document_id == "12345678Z"


def test_import_result_tuple_fields() -> None:
    result = SpreadsheetImportResult(
        assignments=(),
        departments=("Almacén",),
        warnings=(),
        errors=(),
        conflicts=(),
        row_count_read=0,
        sheet_name="Hoja1",
        document_column_index=0,
        department_column_index=1,
    )
    assert result.departments == ("Almacén",)
