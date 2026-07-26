"""Servicio de separación de páginas PDF con pypdf."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import FileNotDecryptedError
from pypdf.errors import PdfReadError as PypdfReadError

from separador_nominas.constants import LOGGER_NAME
from separador_nominas.exceptions import (
    CorruptedPdfError,
    EmptyPdfError,
    PasswordProtectedPdfError,
    PdfNotFoundError,
    PdfReadError,
    PdfWriteError,
    PermissionDeniedError,
    UnexpectedError,
)
from separador_nominas.filename_service import build_output_path
from separador_nominas.validators import (
    validate_base_name,
    validate_destination_dir,
    validate_pdf_path,
)

logger = logging.getLogger(LOGGER_NAME)

ProgressCallback = Callable[[int, int, Path], None]


@dataclass(frozen=True)
class SplitResult:
    """Resultado de una separación de PDF."""

    source_pdf: Path
    destination_dir: Path
    output_files: tuple[Path, ...]
    page_count: int

    @property
    def files_created(self) -> int:
        """Número de archivos generados."""
        return len(self.output_files)


def open_pdf_reader(pdf_path: Path) -> PdfReader:
    """Abre un PdfReader gestionando cifrado y errores de lectura."""
    try:
        reader = PdfReader(str(pdf_path))
    except FileNotFoundError as exc:
        raise PdfNotFoundError("El archivo PDF seleccionado no existe.") from exc
    except PermissionError as exc:
        raise PermissionDeniedError(
            "No se tienen permisos para leer el archivo PDF seleccionado."
        ) from exc
    except FileNotDecryptedError as exc:
        raise PasswordProtectedPdfError(
            "El PDF está protegido con contraseña.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc
    except PypdfReadError as exc:
        raise CorruptedPdfError(
            "No se ha podido abrir el PDF seleccionado.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc
    except OSError as exc:
        raise PdfReadError("No se ha podido leer el archivo PDF seleccionado.") from exc

    if getattr(reader, "is_encrypted", False):
        try:
            if reader.decrypt("") == 0:
                raise PasswordProtectedPdfError(
                    "El PDF está protegido con contraseña.\n"
                    "Comprueba que el archivo no esté dañado "
                    "ni protegido con contraseña."
                )
        except PasswordProtectedPdfError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PasswordProtectedPdfError(
                "El PDF está protegido con contraseña.\n"
                "Comprueba que el archivo no esté dañado "
                "ni protegido con contraseña."
            ) from exc

    return reader


def split_pdf(
    source_pdf: Path | str,
    destination_dir: Path | str,
    base_name: str,
    *,
    progress_callback: ProgressCallback | None = None,
    create_destination: bool = True,
) -> SplitResult:
    """
    Separa cada página del PDF en un archivo independiente.

    Conserva el contenido vectorial/texto del PDF original (sin rasterizar).

    Args:
        source_pdf: Ruta del PDF de origen.
        destination_dir: Carpeta donde guardar los resultados.
        base_name: Nombre base de los archivos generados.
        progress_callback: Callback ``(página_actual, total, ruta_salida)``.
        create_destination: Crear la carpeta de destino si no existe.

    Returns:
        :class:`SplitResult` con las rutas generadas.
    """
    pdf_path = validate_pdf_path(source_pdf)
    dest_path = validate_destination_dir(
        destination_dir, create_if_missing=create_destination
    )
    clean_base = validate_base_name(base_name)

    reader = open_pdf_reader(pdf_path)
    try:
        total_pages = len(reader.pages)
    except Exception as exc:  # noqa: BLE001
        raise CorruptedPdfError(
            "No se ha podido abrir el PDF seleccionado.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc

    if total_pages < 1:
        raise EmptyPdfError("El PDF seleccionado no contiene páginas.")

    logger.info("Inicio de separación: %s páginas", total_pages)

    output_files: list[Path] = []

    for index in range(total_pages):
        page_number = index + 1
        output_path = build_output_path(
            dest_path,
            clean_base,
            page_number,
            total_pages,
            avoid_overwrite=True,
        )

        writer = PdfWriter()
        try:
            writer.add_page(reader.pages[index])
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

        output_files.append(output_path)

        if progress_callback is not None:
            progress_callback(page_number, total_pages, output_path)

    logger.info("Separación completada: %s archivos", len(output_files))

    return SplitResult(
        source_pdf=pdf_path,
        destination_dir=dest_path,
        output_files=tuple(output_files),
        page_count=total_pages,
    )
