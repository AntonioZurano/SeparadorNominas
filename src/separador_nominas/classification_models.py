"""Modelos en memoria para clasificación de nóminas por grupos."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

RecognitionStatus = Literal["recognized", "partial", "unrecognized"]
ExportMode = Literal["separate", "combined"]


@dataclass
class WorkerRecord:
    """Trabajador consolidado a partir de una o varias páginas."""

    worker_id: str
    document_id: str | None
    display_name: str | None
    normalized_name: str | None
    page_numbers: list[int]
    recognition_status: RecognitionStatus
    warnings: list[str] = field(default_factory=list)
    manual_label: str | None = None

    @property
    def ui_name(self) -> str:
        """Nombre visible en la interfaz (manual o detectado)."""
        if self.manual_label and self.manual_label.strip():
            return self.manual_label.strip()
        if self.display_name:
            return self.display_name
        if self.page_numbers:
            return f"No reconocido — Página {self.page_numbers[0]}"
        return "No reconocido"


@dataclass
class PayrollGroup:
    """Grupo o regla de clasificación (departamento, delegación, etc.)."""

    group_id: str
    display_name: str
    safe_folder_name: str
    worker_ids: list[str] = field(default_factory=list)
    export_mode: ExportMode = "combined"


@dataclass
class ClassificationSession:
    """Sesión de clasificación mantenida únicamente en memoria."""

    source_pdf: Path
    page_count: int
    workers: dict[str, WorkerRecord] = field(default_factory=dict)
    groups: dict[str, PayrollGroup] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassificationExportResult:
    """Resultado de la exportación por grupos."""

    source_pdf: Path
    destination_dir: Path
    group_files: tuple[Path, ...]
    unrecognized_files: tuple[Path, ...]
    groups_exported: int
    workers_exported: int
    unassigned_recognized_count: int

    @property
    def files_created(self) -> int:
        """Número total de archivos PDF generados."""
        return len(self.group_files) + len(self.unrecognized_files)
