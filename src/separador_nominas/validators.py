"""Validaciones de rutas, PDF y nombres base."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError
from pypdf.errors import PdfReadError as PypdfReadError

from separador_nominas.constants import PDF_EXTENSION
from separador_nominas.exceptions import (
    CorruptedPdfError,
    DestinationNotSelectedError,
    EmptyBaseNameError,
    EmptyPdfError,
    InvalidDestinationError,
    InvalidPdfExtensionError,
    PasswordProtectedPdfError,
    PdfNotFoundError,
    PdfNotSelectedError,
    PdfReadError,
    PermissionDeniedError,
)
from separador_nominas.filename_service import sanitize_base_name


def validate_pdf_path(pdf_path: Path | str | None) -> Path:
    """
    Valida que la ruta apunte a un archivo PDF existente y legible.

    Returns:
        Ruta absoluta del PDF validado.

    Raises:
        PdfNotSelectedError: Si no se ha indicado ruta.
        PdfNotFoundError: Si no existe o no es un archivo.
        InvalidPdfExtensionError: Si la extensión no es PDF.
        PermissionDeniedError: Si no se puede leer.
        PasswordProtectedPdfError: Si requiere contraseña.
        EmptyPdfError: Si no tiene páginas.
        CorruptedPdfError: Si está dañado.
        PdfReadError: Ante otros errores de lectura.
    """
    if pdf_path is None or str(pdf_path).strip() == "":
        raise PdfNotSelectedError("No se ha seleccionado ningún archivo PDF.")

    path = Path(pdf_path).expanduser()

    if not path.exists():
        raise PdfNotFoundError("El archivo PDF seleccionado no existe.")

    if not path.is_file():
        raise PdfNotFoundError("La ruta indicada no corresponde a un archivo.")

    if path.suffix.lower() != PDF_EXTENSION:
        raise InvalidPdfExtensionError(
            "El archivo seleccionado no es un PDF. Elige un archivo con extensión .pdf."
        )

    try:
        reader = PdfReader(str(path))
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
        raise PdfReadError(
            "No se ha podido leer el archivo PDF seleccionado."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise CorruptedPdfError(
            "No se ha podido abrir el PDF seleccionado.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc

    if getattr(reader, "is_encrypted", False):
        try:
            # Algunos PDF cifrados permiten lectura tras decrypt vacío.
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

    try:
        page_count = len(reader.pages)
    except Exception as exc:  # noqa: BLE001
        raise CorruptedPdfError(
            "No se ha podido abrir el PDF seleccionado.\n"
            "Comprueba que el archivo no esté dañado ni protegido con contraseña."
        ) from exc

    if page_count < 1:
        raise EmptyPdfError("El PDF seleccionado no contiene páginas.")

    return path.resolve()


def get_pdf_page_count(pdf_path: Path | str) -> int:
    """
    Devuelve el número de páginas de un PDF previamente validable.

    Raises:
        Las mismas excepciones que :func:`validate_pdf_path`.
    """
    path = validate_pdf_path(pdf_path)
    reader = PdfReader(str(path))
    if getattr(reader, "is_encrypted", False):
        reader.decrypt("")
    return len(reader.pages)


def validate_destination_dir(
    destination: Path | str | None,
    *,
    create_if_missing: bool = False,
) -> Path:
    """
    Valida la carpeta de destino y, opcionalmente, la crea.

    Args:
        destination: Ruta de la carpeta.
        create_if_missing: Si es True, intenta crear la carpeta cuando no exista.

    Returns:
        Ruta absoluta de la carpeta.

    Raises:
        DestinationNotSelectedError: Si no se ha indicado carpeta.
        InvalidDestinationError: Si la ruta no es válida o no se puede crear.
        PermissionDeniedError: Si faltan permisos.
    """
    if destination is None or str(destination).strip() == "":
        raise DestinationNotSelectedError(
            "No se ha seleccionado ninguna carpeta de destino."
        )

    path = Path(destination).expanduser()

    if path.exists() and not path.is_dir():
        raise InvalidDestinationError(
            "La ruta de destino existe, pero no es una carpeta."
        )

    if not path.exists():
        if not create_if_missing:
            raise InvalidDestinationError(
                "La carpeta de destino no existe.\n"
                "Selecciona una carpeta válida o permite su creación."
            )
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionDeniedError(
                "No se ha podido crear la carpeta de destino.\n"
                "Comprueba que tienes permisos de escritura "
                "en la ubicación seleccionada."
            ) from exc
        except OSError as exc:
            raise InvalidDestinationError(
                "No se ha podido crear la carpeta de destino.\n"
                "Comprueba que la ruta sea válida y que tengas permisos suficientes."
            ) from exc

    # Comprobar escritura creando y eliminando un marcador temporal.
    probe = path / ".separador_nominas_write_probe"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except PermissionError as exc:
        raise PermissionDeniedError(
            "No se tienen permisos de escritura en la carpeta de destino."
        ) from exc
    except OSError as exc:
        raise InvalidDestinationError(
            "La carpeta de destino no es válida o no permite escribir archivos."
        ) from exc

    return path.resolve()


def validate_base_name(base_name: str | None) -> str:
    """
    Valida y limpia el nombre base de los archivos de salida.

    Returns:
        Nombre base saneado y no vacío.

    Raises:
        EmptyBaseNameError: Si el nombre queda vacío tras limpiar.
    """
    if base_name is None or not str(base_name).strip():
        raise EmptyBaseNameError(
            "El nombre base de los archivos no puede estar vacío."
        )

    sanitized = sanitize_base_name(str(base_name))
    if not sanitized:
        raise EmptyBaseNameError(
            "El nombre base de los archivos no es válido.\n"
            "Evita caracteres especiales no permitidos en Windows."
        )
    return sanitized
