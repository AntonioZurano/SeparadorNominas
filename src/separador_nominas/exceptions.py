"""Excepciones de dominio de Separador de Nóminas PDF."""

from __future__ import annotations


class SeparadorNominasError(Exception):
    """Error base de la aplicación."""

    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)


class PdfNotSelectedError(SeparadorNominasError):
    """No se ha seleccionado ningún archivo PDF."""


class DestinationNotSelectedError(SeparadorNominasError):
    """No se ha seleccionado carpeta de destino."""


class EmptyBaseNameError(SeparadorNominasError):
    """El nombre base está vacío o es inválido."""


class PdfNotFoundError(SeparadorNominasError):
    """El archivo PDF no existe en la ruta indicada."""


class InvalidPdfExtensionError(SeparadorNominasError):
    """El archivo no tiene extensión PDF."""


class CorruptedPdfError(SeparadorNominasError):
    """El PDF está dañado o no puede abrirse."""


class PasswordProtectedPdfError(SeparadorNominasError):
    """El PDF está protegido con contraseña."""


class EmptyPdfError(SeparadorNominasError):
    """El PDF no contiene páginas."""


class InvalidDestinationError(SeparadorNominasError):
    """La carpeta de destino no es válida."""


class PermissionDeniedError(SeparadorNominasError):
    """Permisos insuficientes para leer o escribir."""


class PdfReadError(SeparadorNominasError):
    """Error al leer el PDF de origen."""


class PdfWriteError(SeparadorNominasError):
    """Error al escribir un archivo PDF de salida."""


class SelectionCancelledError(SeparadorNominasError):
    """El usuario canceló la selección en el diálogo."""


class UnexpectedError(SeparadorNominasError):
    """Error inesperado no clasificado."""


class EmptyGroupNameError(SeparadorNominasError):
    """El nombre del grupo está vacío."""


class InvalidGroupNameError(SeparadorNominasError):
    """El nombre del grupo no es válido o el grupo no existe."""


class DuplicateGroupNameError(SeparadorNominasError):
    """Ya existe un grupo con el mismo nombre."""


class WorkerNotFoundError(SeparadorNominasError):
    """El trabajador no está en la sesión de clasificación."""


class ClassificationExportError(SeparadorNominasError):
    """Error al exportar la clasificación."""


class SpreadsheetNotSelectedError(SeparadorNominasError):
    """No se ha seleccionado ningún archivo Excel."""


class SpreadsheetNotFoundError(SeparadorNominasError):
    """El archivo Excel no existe."""


class InvalidSpreadsheetExtensionError(SeparadorNominasError):
    """La extensión del Excel no está soportada."""


class SpreadsheetReadError(SeparadorNominasError):
    """No se ha podido leer el archivo Excel."""


class SpreadsheetProtectedError(SeparadorNominasError):
    """El Excel está protegido de forma incompatible."""


class SpreadsheetEmptyError(SeparadorNominasError):
    """La hoja seleccionada no contiene datos útiles."""


class SpreadsheetSheetNotFoundError(SeparadorNominasError):
    """La hoja indicada no existe en el libro."""


class SpreadsheetTooLargeError(SeparadorNominasError):
    """El Excel supera el límite de filas permitido."""


class SpreadsheetColumnError(SeparadorNominasError):
    """No se han podido identificar las columnas necesarias."""
