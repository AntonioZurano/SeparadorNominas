"""Agrupación de páginas reconocidas por nombre normalizado exacto."""

from __future__ import annotations

from separador_nominas.name_normalization import to_safe_filename_stem
from separador_nominas.recognition_models import (
    EmployeePageGroup,
    PageRecognitionResult,
)


def build_employee_groups(
    page_results: tuple[PageRecognitionResult, ...] | list[PageRecognitionResult],
) -> tuple[tuple[EmployeePageGroup, ...], tuple[int, ...]]:
    """
    Agrupa páginas con ``confidence=high`` por ``normalized_key`` exacta.

    El orden de páginas dentro de cada grupo es ascendente por número original.
    El ``display_name`` y el stem de archivo se toman del primer resultado del grupo.
    """
    groups_map: dict[str, EmployeePageGroup] = {}
    order: list[str] = []
    unrecognized: list[int] = []

    for result in page_results:
        if (
            result.confidence != "high"
            or not result.normalized_key
            or not result.display_name
        ):
            unrecognized.append(result.page_number)
            continue

        key = result.normalized_key
        existing = groups_map.get(key)
        if existing is None:
            stem = to_safe_filename_stem(result.display_name)
            groups_map[key] = EmployeePageGroup(
                display_name=result.display_name,
                normalized_key=key,
                safe_filename_stem=stem,
                page_numbers=(result.page_number,),
            )
            order.append(key)
        else:
            pages = existing.page_numbers + (result.page_number,)
            groups_map[key] = EmployeePageGroup(
                display_name=existing.display_name,
                normalized_key=existing.normalized_key,
                safe_filename_stem=existing.safe_filename_stem,
                page_numbers=pages,
            )

    groups = tuple(groups_map[key] for key in order)
    return groups, tuple(unrecognized)
