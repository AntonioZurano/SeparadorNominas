"""Utilidades de prueba para generar PDF sintéticos con texto (sin datos reales)."""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas


def write_text_pdf(path: Path, pages_lines: list[list[str]]) -> Path:
    """
    Escribe un PDF con una página por elemento de ``pages_lines``.

    Cada página contiene las líneas de texto indicadas (síntesis para tests).
    Una lista vacía genera una página en blanco sin texto seleccionable útil.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    for lines in pages_lines:
        if lines:
            y = 780
            for line in lines:
                pdf.drawString(72, y, line)
                y -= 18
        pdf.showPage()
    pdf.save()
    return path
