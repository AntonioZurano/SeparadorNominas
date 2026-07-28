"""Consolidación de páginas en trabajadores y análisis para clasificación."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from separador_nominas.classification_models import (
    ClassificationSession,
    WorkerRecord,
)
from separador_nominas.constants import LOGGER_NAME
from separador_nominas.document_identifier_service import (
    extract_document_ids,
    pick_primary_document,
)
from separador_nominas.employee_name_service import recognize_page
from separador_nominas.exceptions import PdfReadError
from separador_nominas.pdf_service import open_pdf_reader
from separador_nominas.text_extraction_service import extract_text_from_page
from separador_nominas.validators import validate_pdf_path

logger = logging.getLogger(LOGGER_NAME)

AnalyzeProgressCallback = Callable[[int, int], None]


def temp_worker_id(page_number: int) -> str:
    """Identificador temporal de sesión para una página sin DNI/NIE."""
    return f"TEMP-PAGE-{page_number:03d}"


def document_worker_id(document_id: str) -> str:
    """Identificador estable basado en DNI/NIE normalizado."""
    return f"DOC:{document_id}"


def build_workers_from_pages(
    *,
    page_texts: list[str],
) -> dict[str, WorkerRecord]:
    """
    Consolida páginas en ``WorkerRecord``.

    - Con DNI/NIE: una ficha por documento (páginas fusionadas).
    - Sin documento: una ficha ``TEMP-PAGE-N`` por página (sin fusionar por nombre).
    """
    workers: dict[str, WorkerRecord] = {}

    for index, page_text in enumerate(page_texts):
        page_number = index + 1
        name_result = recognize_page(page_index=index, page_text=page_text)
        matches = extract_document_ids(page_text)
        primary, doc_warnings = pick_primary_document(matches)

        warnings = list(doc_warnings)
        if name_result.warning_code:
            warnings.append(name_result.warning_code)

        if primary is not None:
            worker_id = document_worker_id(primary.normalized)
            existing = workers.get(worker_id)
            display = name_result.display_name
            normalized = name_result.normalized_key

            if existing is None:
                status: str
                if display:
                    status = "recognized"
                else:
                    status = "partial"
                workers[worker_id] = WorkerRecord(
                    worker_id=worker_id,
                    document_id=primary.normalized,
                    display_name=display,
                    normalized_name=normalized,
                    page_numbers=[page_number],
                    recognition_status=status,  # type: ignore[arg-type]
                    warnings=warnings,
                )
            else:
                existing.page_numbers.append(page_number)
                existing.page_numbers.sort()
                if (
                    display
                    and existing.display_name
                    and display != existing.display_name
                ):
                    if "name_mismatch" not in existing.warnings:
                        existing.warnings.append("name_mismatch")
                elif display and not existing.display_name:
                    existing.display_name = display
                    existing.normalized_name = normalized
                    if existing.recognition_status == "partial":
                        existing.recognition_status = "recognized"
                for code in warnings:
                    if code not in existing.warnings:
                        existing.warnings.append(code)
            continue

        # Sin documento: no fusionar entre páginas.
        worker_id = temp_worker_id(page_number)
        if name_result.display_name:
            status = "partial"
            display = name_result.display_name
            normalized = name_result.normalized_key
        else:
            status = "unrecognized"
            display = None
            normalized = None
        workers[worker_id] = WorkerRecord(
            worker_id=worker_id,
            document_id=None,
            display_name=display,
            normalized_name=normalized,
            page_numbers=[page_number],
            recognition_status=status,  # type: ignore[arg-type]
            warnings=warnings,
        )

    return workers


def analyze_classification_pdf(
    source_pdf: Path | str,
    *,
    progress_callback: AnalyzeProgressCallback | None = None,
) -> ClassificationSession:
    """
    Analiza un PDF para el modo clasificación (sin escribir ni persistir).

    No registra texto, nombres ni DNI/NIE en los logs.
    """
    pdf_path = validate_pdf_path(source_pdf)
    reader = open_pdf_reader(pdf_path)
    page_count = len(reader.pages)

    page_texts: list[str] = []
    for index in range(page_count):
        try:
            page = reader.pages[index]
        except Exception as exc:  # noqa: BLE001
            raise PdfReadError(
                "No se ha podido leer una de las páginas del PDF.\n"
                "Comprueba que el archivo no esté dañado."
            ) from exc
        page_texts.append(extract_text_from_page(page))
        if progress_callback is not None:
            progress_callback(index + 1, page_count)

    workers = build_workers_from_pages(page_texts=page_texts)
    # Liberar texto cuanto antes.
    page_texts.clear()

    recognized = sum(
        1 for w in workers.values() if w.recognition_status == "recognized"
    )
    unrecognized = sum(
        1 for w in workers.values() if w.recognition_status == "unrecognized"
    )
    logger.info(
        "Análisis de clasificación: %s páginas, %s trabajadores, "
        "%s reconocidos, %s a revisar",
        page_count,
        len(workers),
        recognized,
        unrecognized,
    )

    return ClassificationSession(
        source_pdf=pdf_path,
        page_count=page_count,
        workers=workers,
        groups={},
    )


def format_classification_analysis_summary(session: ClassificationSession) -> str:
    """Resumen agregado sin listar DNI ni nombres (seguro para logs/UI breve)."""
    recognized = sum(
        1 for w in session.workers.values() if w.recognition_status == "recognized"
    )
    partial = sum(
        1 for w in session.workers.values() if w.recognition_status == "partial"
    )
    unrecognized = sum(
        1 for w in session.workers.values() if w.recognition_status == "unrecognized"
    )
    return "\n".join(
        [
            f"Páginas analizadas: {session.page_count}",
            f"Trabajadores detectados: {len(session.workers)}",
            f"Reconocidos (DNI/NIE + nombre): {recognized}",
            f"Parciales (falta dato): {partial}",
            f"No reconocidos: {unrecognized}",
            f"Grupos creados: {len(session.groups)}",
        ]
    )
