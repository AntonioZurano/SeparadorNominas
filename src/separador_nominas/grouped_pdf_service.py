"""Orquestación de análisis y escritura de PDFs agrupados por trabajador."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from separador_nominas.constants import (
    LOGGER_NAME,
    PDF_EXTENSION,
    UNRECOGNIZED_FOLDER_NAME,
    UNRECOGNIZED_PAGE_PREFIX,
)
from separador_nominas.employee_name_service import recognize_page
from separador_nominas.exceptions import (
    PdfReadError,
    PdfWriteError,
    PermissionDeniedError,
    UnexpectedError,
)
from separador_nominas.filename_service import (
    digit_width_for_pages,
    get_available_path,
)
from separador_nominas.grouping_service import build_employee_groups
from separador_nominas.pdf_service import open_pdf_reader
from separador_nominas.recognition_models import (
    GroupingAnalysis,
    GroupingProcessResult,
)
from separador_nominas.text_extraction_service import extract_text_from_page
from separador_nominas.validators import (
    validate_destination_dir,
    validate_pdf_path,
)

logger = logging.getLogger(LOGGER_NAME)

AnalyzeProgressCallback = Callable[[int, int], None]
WriteProgressCallback = Callable[[int, int, Path], None]


def analyze_payroll_pdf(
    source_pdf: Path | str,
    *,
    progress_callback: AnalyzeProgressCallback | None = None,
) -> GroupingAnalysis:
    """
    Analiza un PDF: extrae texto, reconoce nombres y agrupa (sin escribir).

    No registra el contenido textual ni nombres en los logs.
    """
    pdf_path = validate_pdf_path(source_pdf)
    reader = open_pdf_reader(pdf_path)
    page_count = len(reader.pages)

    page_results = []
    for index in range(page_count):
        try:
            page = reader.pages[index]
        except Exception as exc:  # noqa: BLE001
            raise PdfReadError(
                "No se ha podido leer una de las páginas del PDF.\n"
                "Comprueba que el archivo no esté dañado."
            ) from exc

        text = extract_text_from_page(page)
        page_results.append(recognize_page(page_index=index, page_text=text))

        if progress_callback is not None:
            progress_callback(index + 1, page_count)

    results_tuple = tuple(page_results)
    groups, unrecognized = build_employee_groups(results_tuple)

    logger.info(
        "Análisis completado: %s páginas, %s grupos, %s no reconocidas",
        page_count,
        len(groups),
        len(unrecognized),
    )

    return GroupingAnalysis(
        source_pdf=pdf_path,
        page_count=page_count,
        page_results=results_tuple,
        groups=groups,
        unrecognized_page_numbers=unrecognized,
    )


def format_grouping_summary(analysis: GroupingAnalysis) -> str:
    """Construye un resumen textual en español para la UI."""
    lines = [
        f"Páginas analizadas: {analysis.page_count}",
        f"Trabajadores reconocidos: {len(analysis.groups)}",
        f"Páginas no reconocidas: {len(analysis.unrecognized_page_numbers)}",
    ]
    if analysis.groups:
        lines.append("")
        lines.append("Grupos:")
        for group in analysis.groups:
            pages = ", ".join(str(n) for n in group.page_numbers)
            lines.append(
                f"- {group.display_name}: {len(group.page_numbers)} página"
                f"{'s' if len(group.page_numbers) != 1 else ''} ({pages})"
            )
    if analysis.unrecognized_page_numbers:
        pages = ", ".join(str(n) for n in analysis.unrecognized_page_numbers)
        lines.append("")
        lines.append(f"No reconocidas → carpeta {UNRECOGNIZED_FOLDER_NAME}/: {pages}")
    return "\n".join(lines)


def _write_pages(
    reader: PdfReader,
    page_numbers: tuple[int, ...],
    output_path: Path,
) -> None:
    writer = PdfWriter()
    for page_number in page_numbers:
        try:
            writer.add_page(reader.pages[page_number - 1])
        except Exception as exc:  # noqa: BLE001
            raise PdfReadError(
                "No se ha podido leer una de las páginas del PDF.\n"
                "Comprueba que el archivo no esté dañado."
            ) from exc

    try:
        with output_path.open("wb") as handle:
            writer.write(handle)
    except PermissionError as exc:
        raise PermissionDeniedError(
            "No se ha podido guardar uno de los archivos.\n"
            "Comprueba que tienes permisos de escritura en la carpeta seleccionada."
        ) from exc
    except OSError as exc:
        raise PdfWriteError(
            "No se ha podido guardar uno de los archivos.\n"
            "Comprueba que tienes permisos de escritura en la carpeta seleccionada."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise UnexpectedError(
            "Se ha producido un error inesperado al guardar un archivo."
        ) from exc


def write_grouped_pdfs(
    analysis: GroupingAnalysis,
    destination_dir: Path | str,
    *,
    progress_callback: WriteProgressCallback | None = None,
    create_destination: bool = True,
) -> GroupingProcessResult:
    """
    Escribe un PDF por trabajador y páginas no reconocidas en ``No_reconocidas/``.
    """
    dest_path = validate_destination_dir(
        destination_dir, create_if_missing=create_destination
    )
    reader = open_pdf_reader(analysis.source_pdf)

    output_files: list[Path] = []
    unrecognized_files: list[Path] = []

    total_writes = len(analysis.groups) + len(analysis.unrecognized_page_numbers)
    written = 0

    for group in analysis.groups:
        target = dest_path / f"{group.safe_filename_stem}{PDF_EXTENSION}"
        output_path = get_available_path(target)
        _write_pages(reader, group.page_numbers, output_path)
        output_files.append(output_path)
        written += 1
        if progress_callback is not None:
            progress_callback(written, max(total_writes, 1), output_path)

    if analysis.unrecognized_page_numbers:
        unrecognized_dir = dest_path / UNRECOGNIZED_FOLDER_NAME
        try:
            unrecognized_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionDeniedError(
                "No se ha podido crear la carpeta de páginas no reconocidas.\n"
                "Comprueba que tienes permisos de escritura en la carpeta seleccionada."
            ) from exc
        except OSError as exc:
            raise PdfWriteError(
                "No se ha podido crear la carpeta de páginas no reconocidas."
            ) from exc

        width = digit_width_for_pages(analysis.page_count)
        for page_number in analysis.unrecognized_page_numbers:
            number = f"{page_number:0{width}d}"
            filename = f"{UNRECOGNIZED_PAGE_PREFIX}_{number}{PDF_EXTENSION}"
            target = unrecognized_dir / filename
            output_path = get_available_path(target)
            _write_pages(reader, (page_number,), output_path)
            unrecognized_files.append(output_path)
            written += 1
            if progress_callback is not None:
                progress_callback(written, max(total_writes, 1), output_path)

    logger.info(
        "Escritura agrupada completada: %s grupos, %s no reconocidas",
        len(output_files),
        len(unrecognized_files),
    )

    return GroupingProcessResult(
        source_pdf=analysis.source_pdf,
        destination_dir=dest_path,
        groups=analysis.groups,
        unrecognized_page_numbers=analysis.unrecognized_page_numbers,
        output_files=tuple(output_files),
        unrecognized_files=tuple(unrecognized_files),
    )
