"""Prueba de integración del flujo de clasificación (§30 del plan)."""

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


def test_integration_ten_page_classification(tmp_path: Path) -> None:
    pages = [
        ["NOMBRE Y APELLIDOS: Ana Garcia Lopez", "DNI: 12345678Z"],
        ["NOMBRE Y APELLIDOS: Pedro Martinez Ruiz", "DNI: 23456789D"],
        ["NOMBRE Y APELLIDOS: Laura Perez Gil", "DNI: 34567890V"],
        ["NOMBRE Y APELLIDOS: Ana Garcia Lopez", "DNI: 12345678Z"],
        ["NOMBRE Y APELLIDOS: Maria Ruiz Lopez", "NIE: X1234567L"],
        [],  # no reconocida
        ["NOMBRE Y APELLIDOS: Pedro Martinez Ruiz", "DNI: 23456789D"],
        ["NOMBRE Y APELLIDOS: Juan Sanchez Perez", "DNI: 45678901G"],
        ["texto sin etiquetas utiles"],
        ["NOMBRE Y APELLIDOS: Elena Garcia Ruiz", "NIE: Y7654321G"],
    ]
    pdf = write_text_pdf(tmp_path / "nominas.pdf", pages)
    session = analyze_classification_pdf(pdf)

    almacen = create_group(session, "Almacen", export_mode="combined")
    admin = create_group(session, "Administracion", export_mode="separate")
    add_workers_to_group(
        session,
        almacen.group_id,
        [
            document_worker_id("12345678Z"),
            document_worker_id("23456789D"),
        ],
    )
    add_workers_to_group(
        session,
        admin.group_id,
        [
            document_worker_id("X1234567L"),
            document_worker_id("Y7654321G"),
        ],
    )

    dest = tmp_path / "Nominas_clasificadas"
    result = export_classification_session(session, dest)

    combined = dest / "Almacen" / "Nominas_Almacen.pdf"
    assert combined.exists()
    assert len(PdfReader(str(combined)).pages) == 4

    admin_files = sorted((dest / "Administracion").glob("*.pdf"))
    assert len(admin_files) == 2

    unrecognized = sorted((dest / "No_reconocidas").glob("*.pdf"))
    assert len(unrecognized) == 2
    assert result.files_created == 1 + 2 + 2
