"""Exportación de PDFs por grupos (separado o conjunto)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from separador_nominas.classification_models import (
    ClassificationExportResult,
    ClassificationSession,
    PayrollGroup,
    WorkerRecord,
)
from separador_nominas.classification_service import (
    unassigned_worker_ids,
    workers_in_multiple_groups,
)
from separador_nominas.constants import (
    FILENAME_SEPARATOR,
    LOGGER_NAME,
    PDF_EXTENSION,
    UNCLASSIFIED_COMBINED_STEM,
    UNCLASSIFIED_FOLDER_NAME,
    UNRECOGNIZED_FOLDER_NAME,
    UNRECOGNIZED_PAGE_PREFIX,
)
from separador_nominas.exceptions import (
    PdfReadError,
    PdfWriteError,
    PermissionDeniedError,
    UnexpectedError,
)
from separador_nominas.filename_service import (
    digit_width_for_pages,
    get_available_path,
    sanitize_base_name,
)
from separador_nominas.name_normalization import to_safe_filename_stem
from separador_nominas.pdf_service import open_pdf_reader
from separador_nominas.spreadsheet_models import UnclassifiedMode
from separador_nominas.validators import validate_destination_dir

logger = logging.getLogger(LOGGER_NAME)

WriteProgressCallback = Callable[[int, int, Path], None]


def _write_pages(
    reader: PdfReader,
    page_numbers: list[int] | tuple[int, ...],
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


def worker_output_stem(worker: WorkerRecord) -> str:
    """Nombre de archivo seguro para un trabajador (sin extensión)."""
    name_part = ""
    if worker.manual_label:
        name_part = to_safe_filename_stem(worker.manual_label)
    elif worker.display_name:
        name_part = to_safe_filename_stem(worker.display_name)

    if worker.document_id:
        doc = sanitize_base_name(worker.document_id) or worker.document_id
        if name_part:
            return f"{doc}{FILENAME_SEPARATOR}{name_part}"
        return doc

    page = worker.page_numbers[0] if worker.page_numbers else 0
    if name_part:
        return f"{UNRECOGNIZED_PAGE_PREFIX}_{page:03d}{FILENAME_SEPARATOR}{name_part}"
    return f"{UNRECOGNIZED_PAGE_PREFIX}_{page:03d}"


def _sorted_workers_for_group(
    session: ClassificationSession,
    group: PayrollGroup,
) -> list[WorkerRecord]:
    """Trabajadores del grupo ordenados por primera página (orden PDF original)."""
    workers: list[WorkerRecord] = []
    for wid in group.worker_ids:
        worker = session.workers.get(wid)
        if worker is not None and worker.page_numbers:
            workers.append(worker)
    workers.sort(key=lambda w: (min(w.page_numbers), w.worker_id))
    return workers


def _ensure_group_dir(dest: Path, folder_name: str) -> Path:
    group_dir = dest / folder_name
    try:
        group_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionDeniedError(
            "No se ha podido crear la carpeta del grupo.\n"
            "Comprueba que tienes permisos de escritura en la carpeta seleccionada."
        ) from exc
    except OSError as exc:
        raise PdfWriteError("No se ha podido crear la carpeta del grupo.") from exc
    return group_dir


def _pages_for_unassigned_unrecognized(session: ClassificationSession) -> list[int]:
    pages: list[int] = []
    for wid in unassigned_worker_ids(session):
        worker = session.workers[wid]
        if worker.recognition_status == "recognized" and worker.document_id:
            continue
        pages.extend(worker.page_numbers)
    return pages


def _count_planned_writes(
    session: ClassificationSession,
    *,
    unclassified_mode: UnclassifiedMode = "omit",
) -> int:
    total = 0
    for group in session.groups.values():
        workers = _sorted_workers_for_group(session, group)
        if not workers:
            continue
        if group.export_mode == "combined":
            total += 1
        else:
            total += len(workers)
    if unclassified_mode == "combined_folder":
        pages = _pages_for_unclassified(session)
        if pages:
            total += 1
    else:
        total += len(set(_pages_for_unassigned_unrecognized(session)))
    return total


def _pages_for_unclassified(session: ClassificationSession) -> list[int]:
    """Todas las páginas de trabajadores sin asignar (orden global después)."""
    pages: list[int] = []
    for wid in unassigned_worker_ids(session):
        pages.extend(session.workers[wid].page_numbers)
    return sorted(set(pages))


def format_classification_export_summary(session: ClassificationSession) -> str:
    """Resumen previo a exportar (sin listar DNI; sí nombres de grupo)."""
    unassigned = unassigned_worker_ids(session)
    unassigned_recognized = [
        wid
        for wid in unassigned
        if session.workers[wid].recognition_status == "recognized"
    ]
    multi = workers_in_multiple_groups(session)
    lines = [
        "Resumen de clasificación",
        "",
        f"PDF analizado: {session.source_pdf.name}",
        f"Páginas totales: {session.page_count}",
        f"Trabajadores detectados: {len(session.workers)}",
        f"Grupos creados: {len(session.groups)}",
        f"Trabajadores sin asignar: {len(unassigned)}",
        f"Reconocidos sin asignar (no se exportarán): {len(unassigned_recognized)}",
    ]
    if multi:
        lines.append(
            f"Advertencia: {len(multi)} trabajador(es) en varios grupos "
            "(sus páginas se incluirán en cada grupo)."
        )
    if session.groups:
        lines.append("")
        for group in session.groups.values():
            workers = _sorted_workers_for_group(session, group)
            pages = sum(len(w.page_numbers) for w in workers)
            mode_label = (
                "archivo conjunto"
                if group.export_mode == "combined"
                else "un archivo por trabajador"
            )
            lines.append(group.display_name)
            lines.append(f"- {len(workers)} trabajadores")
            lines.append(f"- {pages} páginas")
            lines.append(f"- Exportación: {mode_label}")
            lines.append("")
    return "\n".join(lines).rstrip()


def export_classification_session(
    session: ClassificationSession,
    destination_dir: Path | str,
    *,
    progress_callback: WriteProgressCallback | None = None,
    create_destination: bool = True,
    unclassified_mode: UnclassifiedMode = "omit",
) -> ClassificationExportResult:
    """
    Exporta grupos a carpetas.

    - ``unclassified_mode="omit"`` (manual): reconocidos sin asignar omitidos;
      no reconocidos/TEMP → ``No_reconocidas/Pagina_XXX.pdf``.
    - ``unclassified_mode="combined_folder"`` (Excel): todas las páginas sin
      asignar → ``No_clasificadas/Nominas_no_clasificadas.pdf`` (orden global).
    """
    dest_path = validate_destination_dir(
        destination_dir, create_if_missing=create_destination
    )
    reader = open_pdf_reader(session.source_pdf)

    group_files: list[Path] = []
    unrecognized_files: list[Path] = []
    unclassified_files: list[Path] = []
    workers_exported: set[str] = set()
    written = 0
    planned = max(
        _count_planned_writes(session, unclassified_mode=unclassified_mode), 1
    )

    for group in session.groups.values():
        workers = _sorted_workers_for_group(session, group)
        if not workers:
            continue

        group_dir = _ensure_group_dir(dest_path, group.safe_folder_name)

        if group.export_mode == "combined":
            pages: list[int] = []
            for worker in workers:
                pages.extend(worker.page_numbers)
                workers_exported.add(worker.worker_id)
            pages = sorted(set(pages))
            stem = sanitize_base_name(f"Nominas_{group.safe_folder_name}")
            target = group_dir / f"{stem}{PDF_EXTENSION}"
            output_path = get_available_path(target)
            _write_pages(reader, pages, output_path)
            group_files.append(output_path)
            written += 1
            if progress_callback is not None:
                progress_callback(written, planned, output_path)
        else:
            for worker in workers:
                stem = worker_output_stem(worker)
                target = group_dir / f"{stem}{PDF_EXTENSION}"
                output_path = get_available_path(target)
                _write_pages(reader, sorted(worker.page_numbers), output_path)
                group_files.append(output_path)
                workers_exported.add(worker.worker_id)
                written += 1
                if progress_callback is not None:
                    progress_callback(written, planned, output_path)

    unassigned = unassigned_worker_ids(session)
    unassigned_recognized_count = sum(
        1
        for wid in unassigned
        if session.workers[wid].recognition_status == "recognized"
        and session.workers[wid].document_id
    )

    if unclassified_mode == "combined_folder":
        pages_unclassified = _pages_for_unclassified(session)
        if pages_unclassified:
            unclassified_dir = _ensure_group_dir(
                dest_path, UNCLASSIFIED_FOLDER_NAME
            )
            stem = sanitize_base_name(UNCLASSIFIED_COMBINED_STEM)
            target = unclassified_dir / f"{stem}{PDF_EXTENSION}"
            output_path = get_available_path(target)
            _write_pages(reader, pages_unclassified, output_path)
            unclassified_files.append(output_path)
            written += 1
            if progress_callback is not None:
                progress_callback(written, planned, output_path)
            unassigned_recognized_count = 0
    else:
        pages_for_unrecognized = _pages_for_unassigned_unrecognized(session)
        if pages_for_unrecognized:
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

            width = digit_width_for_pages(session.page_count)
            for page_number in sorted(set(pages_for_unrecognized)):
                number = f"{page_number:0{width}d}"
                filename = f"{UNRECOGNIZED_PAGE_PREFIX}_{number}{PDF_EXTENSION}"
                target = unrecognized_dir / filename
                output_path = get_available_path(target)
                _write_pages(reader, (page_number,), output_path)
                unrecognized_files.append(output_path)
                written += 1
                if progress_callback is not None:
                    progress_callback(written, planned, output_path)

    logger.info(
        "Exportación de clasificación: %s archivos de grupo, "
        "%s no reconocidas, %s no clasificadas, "
        "%s reconocidos sin asignar omitidos",
        len(group_files),
        len(unrecognized_files),
        len(unclassified_files),
        unassigned_recognized_count,
    )

    return ClassificationExportResult(
        source_pdf=session.source_pdf,
        destination_dir=dest_path,
        group_files=tuple(group_files),
        unrecognized_files=tuple(unrecognized_files),
        groups_exported=len({p.parent for p in group_files}),
        workers_exported=len(workers_exported),
        unassigned_recognized_count=unassigned_recognized_count,
        unclassified_files=tuple(unclassified_files),
    )
