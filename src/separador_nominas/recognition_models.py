"""Modelos de datos para reconocimiento y agrupación de nóminas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RecognitionConfidence = Literal["high", "none"]


@dataclass(frozen=True)
class PageRecognitionResult:
    """Resultado del reconocimiento de una página (sin texto extraído)."""

    page_index: int
    page_number: int
    has_text: bool
    detected_name: str | None
    display_name: str | None
    normalized_key: str | None
    confidence: RecognitionConfidence
    warning_code: str | None = None


@dataclass(frozen=True)
class EmployeePageGroup:
    """Grupo de páginas asociadas a un mismo trabajador."""

    display_name: str
    normalized_key: str
    safe_filename_stem: str
    page_numbers: tuple[int, ...]


@dataclass(frozen=True)
class GroupingAnalysis:
    """Análisis previo a la escritura de PDFs agrupados."""

    source_pdf: Path
    page_count: int
    page_results: tuple[PageRecognitionResult, ...]
    groups: tuple[EmployeePageGroup, ...]
    unrecognized_page_numbers: tuple[int, ...]


@dataclass(frozen=True)
class GroupingProcessResult:
    """Resultado de la escritura de PDFs agrupados."""

    source_pdf: Path
    destination_dir: Path
    groups: tuple[EmployeePageGroup, ...]
    unrecognized_page_numbers: tuple[int, ...]
    output_files: tuple[Path, ...]
    unrecognized_files: tuple[Path, ...]

    @property
    def files_created(self) -> int:
        """Número total de archivos generados (grupos + no reconocidas)."""
        return len(self.output_files) + len(self.unrecognized_files)

    @property
    def recognized_worker_count(self) -> int:
        """Número de trabajadores reconocidos."""
        return len(self.groups)
