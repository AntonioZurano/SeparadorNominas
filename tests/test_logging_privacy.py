"""Privacidad en logs de excepciones (marcadores sintéticos, sin datos reales)."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest

from separador_nominas.constants import LOGGER_NAME
from separador_nominas.exceptions import PdfNotFoundError
from separador_nominas.logging_utils import log_unexpected_error

# Marcadores reconocibles; no son datos personales reales.
SYN_PATH_MARKER = "SYN_PATH_MARKER"
SYN_NAME_MARKER = "SYN_NAME_MARKER"
SYN_DNI_MARKER = "SYN_DNI_00000000T"
SYN_CELL_MARKER = "SYN_CELL_MARKER"


def _formatted_log_blob(caplog: pytest.LogCaptureFixture) -> str:
    """Texto formateado completo de cada LogRecord (incluye traceback si hay)."""
    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    parts: list[str] = []
    for record in caplog.records:
        parts.append(formatter.format(record))
    return "\n".join(parts)


def _assert_no_synthetic_leak(blob: str) -> None:
    assert SYN_PATH_MARKER not in blob
    assert SYN_NAME_MARKER not in blob
    assert SYN_DNI_MARKER not in blob
    assert SYN_CELL_MARKER not in blob


def _make_sensitive_os_error(tmp_path: Path) -> OSError:
    sensitive = tmp_path / SYN_PATH_MARKER / f"{SYN_NAME_MARKER}.pdf"
    sensitive.parent.mkdir(parents=True, exist_ok=True)
    return OSError(2, f"No such file: {SYN_CELL_MARKER}", str(sensitive))


@pytest.fixture
def app_root():
    """Tk mínimo; se omite si no hay display usable."""
    tkinter = pytest.importorskip("tkinter")
    try:
        root = tkinter.Tk()
    except tkinter.TclError as exc:
        pytest.skip(f"Sin display Tk usable: {exc}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(app_root):
    from separador_nominas.gui import SeparadorNominasApp

    return SeparadorNominasApp(app_root)


def test_log_unexpected_error_omits_sensitive_markers(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    err = _make_sensitive_os_error(tmp_path)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    try:
        with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
            log_unexpected_error(logger, "inspect_pdf", err)
        blob = _formatted_log_blob(caplog) + "\n" + stream.getvalue()
    finally:
        logger.removeHandler(handler)

    _assert_no_synthetic_leak(blob)
    assert "inspect_pdf" in blob
    assert type(err).__name__ in blob
    assert "ERROR" in blob
    assert "Traceback" not in blob


def test_run_inspect_pdf_unexpected_log_privacy(
    app,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    err = _make_sensitive_os_error(tmp_path)

    def boom(_path: object) -> object:
        raise err

    monkeypatch.setattr("separador_nominas.gui.inspect_pdf", boom)
    monkeypatch.setattr(app, "_on_pdf_inspect_error", lambda _msg: None)

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        app._run_inspect_pdf(str(tmp_path / SYN_PATH_MARKER / "x.pdf"))

    blob = _formatted_log_blob(caplog)
    _assert_no_synthetic_leak(blob)
    assert "inspect_pdf" in blob
    assert type(err).__name__ in blob
    assert "Traceback" not in blob


def test_run_split_unexpected_log_privacy(
    app,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    err = _make_sensitive_os_error(tmp_path)

    def boom(*_a: object, **_k: object) -> object:
        raise err

    monkeypatch.setattr("separador_nominas.gui.split_pdf", boom)
    monkeypatch.setattr(app, "_on_process_error", lambda _msg: None)

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        app._run_split("pdf", "dest", "base")

    blob = _formatted_log_blob(caplog)
    _assert_no_synthetic_leak(blob)
    assert "split_pdf" in blob
    assert type(err).__name__ in blob
    assert "Traceback" not in blob


def test_run_classify_excel_unexpected_log_privacy(
    app,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    err = _make_sensitive_os_error(tmp_path)

    def boom(*_a: object, **_k: object) -> object:
        raise err

    monkeypatch.setattr(
        "separador_nominas.gui.import_department_assignments", boom
    )
    monkeypatch.setattr(app, "_on_process_error", lambda _msg: None)

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        app._run_classify_excel_analyze(
            "pdf", "excel", "dest", None, None
        )

    blob = _formatted_log_blob(caplog)
    _assert_no_synthetic_leak(blob)
    assert "classify_excel_analyze" in blob
    assert type(err).__name__ in blob
    assert "Traceback" not in blob


def test_domain_error_with_cause_does_not_log_path(
    app,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cause = _make_sensitive_os_error(tmp_path)
    domain = PdfNotFoundError("El archivo PDF seleccionado no existe.")
    domain.__cause__ = cause

    def boom(_path: object) -> object:
        raise domain

    monkeypatch.setattr("separador_nominas.gui.inspect_pdf", boom)
    monkeypatch.setattr(app, "_on_pdf_inspect_error", lambda _msg: None)

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        app._run_inspect_pdf("ignored.pdf")

    blob = _formatted_log_blob(caplog)
    _assert_no_synthetic_leak(blob)
    assert "Traceback" not in blob


def test_chained_unexpected_markers_not_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    inner = FileNotFoundError(
        f"{SYN_PATH_MARKER} {SYN_DNI_MARKER} {SYN_NAME_MARKER} {SYN_CELL_MARKER}"
    )
    outer = RuntimeError("wrapper")
    outer.__cause__ = inner

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        log_unexpected_error(logger, "export_classification", outer)

    blob = _formatted_log_blob(caplog)
    _assert_no_synthetic_leak(blob)
    assert "export_classification" in blob
    assert "RuntimeError" in blob
    assert "Traceback" not in blob
