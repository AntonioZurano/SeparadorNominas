"""Modelos en memoria para importación de departamentos desde Excel."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

UnclassifiedMode = Literal["omit", "combined_folder"]


@dataclass(frozen=True)
class DepartmentAssignment:
    """Asignación DNI/NIE → departamento leída del Excel."""

    document_id: str
    department_name: str
    department_key: str
    source_row: int


@dataclass(frozen=True)
class SpreadsheetRowIssue:
    """Advertencia o error de una fila del Excel (sin datos personales en logs)."""

    row_number: int
    issue_code: str
    user_message: str


@dataclass(frozen=True)
class AssignmentConflict:
    """Mismo documento con departamentos distintos en el Excel."""

    document_id: str
    source_rows: tuple[int, ...]
    department_keys: tuple[str, ...]
    department_names: tuple[str, ...]
    # Pares (department_key, display_name) alineados
    department_options: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SpreadsheetImportResult:
    """Resultado del análisis del Excel (solo en memoria)."""

    assignments: tuple[DepartmentAssignment, ...]
    departments: tuple[str, ...]
    warnings: tuple[SpreadsheetRowIssue, ...]
    errors: tuple[SpreadsheetRowIssue, ...]
    conflicts: tuple[AssignmentConflict, ...]
    row_count_read: int
    sheet_name: str
    document_column_index: int
    department_column_index: int


@dataclass(frozen=True)
class ColumnMapping:
    """Columnas elegidas (0-based) para documento y departamento."""

    document_column_index: int
    department_column_index: int
    document_header: str | None = None
    department_header: str | None = None
    header_row_used: bool = False


@dataclass(frozen=True)
class MatchSummary:
    """Resumen del cruce Excel ↔ trabajadores del PDF."""

    matched_workers: int
    unmatched_pdf_workers: int
    unmatched_spreadsheet_rows: int
    conflicts_pending: int
    pages_unclassified: int
    departments_with_workers: int


@dataclass
class SpreadsheetClassificationState:
    """Metadatos temporales del modo Excel (solo en memoria)."""

    source_spreadsheet: Path | None = None
    sheet_name: str | None = None
    column_mapping: ColumnMapping | None = None
    import_result: SpreadsheetImportResult | None = None
    match_summary: MatchSummary | None = None
    unresolved_conflict_docs: set[str] = field(default_factory=set)
    resolved_conflict_choices: dict[str, str] = field(default_factory=dict)
