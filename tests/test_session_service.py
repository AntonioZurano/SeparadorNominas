"""Tests de sesión y archivos temporales."""

from __future__ import annotations

from pathlib import Path

from separador_nominas.classification_models import (
    ClassificationSession,
    WorkerRecord,
)
from separador_nominas.session_service import SessionService
from separador_nominas.temporary_files_service import TemporaryFilesService


def test_clear_session_empties_workers_and_groups(tmp_path: Path) -> None:
    temps = TemporaryFilesService()
    temp_dir = temps.create_temp_dir()
    (temp_dir / "marker.txt").write_text("x", encoding="utf-8")

    service = SessionService(temporary_files=temps)
    session = ClassificationSession(
        source_pdf=tmp_path / "a.pdf",
        page_count=1,
        workers={
            "DOC:1": WorkerRecord(
                worker_id="DOC:1",
                document_id="12345678Z",
                display_name="A",
                normalized_name="a",
                page_numbers=[1],
                recognition_status="recognized",
            )
        },
        groups={},
    )
    service.set_session(session)
    assert service.has_session()
    service.clear_session()
    assert not service.has_session()
    assert not temp_dir.exists()


def test_set_session_clears_previous() -> None:
    service = SessionService()
    first = ClassificationSession(
        source_pdf=Path("a.pdf"), page_count=1, workers={}, groups={}
    )
    second = ClassificationSession(
        source_pdf=Path("b.pdf"), page_count=2, workers={}, groups={}
    )
    service.set_session(first)
    service.set_session(second)
    assert service.session is second
    assert service.session.page_count == 2
