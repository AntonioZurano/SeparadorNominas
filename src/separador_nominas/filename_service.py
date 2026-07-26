"""Generación y saneamiento de nombres de archivo para las nóminas separadas."""

from __future__ import annotations

import re
from pathlib import Path

from separador_nominas.constants import (
    COLLISION_START_INDEX,
    DEFAULT_BASE_NAME,
    FILENAME_SEPARATOR,
    MAX_BASE_NAME_LENGTH,
    OUTPUT_FOLDER_SUFFIX,
    PDF_EXTENSION,
    WINDOWS_INVALID_FILENAME_CHARS,
    WINDOWS_RESERVED_NAMES,
)


def digit_width_for_pages(total_pages: int) -> int:
    """
    Calcula el número de dígitos necesarios para numerar las páginas.

    - Hasta 9 páginas: 1 dígito
    - Hasta 99 páginas: 2 dígitos
    - Desde 100 páginas: 3 o más dígitos
    """
    if total_pages < 1:
        return 1
    return max(1, len(str(total_pages)))


def sanitize_base_name(name: str) -> str:
    """
    Limpia un nombre base para que sea válido en Windows.

    - Elimina caracteres no permitidos.
    - Sustituye espacios múltiples por uno solo y recorta extremos.
    - Elimina puntos y espacios finales.
    - Evita nombres reservados de Windows.
    - Limita la longitud máxima.
    """
    cleaned = str(name).strip()
    translation = str.maketrans(
        {char: "_" for char in WINDOWS_INVALID_FILENAME_CHARS}
    )
    cleaned = cleaned.translate(translation)
    # Caracteres de control
    cleaned = re.sub(r"[\x00-\x1f]", "", cleaned)
    cleaned = re.sub(r"[\s_]+", "_", cleaned)
    cleaned = cleaned.strip("._ ")

    if not cleaned or cleaned.replace("_", "") == "":
        return ""

    stem_for_reserved = cleaned.split(".")[0].upper()
    if stem_for_reserved in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_file"

    if len(cleaned) > MAX_BASE_NAME_LENGTH:
        cleaned = cleaned[:MAX_BASE_NAME_LENGTH].rstrip("._ ")

    return cleaned


def suggest_base_name_from_pdf(pdf_path: Path | str) -> str:
    """Propone un nombre base a partir del nombre del PDF de origen."""
    stem = Path(pdf_path).stem
    sanitized = sanitize_base_name(stem)
    return sanitized or DEFAULT_BASE_NAME


def suggest_output_directory(pdf_path: Path | str) -> Path:
    """
    Propone una carpeta de destino junto al PDF original.

    Ejemplo: ``Nominas_Julio_2026.pdf`` → ``Nominas_Julio_2026_separadas``
    """
    path = Path(pdf_path)
    base = sanitize_base_name(path.stem) or DEFAULT_BASE_NAME
    return path.parent / f"{base}{OUTPUT_FOLDER_SUFFIX}"


def build_page_filename(base_name: str, page_number: int, total_pages: int) -> str:
    """
    Construye el nombre de archivo para una página concreta.

    Ejemplo con 18 páginas: ``Nominas_Julio_2026_04.pdf``
    """
    sanitized = sanitize_base_name(base_name) or DEFAULT_BASE_NAME
    width = digit_width_for_pages(total_pages)
    number = f"{page_number:0{width}d}"
    return f"{sanitized}{FILENAME_SEPARATOR}{number}{PDF_EXTENSION}"


def get_available_path(target_path: Path) -> Path:
    """
    Devuelve una ruta disponible sin sobrescribir archivos existentes.

    Si ``Nomina_001.pdf`` existe, prueba ``Nomina_001_2.pdf``,
    ``Nomina_001_3.pdf``, etc.
    """
    path = Path(target_path)
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = COLLISION_START_INDEX

    while True:
        candidate = parent / f"{stem}{FILENAME_SEPARATOR}{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def build_output_path(
    destination_dir: Path | str,
    base_name: str,
    page_number: int,
    total_pages: int,
    *,
    avoid_overwrite: bool = True,
) -> Path:
    """
    Construye la ruta completa de salida para una página.

    Args:
        destination_dir: Carpeta de destino.
        base_name: Nombre base de los archivos.
        page_number: Número de página (1-based).
        total_pages: Total de páginas del PDF.
        avoid_overwrite: Si True, evita colisiones con archivos existentes.
    """
    filename = build_page_filename(base_name, page_number, total_pages)
    path = Path(destination_dir) / filename
    if avoid_overwrite:
        return get_available_path(path)
    return path
