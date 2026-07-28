"""Ciclo de vida de la sesión de clasificación (solo memoria)."""

from __future__ import annotations

import logging
from pathlib import Path

from separador_nominas.classification_models import ClassificationSession
from separador_nominas.constants import LOGGER_NAME
from separador_nominas.temporary_files_service import TemporaryFilesService

logger = logging.getLogger(LOGGER_NAME)


class SessionService:
    """Mantiene como máximo una sesión activa en memoria."""

    def __init__(
        self,
        *,
        temporary_files: TemporaryFilesService | None = None,
    ) -> None:
        self._session: ClassificationSession | None = None
        self.temporary_files = temporary_files or TemporaryFilesService()

    @property
    def session(self) -> ClassificationSession | None:
        """Sesión actual o ``None``."""
        return self._session

    def set_session(self, session: ClassificationSession) -> ClassificationSession:
        """
        Sustituye la sesión activa.

        Si ya había una, se limpia antes (sin borrar PDFs de destino).
        """
        if self._session is not None:
            self.clear_session()
        self._session = session
        logger.info(
            "Sesión de clasificación iniciada: %s páginas, %s trabajadores",
            session.page_count,
            len(session.workers),
        )
        return session

    def clear_session(self) -> None:
        """Vacía trabajadores, grupos y referencias; limpia temporales."""
        if self._session is not None:
            self._session.workers.clear()
            self._session.groups.clear()
            self._session = None
        self.temporary_files.cleanup()
        logger.info("Sesión de clasificación limpiada")

    def has_session(self) -> bool:
        """True si hay una sesión activa."""
        return self._session is not None

    def require_session(self) -> ClassificationSession:
        """Devuelve la sesión o lanza ``RuntimeError`` (uso interno)."""
        if self._session is None:
            raise RuntimeError("No hay sesión de clasificación activa")
        return self._session

    def replace_source_pdf(self, source_pdf: Path) -> None:
        """Indica cambio de PDF: limpia la sesión previa."""
        if self._session is not None:
            self.clear_session()
        _ = source_pdf  # la nueva sesión se crea tras el análisis
