"""Cruce Excel ↔ trabajadores PDF y creación automática de grupos."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from separador_nominas.classification_models import ClassificationSession
from separador_nominas.classification_service import (
    add_workers_to_group,
    create_group,
    remove_workers_from_group,
    unassigned_worker_ids,
)
from separador_nominas.constants import LOGGER_NAME
from separador_nominas.department_normalization import to_department_key
from separador_nominas.spreadsheet_models import (
    AssignmentConflict,
    DepartmentAssignment,
    MatchSummary,
    SpreadsheetClassificationState,
    SpreadsheetImportResult,
)

logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class AssignmentApplyResult:
    """Resultado de aplicar el Excel sobre una sesión de clasificación."""

    summary: MatchSummary
    unmatched_spreadsheet: tuple[DepartmentAssignment, ...]
    unresolved_conflicts: tuple[AssignmentConflict, ...]
    groups_created: int
    workers_assigned: int


def apply_spreadsheet_to_session(
    session: ClassificationSession,
    import_result: SpreadsheetImportResult,
    *,
    conflict_resolutions: dict[str, str] | None = None,
    clear_existing_groups: bool = True,
) -> AssignmentApplyResult:
    """
    Crea grupos por departamento y asigna trabajadores (política exclusiva).

    ``conflict_resolutions`` mapea ``document_id`` → ``department_key`` elegido.
    """
    resolutions = conflict_resolutions or {}

    if clear_existing_groups:
        session.groups.clear()

    # document_id → assignment (solo no conflictivos)
    assignment_by_doc = {
        item.document_id: item for item in import_result.assignments
    }

    # Conflictos resueltos manualmente
    conflict_by_doc = {c.document_id: c for c in import_result.conflicts}
    for doc_id, dept_key in resolutions.items():
        conflict = conflict_by_doc.get(doc_id)
        if conflict is None:
            continue
        if dept_key not in conflict.department_keys:
            continue
        display = dept_key
        for key, name in conflict.department_options:
            if key == dept_key:
                display = name
                break
        else:
            for name in conflict.department_names:
                if to_department_key(name) == dept_key:
                    display = name
                    break
        assignment_by_doc[doc_id] = DepartmentAssignment(
            document_id=doc_id,
            department_name=display,
            department_key=dept_key,
            source_row=conflict.source_rows[0],
        )

    unresolved = tuple(
        c
        for c in import_result.conflicts
        if c.document_id not in assignment_by_doc
    )

    # Workers del PDF indexados por document_id
    workers_by_doc: dict[str, str] = {}
    for worker_id, worker in session.workers.items():
        if worker.document_id:
            workers_by_doc[worker.document_id] = worker_id

    matched_docs = set(assignment_by_doc) & set(workers_by_doc)
    unmatched_spreadsheet = tuple(
        assignment_by_doc[doc]
        for doc in assignment_by_doc
        if doc not in workers_by_doc
    )

    # Crear grupos solo para departamentos con al menos un worker del PDF
    dept_to_worker_ids: dict[str, list[str]] = {}
    dept_display: dict[str, str] = {}
    for doc_id in matched_docs:
        assignment = assignment_by_doc[doc_id]
        dept_to_worker_ids.setdefault(assignment.department_key, []).append(
            workers_by_doc[doc_id]
        )
        dept_display.setdefault(
            assignment.department_key, assignment.department_name
        )

    groups_created = 0
    workers_assigned = 0
    for dept_key, worker_ids in dept_to_worker_ids.items():
        group = create_group(
            session,
            dept_display[dept_key],
            export_mode="combined",
        )
        # Asegurar carpeta coherente si create_group usó otro safe name
        added, _skipped = add_workers_to_group(session, group.group_id, worker_ids)
        groups_created += 1
        workers_assigned += added

    unmatched_pdf = 0
    pages_unclassified = 0
    for worker in session.workers.values():
        if worker.worker_id in {
            wid for ids in dept_to_worker_ids.values() for wid in ids
        }:
            continue
        # Sin departamento o conflicto no resuelto
        if worker.document_id and worker.document_id in {
            c.document_id for c in unresolved
        }:
            pages_unclassified += len(worker.page_numbers)
            unmatched_pdf += 1
            continue
        if worker.document_id and worker.document_id not in assignment_by_doc:
            pages_unclassified += len(worker.page_numbers)
            unmatched_pdf += 1
            continue
        if not worker.document_id:
            pages_unclassified += len(worker.page_numbers)

    summary = MatchSummary(
        matched_workers=workers_assigned,
        unmatched_pdf_workers=unmatched_pdf,
        unmatched_spreadsheet_rows=len(unmatched_spreadsheet),
        conflicts_pending=len(unresolved),
        pages_unclassified=pages_unclassified,
        departments_with_workers=groups_created,
    )

    logger.info(
        "Cruce Excel-PDF completado. "
        "%s trabajadores asignados. "
        "%s sin departamento. "
        "%s registros Excel sin coincidencia. "
        "%s conflictos pendientes.",
        summary.matched_workers,
        summary.unmatched_pdf_workers,
        summary.unmatched_spreadsheet_rows,
        summary.conflicts_pending,
    )

    return AssignmentApplyResult(
        summary=summary,
        unmatched_spreadsheet=unmatched_spreadsheet,
        unresolved_conflicts=unresolved,
        groups_created=groups_created,
        workers_assigned=workers_assigned,
    )


def resolve_conflict_and_reapply(
    session: ClassificationSession,
    state: SpreadsheetClassificationState,
    document_id: str,
    department_key: str,
) -> AssignmentApplyResult:
    """Guarda la elección de conflicto y reaplica asignaciones."""
    if state.import_result is None:
        raise ValueError("No hay resultado de importación en la sesión.")
    state.resolved_conflict_choices[document_id] = department_key
    state.unresolved_conflict_docs.discard(document_id)
    return apply_spreadsheet_to_session(
        session,
        state.import_result,
        conflict_resolutions=state.resolved_conflict_choices,
        clear_existing_groups=True,
    )


def reassign_worker_exclusive(
    session: ClassificationSession,
    worker_id: str,
    target_group_id: str,
) -> None:
    """Mueve un trabajador a un único grupo (quita de los demás)."""
    for group in session.groups.values():
        if worker_id in group.worker_ids and group.group_id != target_group_id:
            remove_workers_from_group(session, group.group_id, [worker_id])
    add_workers_to_group(session, target_group_id, [worker_id])


def format_excel_match_summary(
    session: ClassificationSession,
    apply_result: AssignmentApplyResult,
    import_result: SpreadsheetImportResult,
) -> str:
    """Resumen de vista previa (sin volcar DNI en logs; sí en UI)."""
    lines = [
        "Resumen de importación",
        "",
        "PDF:",
        f"- {session.page_count} páginas",
        f"- {len(session.workers)} trabajadores/fichas detectadas",
        "",
        "Excel:",
        f"- {import_result.row_count_read} filas analizadas",
        f"- {len(import_result.assignments)} asignaciones válidas",
        f"- {len(import_result.warnings)} filas con advertencias",
        f"- {len(import_result.errors)} filas con errores",
        f"- {len(import_result.departments)} departamentos detectados",
        "",
        "Coincidencias:",
        f"- {apply_result.summary.matched_workers} trabajadores asignados",
        (
            f"- {apply_result.summary.unmatched_pdf_workers} "
            "trabajadores sin departamento"
        ),
        (
            f"- {apply_result.summary.unmatched_spreadsheet_rows} "
            "registros Excel no encontrados en el PDF"
        ),
        f"- {apply_result.summary.conflicts_pending} conflictos pendientes",
        (
            f"- {apply_result.summary.pages_unclassified} "
            "páginas irán a No_clasificadas"
        ),
    ]
    if session.groups:
        lines.append("")
        lines.append("Por departamento:")
        for group in session.groups.values():
            pages = sum(
                len(session.workers[wid].page_numbers)
                for wid in group.worker_ids
                if wid in session.workers
            )
            lines.append(group.display_name)
            lines.append(f"- {len(group.worker_ids)} trabajadores")
            lines.append(f"- {pages} páginas")
            lines.append("")
    if apply_result.unmatched_spreadsheet:
        lines.append("Registros Excel no encontrados en el PDF:")
        for item in apply_result.unmatched_spreadsheet:
            lines.append(
                f"- Fila {item.source_row}: documento sin coincidencia "
                f"({item.department_name})"
            )
        lines.append("")
    if apply_result.unresolved_conflicts:
        lines.append("Conflictos (elige un departamento antes de generar):")
        for conflict in apply_result.unresolved_conflicts:
            lines.append(
                f"- Documento en filas {', '.join(map(str, conflict.source_rows))}: "
                + " / ".join(conflict.department_names)
            )
    return "\n".join(lines).rstrip()


def unclassified_worker_ids(
    session: ClassificationSession,
    *,
    unresolved_conflict_docs: set[str] | frozenset[str] | None = None,
) -> list[str]:
    """Trabajadores cuyas páginas deben ir a No_clasificadas."""
    unresolved = unresolved_conflict_docs or set()
    assigned = set(unassigned_worker_ids(session))
    result: list[str] = []
    for wid in assigned:
        worker = session.workers[wid]
        if worker.document_id and worker.document_id in unresolved:
            result.append(wid)
            continue
        result.append(wid)
    return result
