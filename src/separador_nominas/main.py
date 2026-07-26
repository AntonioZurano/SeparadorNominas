"""Punto de entrada de Separador de Nóminas PDF."""

from __future__ import annotations

import logging
import sys

from separador_nominas.constants import (
    APP_NAME,
    APP_VERSION,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOGGER_NAME,
)


def configure_logging(*, to_console: bool = True) -> None:
    """
    Configura el registro técnico básico.

    No escribe archivos permanentes ni datos personales.
    En el ejecutable empaquetado se limita a WARNING si no hay consola.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # En ejecutable sin consola (--noconsole), reducir ruido.
    frozen = getattr(sys, "frozen", False)
    if frozen:
        handler.setLevel(logging.WARNING)
    else:
        handler.setLevel(logging.INFO if to_console else logging.WARNING)

    logger.addHandler(handler)
    logger.propagate = False


def main() -> int:
    """Arranca la aplicación gráfica."""
    configure_logging()
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("Inicio de %s v%s", APP_NAME, APP_VERSION)

    try:
        from separador_nominas.gui import run_app

        run_app()
    except ModuleNotFoundError as exc:
        if "tkinter" in str(exc).lower():
            logger.error("Tkinter no está disponible en este entorno")
            print(
                "No se ha podido iniciar la interfaz gráfica.\n"
                "Tkinter no está instalado en este Python.\n"
                "En Windows suele venir incluido; "
                "en Linux instala el paquete python3-tk.",
                file=sys.stderr,
            )
            return 1
        raise
    except Exception:  # noqa: BLE001
        logger.exception("Error inesperado al arrancar la aplicación")
        return 1

    logger.info("Aplicación finalizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
