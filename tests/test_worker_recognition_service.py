"""Tests de consolidación de trabajadores por DNI/NIE."""

from __future__ import annotations

from separador_nominas.worker_recognition_service import (
    build_workers_from_pages,
    document_worker_id,
    temp_worker_id,
)


def _page(name: str, doc: str) -> str:
    return f"NOMBRE Y APELLIDOS: {name}\nDNI: {doc}\n"


def test_one_page_per_worker() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Juan Perez Ruiz", "23456789D"),
        ]
    )
    assert len(workers) == 2
    ana = workers[document_worker_id("12345678Z")]
    assert ana.page_numbers == [1]
    assert ana.recognition_status == "recognized"


def test_same_dni_multiple_pages_merged() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Pedro Martinez", "23456789D"),
            _page("Ana Garcia Lopez", "12345678Z"),
        ]
    )
    ana = workers[document_worker_id("12345678Z")]
    assert ana.page_numbers == [1, 3]


def test_same_dni_name_mismatch_warning() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Ana Gomez Lopez", "12345678Z"),
        ]
    )
    ana = workers[document_worker_id("12345678Z")]
    assert "name_mismatch" in ana.warnings
    assert ana.page_numbers == [1, 2]


def test_same_name_different_dni_are_distinct() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Ana Garcia Lopez", "87654321X"),
        ]
    )
    assert len(workers) == 2


def test_without_dni_creates_temp_per_page() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            "NOMBRE Y APELLIDOS: Ana Garcia Lopez\n",
            "sin datos\n",
        ]
    )
    assert temp_worker_id(1) in workers
    assert temp_worker_id(2) in workers
    assert workers[temp_worker_id(1)].recognition_status == "partial"
    assert workers[temp_worker_id(2)].recognition_status == "unrecognized"


def test_interleaved_pages_keep_order() -> None:
    workers = build_workers_from_pages(
        page_texts=[
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Pedro Martinez", "23456789D"),
            _page("Ana Garcia Lopez", "12345678Z"),
            _page("Pedro Martinez", "23456789D"),
        ]
    )
    assert workers[document_worker_id("12345678Z")].page_numbers == [1, 3]
    assert workers[document_worker_id("23456789D")].page_numbers == [2, 4]
