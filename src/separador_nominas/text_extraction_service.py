"""Extracción local de texto de páginas PDF con pypdf (sin OCR)."""

from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PageObject, PdfReader

from separador_nominas.constants import LOGGER_NAME
from separador_nominas.exceptions import (
    CorruptedPdfError,
    EmptyPdfError,
    PdfReadError,
)
from separador_nominas.pdf_service import open_pdf_reader
from separador_nominas.validators import validate_pdf_path

logger = logging.getLogger(LOGGER_NAME)


def extract_text_from_page(page: PageObject) -> str:
    """
    Extrae el texto seleccionable de una página PDF.

    Returns:
        Texto normalizado (sin espacios extremos). Cadena vacía si no hay texto
        o si la extracción falla de forma no fatal.
    """
    try:
        raw = page.extract_text()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No se ha podido extraer texto de una página: %s",
            type(exc).__name__,
        )
        return ""

    if raw is None:
        return ""
    return str(raw).strip()


def extract_texts_from_reader(reader: PdfReader) -> tuple[str, ...]:
    """
    Extrae el texto de todas las páginas de un ``PdfReader`` ya abierto.

    Raises:
        EmptyPdfError: Si el PDF no tiene páginas.
        PdfReadError / CorruptedPdfError: Si no se pueden leer las páginas.
    """
    try:
        total_pages = len(reader.pages)
    except Exception as exc:  # noqa: BLE001
        raise CorruptedPdfError(
            "No se ha podido abrir el PDF seleccionado.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc

    if total_pages < 1:
        raise EmptyPdfError("El PDF seleccionado no contiene páginas.")

    texts: list[str] = []
    for index in range(total_pages):
        try:
            page = reader.pages[index]
        except Exception as exc:  # noqa: BLE001
            raise PdfReadError(
                "No se ha podido leer una de las páginas del PDF.\n"
                "Comprueba que el archivo no esté dañado."
            ) from exc
        texts.append(extract_text_from_page(page))

    logger.info("Texto extraído de %s páginas (sin volcar contenido)", total_pages)
    return tuple(texts)


def extract_texts_from_pdf(pdf_path: Path | str) -> tuple[str, ...]:
    """
    Valida y abre un PDF, devolviendo el texto de cada página.

    El contenido textual no se escribe en logs.
    """
    path = validate_pdf_path(pdf_path)
    reader = open_pdf_reader(path)
    return extract_texts_from_reader(reader)
