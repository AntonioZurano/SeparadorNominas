"""Tests del servicio de grupos y asignaciones."""

from __future__ import annotations

from pathlib import Path

import pytest

from separador_nominas.classification_models import (
    ClassificationSession,
    WorkerRecord,
)
from separador_nominas.classification_service import (
    add_workers_to_group,
    create_group,
    delete_group,
    remove_workers_from_group,
    rename_group,
    set_export_mode,
    unassigned_worker_ids,
    workers_in_multiple_groups,
)
from separador_nominas.exceptions import (
    DuplicateGroupNameError,
    EmptyGroupNameError,
)


def _session() -> ClassificationSession:
    workers = {
        "DOC:12345678Z": WorkerRecord(
            worker_id="DOC:12345678Z",
            document_id="12345678Z",
            display_name="Ana Garcia Lopez",
            normalized_name="ana garcia lopez",
            page_numbers=[1, 4],
            recognition_status="recognized",
        ),
        "DOC:23456789D": WorkerRecord(
            worker_id="DOC:23456789D",
            document_id="23456789D",
            display_name="Juan Perez",
            normalized_name="juan perez",
            page_numbers=[2],
            recognition_status="recognized",
        ),
        "TEMP-PAGE-003": WorkerRecord(
            worker_id="TEMP-PAGE-003",
            document_id=None,
            display_name=None,
            normalized_name=None,
            page_numbers=[3],
            recognition_status="unrecognized",
        ),
    }
    return ClassificationSession(
        source_pdf=Path("synthetic.pdf"),
        page_count=4,
        workers=workers,
        groups={},
    )


def test_create_rename_delete_group() -> None:
    session = _session()
    group = create_group(session, "Almacén")
    assert group.safe_folder_name
    rename_group(session, group.group_id, "Almacen Norte")
    assert session.groups[group.group_id].display_name == "Almacen Norte"
    delete_group(session, group.group_id)
    assert group.group_id not in session.groups


def test_duplicate_and_empty_group_name() -> None:
    session = _session()
    create_group(session, "Almacen")
    with pytest.raises(DuplicateGroupNameError):
        create_group(session, "almacen")
    with pytest.raises(EmptyGroupNameError):
        create_group(session, "   ")


def test_add_remove_and_multi_assignment() -> None:
    session = _session()
    g1 = create_group(session, "Almacen")
    g2 = create_group(session, "Comite")
    add_workers_to_group(session, g1.group_id, ["DOC:12345678Z"])
    add_workers_to_group(session, g2.group_id, ["DOC:12345678Z"])
    assert workers_in_multiple_groups(session) == ["DOC:12345678Z"]
    added, skipped = add_workers_to_group(
        session, g1.group_id, ["DOC:12345678Z"]
    )
    assert added == 0 and skipped == 1
    remove_workers_from_group(session, g1.group_id, ["DOC:12345678Z"])
    assert "DOC:12345678Z" not in session.groups[g1.group_id].worker_ids


def test_unassigned_and_export_mode() -> None:
    session = _session()
    g1 = create_group(session, "Almacen", export_mode="separate")
    set_export_mode(session, g1.group_id, "combined")
    assert session.groups[g1.group_id].export_mode == "combined"
    add_workers_to_group(session, g1.group_id, ["DOC:12345678Z"])
    unassigned = unassigned_worker_ids(session)
    assert "DOC:23456789D" in unassigned
    assert "DOC:12345678Z" not in unassigned
