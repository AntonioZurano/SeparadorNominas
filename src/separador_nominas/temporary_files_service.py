"""Gestión de archivos temporales sensibles (limpieza garantizada)."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from separador_nominas.constants import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class TemporaryFilesService:
    """Registra directorios temporales y los elimina al limpiar."""

    def __init__(self) -> None:
        self._dirs: list[Path] = []

    def create_temp_dir(self, *, prefix: str = "separador_nominas_") -> Path:
        """Crea un directorio temporal del sistema y lo registra."""
        path = Path(tempfile.mkdtemp(prefix=prefix))
        self._dirs.append(path)
        logger.info("Directorio temporal creado")
        return path

    def register(self, path: Path | str) -> Path:
        """Registra una ruta ya existente para limpieza posterior."""
        resolved = Path(path)
        if resolved not in self._dirs:
            self._dirs.append(resolved)
        return resolved

    def cleanup(self) -> None:
        """
        Elimina todos los directorios registrados.

        En Windows un archivo bloqueado puede impedir el borrado; se registra
        el tipo de error sin rutas ni contenido.
        """
        remaining: list[Path] = []
        for path in self._dirs:
            try:
                if path.exists():
                    shutil.rmtree(path, ignore_errors=False)
            except OSError:
                logger.warning(
                    "No se ha podido eliminar un directorio temporal "
                    "(posible bloqueo de archivo)"
                )
                remaining.append(path)
        self._dirs = remaining

    @property
    def tracked_count(self) -> int:
        """Número de directorios aún registrados."""
        return len(self._dirs)
