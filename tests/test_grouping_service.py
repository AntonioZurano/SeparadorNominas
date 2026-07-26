"""Tests de agrupación por nombre normalizado."""

from __future__ import annotations

from separador_nominas.grouping_service import build_employee_groups
from separador_nominas.recognition_models import PageRecognitionResult


def _high(
    page_index: int,
    display: str,
    key: str,
) -> PageRecognitionResult:
    return PageRecognitionResult(
        page_index=page_index,
        page_number=page_index + 1,
        has_text=True,
        detected_name=display,
        display_name=display,
        normalized_key=key,
        confidence="high",
    )


def _none(page_index: int) -> PageRecognitionResult:
    return PageRecognitionResult(
        page_index=page_index,
        page_number=page_index + 1,
        has_text=False,
        detected_name=None,
        display_name=None,
        normalized_key=None,
        confidence="none",
        warning_code="no_text",
    )


class TestBuildEmployeeGroups:
    def test_groups_same_key_and_order(self) -> None:
        pages = [
            _high(0, "Ana Perez", "ana perez"),
            _high(1, "Pedro Ruiz", "pedro ruiz"),
            _high(2, "Ana Pérez", "ana perez"),
            _none(3),
        ]
        groups, unrecognized = build_employee_groups(pages)

        assert len(groups) == 2
        assert groups[0].display_name == "Ana Perez"
        assert groups[0].page_numbers == (1, 3)
        assert groups[1].page_numbers == (2,)
        assert unrecognized == (4,)

    def test_distinct_keys_not_merged(self) -> None:
        pages = [
            _high(0, "Ana Perez", "ana perez"),
            _high(1, "Ana Perez Lopez", "ana perez lopez"),
        ]
        groups, unrecognized = build_employee_groups(pages)
        assert len(groups) == 2
        assert unrecognized == ()
