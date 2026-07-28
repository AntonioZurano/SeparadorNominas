"""Tests de exportación separada y conjunta por grupos."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from separador_nominas.classification_service import (
    add_workers_to_group,
    create_group,
)
from separador_nominas.group_export_service import export_classification_session
from separador_nominas.worker_recognition_service import (
    analyze_classification_pdf,
    document_worker_id,
)
from tests.pdf_fixtures import write_text_pdf


def _payroll_page(name: str, dni: str) -> list[str]:
    return [f"NOMBRE Y APELLIDOS: {name}", f"DNI: {dni}"]


def test_export_combined_and_separate(tmp_path: Path) -> None:
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [
            _payroll_page("Ana Garcia Lopez", "12345678Z"),
            _payroll_page("Juan Perez Ruiz", "23456789D"),
            _payroll_page("Maria Sanchez Gil", "X1234567L"),
            ["SIN DATOS"],
            _payroll_page("Ana Garcia Lopez", "12345678Z"),
        ],
    )
    session = analyze_classification_pdf(pdf)
    almacen = create_group(session, "Almacen", export_mode="combined")
    admin = create_group(session, "Administracion", export_mode="separate")
    add_workers_to_group(
        session,
        almacen.group_id,
        [document_worker_id("12345678Z"), document_worker_id("23456789D")],
    )
    add_workers_to_group(
        session,
        admin.group_id,
        [document_worker_id("X1234567L")],
    )

    dest = tmp_path / "out"
    result = export_classification_session(session, dest)

    combined = dest / "Almacen" / "Nominas_Almacen.pdf"
    assert combined.exists()
    assert len(PdfReader(str(combined)).pages) == 3  # Ana 1+5, Juan 2

    maria_files = list((dest / "Administracion").glob("*.pdf"))
    assert len(maria_files) == 1
    assert len(PdfReader(str(maria_files[0])).pages) == 1

    unrecognized = list((dest / "No_reconocidas").glob("*.pdf"))
    assert len(unrecognized) == 1
    assert result.unassigned_recognized_count == 0


def test_export_collision_suffix(tmp_path: Path) -> None:
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [_payroll_page("Ana Garcia Lopez", "12345678Z")],
    )
    session = analyze_classification_pdf(pdf)
    group = create_group(session, "Almacen", export_mode="combined")
    add_workers_to_group(
        session, group.group_id, [document_worker_id("12345678Z")]
    )
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "Almacen").mkdir()
    existing = dest / "Almacen" / "Nominas_Almacen.pdf"
    existing.write_bytes(b"%PDF-1.4")

    result = export_classification_session(session, dest)
    names = {p.name for p in result.group_files}
    assert "Nominas_Almacen_2.pdf" in names


def test_empty_group_creates_no_folder(tmp_path: Path) -> None:
    pdf = write_text_pdf(
        tmp_path / "src.pdf",
        [_payroll_page("Ana Garcia Lopez", "12345678Z")],
    )
    session = analyze_classification_pdf(pdf)
    create_group(session, "Vacio", export_mode="combined")
    dest = tmp_path / "out"
    export_classification_session(session, dest)
    assert not (dest / "Vacio").exists()
