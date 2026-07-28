#!/usr/bin/env python3
"""Genera un PDF sintético de 1500 nóminas para probar clasificación por grupos.

Solo datos ficticios. No usar datos personales reales.
Salida por defecto: pruebas/nominas_1500_clasificacion.pdf
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

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

# Grupos sugeridos para la prueba manual (solo leyenda; no van en el PDF).
SUGGESTED_GROUPS = (
    "Almacen",
    "Administracion",
    "Produccion",
    "Direccion",
    "Reparto",
    "Delegacion_Murcia",
    "Delegacion_Almeria",
)


def dni_from_number(number: int) -> str:
    return f"{number:08d}{_CONTROL[number % 23]}"


def nie_from(prefix: str, seven: int) -> str:
    value = _NIE_PREFIX[prefix] * 10_000_000 + seven
    return f"{prefix}{seven:07d}{_CONTROL[value % 23]}"


def full_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST)} {rng.choice(LAST)} {rng.choice(LAST)}"


def page_normal(name: str, doc: str, *, dept_hint: str) -> list[str]:
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"DEPARTAMENTO REF: {dept_hint}",
        f"NOMBRE Y APELLIDOS: {name}",
        f"DNI: {doc}",
        "PERIODO: 07/2026",
    ]


def page_nie(name: str, doc: str, *, dept_hint: str) -> list[str]:
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"DEPARTAMENTO REF: {dept_hint}",
        f"NOMBRE Y APELLIDOS: {name}",
        f"NIE: {doc}",
        "PERIODO: 07/2026",
    ]


def page_spaced_dni(name: str, doc: str) -> list[str]:
    spaced = f"{doc[:2]} {doc[2:5]} {doc[5:8]}-{doc[8]}"
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"NOMBRE Y APELLIDOS: {name}",
        f"D.N.I.: {spaced}",
    ]


def page_name_only(name: str) -> list[str]:
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"NOMBRE Y APELLIDOS: {name}",
        "SIN DOCUMENTO EN ESTA PAGINA",
    ]


def page_blank() -> list[str]:
    return []


def page_noise() -> list[str]:
    return [
        "DOCUMENTO INTERNO",
        "CIF EMPRESA: B12345674",
        "sin etiquetas de trabajador",
    ]


def page_bad_letter(name: str, number: int) -> list[str]:
    wrong = f"{number:08d}A"  # letra probablemente incorrecta
    if wrong == dni_from_number(number):
        wrong = f"{number:08d}B"
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"NOMBRE Y APELLIDOS: {name}",
        f"DNI: {wrong}",
    ]


def page_multi_docs(name: str, worker_doc: str) -> list[str]:
    return [
        "RECIBO DE SALARIOS (SINTETICO)",
        f"NOMBRE Y APELLIDOS: {name}",
        f"DNI: {worker_doc}",
        "DOCUMENTO ANTERIOR: 00000000T",
    ]


def build_pages(total: int, seed: int) -> tuple[list[list[str]], list[str]]:
    rng = random.Random(seed)
    pages: list[list[str]] = []
    legend: list[str] = [
        "PDF sintético para clasificación (datos ficticios).",
        f"Total páginas: {total}",
        f"Semilla: {seed}",
        "",
        "Grupos sugeridos para la prueba manual:",
        *[f"  - {g}" for g in SUGGESTED_GROUPS],
        "",
        "Casos incluidos:",
        "  - DNI+nombre (mayoría), repartidos por DEPARTAMENTO REF",
        "  - Varias páginas del mismo DNI (nómina + paga extra)",
        "  - Mismo DNI con nombres distintos (advertencia name_mismatch)",
        "  - Mismo nombre con DNI distinto (dos trabajadores)",
        "  - NIE X/Y/Z",
        "  - DNI con espacios/guiones",
        "  - Letra de control incorrecta",
        "  - Solo nombre (sin DNI) → TEMP/parcial",
        "  - Página en blanco / ruido sin trabajador",
        "  - Varios documentos en la misma página",
        "",
        "Distribución aproximada de DEPARTAMENTO REF (para agrupar):",
    ]

    # Pool de números DNI únicos.
    used_numbers: set[int] = set()

    def next_dni() -> str:
        while True:
            n = rng.randint(10_000_000, 99_999_999)
            if n not in used_numbers:
                used_numbers.add(n)
                return dni_from_number(n)

    def next_nie(prefix: str) -> str:
        while True:
            seven = rng.randint(0, 9_999_999)
            key = _NIE_PREFIX[prefix] * 10_000_000 + seven
            if key not in used_numbers:
                used_numbers.add(key)
                return nie_from(prefix, seven)

    # Trabajadores "estables" por departamento (para poder agrupar con sentido).
    workers_by_dept: dict[str, list[tuple[str, str]]] = {g: [] for g in SUGGESTED_GROUPS}
    for dept in SUGGESTED_GROUPS:
        count = 80 if dept != "Direccion" else 40
        for _ in range(count):
            workers_by_dept[dept].append((full_name(rng), next_dni()))

    # --- Casos especiales (reservar ~350 páginas) ---
    specials: list[list[str]] = []

    # Multi-página mismo DNI (50 trabajadores × 2 = 100 páginas)
    multi_workers = [
        (full_name(rng), next_dni(), rng.choice(SUGGESTED_GROUPS))
        for _ in range(50)
    ]
    for name, doc, dept in multi_workers:
        specials.append(page_normal(name, doc, dept_hint=dept))
        specials.append(
            page_normal(name, doc, dept_hint=dept)[:-1]
            + ["CONCEPTO: PAGA EXTRAORDINARIA"]
        )

    # Name mismatch mismo DNI (20 × 2)
    for _ in range(20):
        doc = next_dni()
        dept = rng.choice(SUGGESTED_GROUPS)
        specials.append(page_normal(full_name(rng), doc, dept_hint=dept))
        specials.append(page_normal(full_name(rng), doc, dept_hint=dept))

    # Mismo nombre, DNI distinto (15 pares = 30)
    for _ in range(15):
        name = full_name(rng)
        dept = rng.choice(SUGGESTED_GROUPS)
        specials.append(page_normal(name, next_dni(), dept_hint=dept))
        specials.append(page_normal(name, next_dni(), dept_hint=dept))

    # NIE X/Y/Z (60)
    for prefix in ("X", "Y", "Z"):
        for _ in range(20):
            dept = rng.choice(SUGGESTED_GROUPS)
            specials.append(
                page_nie(full_name(rng), next_nie(prefix), dept_hint=dept)
            )

    # DNI con espacios (40)
    for _ in range(40):
        specials.append(page_spaced_dni(full_name(rng), next_dni()))

    # Letra incorrecta (40)
    for _ in range(40):
        n = rng.randint(10_000_000, 99_999_999)
        used_numbers.add(n)
        specials.append(page_bad_letter(full_name(rng), n))

    # Solo nombre (50)
    for _ in range(50):
        specials.append(page_name_only(full_name(rng)))

    # Blancas / ruido (40)
    for _ in range(20):
        specials.append(page_blank())
    for _ in range(20):
        specials.append(page_noise())

    # Multi-documento en página (30)
    for _ in range(30):
        specials.append(page_multi_docs(full_name(rng), next_dni()))

    rng.shuffle(specials)

    # Relleno con trabajadores por departamento hasta `total`.
    filler: list[list[str]] = []
    dept_cycle = list(SUGGESTED_GROUPS)
    idx = 0
    while len(specials) + len(filler) < total:
        dept = dept_cycle[idx % len(dept_cycle)]
        idx += 1
        pool = workers_by_dept[dept]
        name, doc = pool[rng.randint(0, len(pool) - 1)]
        # ~15% segunda página del mismo trabajador intercalada vía reutilizar
        if rng.random() < 0.12:
            filler.append(page_normal(name, doc, dept_hint=dept))
        filler.append(page_normal(name, doc, dept_hint=dept))

    pages = (specials + filler)[:total]
    rng.shuffle(pages)

    # Conteo por hint de departamento en leyenda
    from collections import Counter

    hints = Counter()
    for page in pages:
        for line in page:
            if line.startswith("DEPARTAMENTO REF: "):
                hints[line.split(": ", 1)[1]] += 1
                break
        else:
            hints["(sin hint / especial)"] += 1

    for dept, count in sorted(hints.items()):
        legend.append(f"  - {dept}: {count} páginas (aprox.)")
    legend.append("")
    legend.append(
        "Nota: DEPARTAMENTO REF es solo ayuda visual en el PDF; la app no "
        "agrupa automáticamente por ese campo. Debes crear los grupos a mano."
    )

    return pages, legend


def write_pdf(path: Path, pages: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path))
    for lines in pages:
        if lines:
            y = 800
            for line in lines:
                pdf.drawString(50, y, line[:110])
                y -= 16
        pdf.showPage()
    pdf.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pages",
        type=int,
        default=1500,
        help="Número de páginas (default 1500)",
    )
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta del PDF de salida",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    pruebas = root / "pruebas"
    out = args.out or (pruebas / "nominas_1500_clasificacion.pdf")

    pages, legend = build_pages(args.pages, args.seed)
    write_pdf(out, pages)

    legend_path = out.with_name(out.stem + "_LEYENDA.txt")
    legend_path.write_text("\n".join(legend) + "\n", encoding="utf-8")

    # Copia adicional en subcarpeta de entrada de pruebas.
    entrada = pruebas / "entrada_clasificacion"
    entrada.mkdir(parents=True, exist_ok=True)
    dest_copy = entrada / out.name
    dest_copy.write_bytes(out.read_bytes())
    (entrada / legend_path.name).write_text(
        legend_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Carpeta destino vacía sugerida para la app.
    (pruebas / "salida_clasificacion").mkdir(parents=True, exist_ok=True)

    print(f"PDF: {out} ({args.pages} páginas, {out.stat().st_size} bytes)")
    print(f"Copia: {dest_copy}")
    print(f"Leyenda: {legend_path}")
    print(f"Destino sugerido: {pruebas / 'salida_clasificacion'}")


if __name__ == "__main__":
    main()
