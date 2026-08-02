#!/usr/bin/env python3
"""Genera PDF (1000 nóminas) + Excel (~20 departamentos) para prueba de carga.

Solo datos ficticios. Salida: pruebas/entrada_excel_carga/
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from openpyxl import Workbook
from reportlab.pdfgen import canvas

_CONTROL = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX = {"X": 0, "Y": 1, "Z": 2}

FIRST = [
    "Ana", "Juan", "Maria", "Pedro", "Laura", "Carlos", "Elena", "Luis",
    "Sofia", "Diego", "Lucia", "Miguel", "Carmen", "Javier", "Paula",
    "Andres", "Irene", "Roberto", "Nuria", "Pablo", "Clara", "Alberto",
    "Raquel", "Sergio", "Marta", "Hector", "Isabel", "Oscar", "Beatriz",
    "Victor",
]
LAST = [
    "Garcia", "Lopez", "Martinez", "Sanchez", "Perez", "Gonzalez", "Ruiz",
    "Diaz", "Moreno", "Jimenez", "Hernandez", "Alonso", "Romero", "Navarro",
    "Torres", "Dominguez", "Vazquez", "Ramos", "Gil", "Serrano", "Blanco",
    "Molina", "Morales", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio",
    "Marin", "Nieto",
]

DEPARTMENTS = (
    "Almacén",
    "Administración",
    "Producción",
    "Dirección",
    "Reparto",
    "Delegación Murcia",
    "Delegación Almería",
    "Calidad",
    "Logística",
    "Compras",
    "Ventas",
    "RRHH",
    "Finanzas",
    "IT",
    "Mantenimiento",
    "Atención al cliente",
    "Marketing",
    "Legal",
    "Formación",
    "Seguridad",
)


def dni_from_number(number: int) -> str:
    return f"{number:08d}{_CONTROL[number % 23]}"


def nie_from(prefix: str, seven: int) -> str:
    value = _NIE_PREFIX[prefix] * 10_000_000 + seven
    return f"{prefix}{seven:07d}{_CONTROL[value % 23]}"


def full_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)} {rng.choice(LAST)}"


def build_workers(
    *,
    page_count: int,
    dept_count: int,
    seed: int,
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """
    Construye páginas PDF y filas Excel.

    Returns:
        pages_meta: lista por página con name/doc/kind
        excel_rows: (document_id, department) únicos (+ algunos solo Excel)
    """
    rng = random.Random(seed)
    depts = list(DEPARTMENTS[:dept_count])
    if len(depts) < dept_count:
        raise ValueError("No hay suficientes departamentos definidos.")

    # ~85% páginas con DNI único o repetido; resto sin documento / NIE
    workers_by_doc: dict[str, dict[str, object]] = {}
    pages: list[dict[str, object]] = []
    next_dni = 10_000_000 + rng.randint(0, 50_000)

    for page_idx in range(page_count):
        roll = rng.random()
        if roll < 0.08:
            # Página sin DNI
            pages.append(
                {
                    "kind": "blank",
                    "name": None,
                    "doc": None,
                    "dept": None,
                }
            )
            continue

        if roll < 0.12 and workers_by_doc:
            # Segunda página del mismo trabajador
            doc = rng.choice(list(workers_by_doc))
            meta = workers_by_doc[doc]
            pages.append(
                {
                    "kind": "extra",
                    "name": meta["name"],
                    "doc": doc,
                    "dept": meta["dept"],
                }
            )
            continue

        if roll < 0.18:
            prefix = rng.choice(("X", "Y", "Z"))
            seven = rng.randint(1_000_000, 9_999_999)
            doc = nie_from(prefix, seven)
            kind = "nie"
        else:
            next_dni += 1
            doc = dni_from_number(next_dni)
            kind = "dni"

        if doc in workers_by_doc:
            meta = workers_by_doc[doc]
            pages.append(
                {
                    "kind": "extra",
                    "name": meta["name"],
                    "doc": doc,
                    "dept": meta["dept"],
                }
            )
            continue

        name = full_name(rng)
        dept = rng.choice(depts)
        workers_by_doc[doc] = {"name": name, "dept": dept, "kind": kind}
        pages.append({"kind": kind, "name": name, "doc": doc, "dept": dept})

    excel_rows = [
        (doc, str(meta["dept"]))
        for doc, meta in workers_by_doc.items()
    ]
    # Algunos registros solo en Excel (sin PDF)
    for i in range(15):
        next_dni += 1
        excel_rows.append((dni_from_number(next_dni), rng.choice(depts)))

    rng.shuffle(excel_rows)
    return pages, excel_rows


def write_pdf(path: Path, pages: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    for page in pages:
        if page["kind"] == "blank":
            pdf.drawString(72, 780, "PAGINA SIN DOCUMENTO (SINTETICO)")
            pdf.drawString(72, 760, "Texto de relleno sin DNI ni NIE")
        else:
            name = str(page["name"])
            doc = str(page["doc"])
            label = "NIE" if page["kind"] == "nie" else "DNI"
            periodo = (
                "PAGA EXTRA 07/2026"
                if page["kind"] == "extra"
                else "PERIODO: 07/2026"
            )
            pdf.drawString(72, 780, "RECIBO DE SALARIOS (SINTETICO)")
            pdf.drawString(72, 760, f"NOMBRE Y APELLIDOS: {name}")
            pdf.drawString(72, 742, f"{label}: {doc}")
            pdf.drawString(72, 724, periodo)
        pdf.showPage()
    pdf.save()


def write_xlsx(path: Path, rows: list[tuple[str, str]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Departamentos"
    sheet.append(["DNI/NIE", "Departamento"])
    for doc, dept in rows:
        sheet.append([doc, dept])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()


def write_xls(path: Path, rows: list[tuple[str, str]]) -> None:
    import xlwt

    book = xlwt.Workbook()
    sheet = book.add_sheet("Departamentos")
    sheet.write(0, 0, "DNI/NIE")
    sheet.write(0, 1, "Departamento")
    for idx, (doc, dept) in enumerate(rows, start=1):
        sheet.write(idx, 0, doc)
        sheet.write(idx, 1, dept)
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(str(path))


def write_leyenda(
    path: Path,
    *,
    pages: int,
    depts: int,
    excel_rows: int,
    unique_docs: int,
) -> None:
    lines = [
        "Material sintético de CARGA para classify_excel.",
        "Solo datos ficticios.",
        "",
        f"PDF: nominas_1000_excel.pdf ({pages} páginas)",
        f"Excel: departamentos_20.xlsx / .xls (~{depts} departamentos, "
        f"{excel_rows} filas)",
        f"Trabajadores con documento en PDF: ~{unique_docs}",
        "",
        "Departamentos:",
        *[f"  - {d}" for d in DEPARTMENTS[:depts]],
        "",
        "Uso:",
        "  1. Modo Clasificar automáticamente mediante Excel",
        "  2. Seleccionar el PDF",
        "  3. Seleccionar el .xlsx o .xls",
        "  4. Analizar → Generar",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=1000)
    parser.add_argument("--departments", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260730)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("pruebas/entrada_excel_carga"),
    )
    args = parser.parse_args()

    pages_meta, excel_rows = build_workers(
        page_count=args.pages,
        dept_count=args.departments,
        seed=args.seed,
    )
    unique_docs = len({p["doc"] for p in pages_meta if p.get("doc")})

    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    pdf_path = out / "nominas_1000_excel.pdf"
    xlsx_path = out / "departamentos_20.xlsx"
    xls_path = out / "departamentos_20.xls"

    print(f"Generando PDF ({args.pages} páginas)...")
    write_pdf(pdf_path, pages_meta)
    print("Generando Excel xlsx/xls...")
    write_xlsx(xlsx_path, excel_rows)
    write_xls(xls_path, excel_rows)
    write_leyenda(
        out / "LEYENDA.txt",
        pages=args.pages,
        depts=args.departments,
        excel_rows=len(excel_rows),
        unique_docs=unique_docs,
    )
    print(f"Listo en {out.resolve()}")
    print(f"  Documentos únicos en PDF: {unique_docs}")
    print(f"  Filas Excel: {len(excel_rows)}")
    print(f"  Departamentos: {args.departments}")


if __name__ == "__main__":
    main()
