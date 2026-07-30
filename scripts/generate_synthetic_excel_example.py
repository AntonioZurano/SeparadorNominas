#!/usr/bin/env python3
"""Genera PDF + Excel sintéticos para probar el modo classify_excel (v2.5).

Solo datos ficticios. No usar datos personales reales.
Salida por defecto: pruebas/entrada_excel/
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import Workbook
from reportlab.pdfgen import canvas

# DNI/NIE con letra de control válida (ficticios).
WORKERS: list[tuple[str, str, str]] = [
    # name, document_id, department
    ("Ana Garcia Lopez", "11111111H", "Almacén"),
    ("Juan Perez Ruiz", "22222222J", "Administración"),
    ("Luis Martinez Gil", "33333333P", "Almacén"),
    ("Nuria Sanchez Diaz", "X1234567L", "Producción"),
    ("Pedro Lopez Nieto", "23456789D", "Dirección"),
    ("Maria Romero Torres", "12345678Z", "Producción"),
]

# Documento solo en Excel (no aparece en el PDF).
EXCEL_ONLY = ("44444444A", "Reparto")


def write_pdf(path: Path) -> None:
    """PDF: 8 páginas (incluye 2.ª nómina de Ana y una sin DNI)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))

    pages: list[list[str]] = [
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[0][0]}",
            f"DNI: {WORKERS[0][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[1][0]}",
            f"DNI: {WORKERS[1][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[2][0]}",
            f"DNI: {WORKERS[2][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[0][0]}",
            f"DNI: {WORKERS[0][1]}",
            "PERIODO: PAGA EXTRA 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[3][0]}",
            f"NIE: {WORKERS[3][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[4][0]}",
            f"DNI: {WORKERS[4][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "RECIBO DE SALARIOS (SINTETICO)",
            f"NOMBRE Y APELLIDOS: {WORKERS[5][0]}",
            f"DNI: {WORKERS[5][1]}",
            "PERIODO: 07/2026",
        ],
        [
            "PAGINA SIN DOCUMENTO (SINTETICO)",
            "Texto de relleno sin DNI ni NIE",
        ],
    ]

    for lines in pages:
        y = 780
        for line in lines:
            pdf.drawString(72, y, line)
            y -= 18
        pdf.showPage()
    pdf.save()


def write_xlsx(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Departamentos"
    sheet.append(["DNI/NIE", "Departamento"])
    for _name, doc, dept in WORKERS:
        sheet.append([doc, dept])
    sheet.append([EXCEL_ONLY[0], EXCEL_ONLY[1]])
    # Duplicado benigno (mismo depto)
    sheet.append([WORKERS[0][1], WORKERS[0][2]])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()


def write_xls(path: Path) -> None:
    import xlwt

    book = xlwt.Workbook()
    sheet = book.add_sheet("Departamentos")
    sheet.write(0, 0, "DNI/NIE")
    sheet.write(0, 1, "Departamento")
    row = 1
    for _name, doc, dept in WORKERS:
        sheet.write(row, 0, doc)
        sheet.write(row, 1, dept)
        row += 1
    sheet.write(row, 0, EXCEL_ONLY[0])
    sheet.write(row, 1, EXCEL_ONLY[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(str(path))


def write_leyenda(path: Path) -> None:
    lines = [
        "Material sintético para modo «Clasificar automáticamente mediante Excel».",
        "Solo datos ficticios. No usar nóminas ni Excel reales.",
        "",
        "Archivos:",
        "  - nominas_excel_ejemplo.pdf   (8 páginas)",
        "  - departamentos_ejemplo.xlsx",
        "  - departamentos_ejemplo.xls",
        "",
        "PDF → páginas:",
        "  1,4  Ana Garcia Lopez   11111111H  → Almacén",
        "  2    Juan Perez Ruiz    22222222J  → Administración",
        "  3    Luis Martinez Gil  33333333P  → Almacén",
        "  5    Nuria Sanchez Diaz X1234567L  → Producción",
        "  6    Pedro Lopez Nieto  23456789D  → Dirección",
        "  7    Maria Romero Torres 12345678Z → Producción",
        "  8    sin DNI                        → No_clasificadas",
        "",
        "Excel sin coincidencia en PDF:",
        f"  - {EXCEL_ONLY[0]} → {EXCEL_ONLY[1]} (aviso; no genera carpeta)",
        "",
        "Salida esperada aproximada:",
        "  Almacén/         páginas 1, 3, 4",
        "  Administración/  página 2",
        "  Producción/      páginas 5, 7",
        "  Dirección/       página 6",
        "  No_clasificadas/ página 8",
        "",
        "Uso en la app:",
        "  1. Modo: Clasificar automáticamente mediante Excel",
        "  2. Seleccionar nominas_excel_ejemplo.pdf",
        "  3. Seleccionar departamentos_ejemplo.xlsx (o .xls)",
        "  4. Analizar con Excel → revisar resumen → Generar",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera PDF+Excel sintéticos para classify_excel."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("pruebas/entrada_excel"),
        help="Carpeta de salida (default: pruebas/entrada_excel)",
    )
    args = parser.parse_args()
    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    write_pdf(out / "nominas_excel_ejemplo.pdf")
    write_xlsx(out / "departamentos_ejemplo.xlsx")
    write_xls(out / "departamentos_ejemplo.xls")
    write_leyenda(out / "LEYENDA.txt")

    print(f"Generado en {out.resolve()}")
    for name in (
        "nominas_excel_ejemplo.pdf",
        "departamentos_ejemplo.xlsx",
        "departamentos_ejemplo.xls",
        "LEYENDA.txt",
    ):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
