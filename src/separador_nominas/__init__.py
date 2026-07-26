"""Separador de Nóminas PDF: divide un PDF multipágina en archivos individuales."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

__all__ = ["__version__"]


def _read_version() -> str:
    """Obtiene la versión del paquete o del archivo VERSION del proyecto."""
    try:
        return version("separador-nominas")
    except PackageNotFoundError:
        version_file = Path(__file__).resolve().parents[2] / "VERSION"
        if version_file.is_file():
            return version_file.read_text(encoding="utf-8").strip()
        return "1.0.0"


__version__ = _read_version()
