"""Utilidades de registro técnico sin volcar datos de usuario."""

from __future__ import annotations

import logging


def log_unexpected_error(
    logger: logging.Logger,
    operation_id: str,
    exc: BaseException,
) -> None:
    """
    Registra un error inesperado con contexto mínimo de diagnóstico.

    Solo escribe el identificador de operación (fijo, definido por la app) y
    el nombre del tipo de excepción. No registra ``str(exc)``, ``repr(exc)``,
    ``args`` ni ``exc_info``/traceback, que pueden incluir rutas u otros
    datos procedentes de archivos o del sistema.

    ``operation_id`` debe ser un literal controlado por la aplicación
    (p. ej. ``\"inspect_pdf\"``), nunca una ruta ni texto introducido por
    el usuario.
    """
    logger.error(
        "Error inesperado en %s: %s",
        operation_id,
        type(exc).__name__,
        exc_info=False,
    )
