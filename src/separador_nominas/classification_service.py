"""Gestión en memoria de grupos y asignaciones de trabajadores."""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from separador_nominas.classification_models import (
    ClassificationSession,
    ExportMode,
    PayrollGroup,
)
from separador_nominas.exceptions import (
    DuplicateGroupNameError,
    EmptyGroupNameError,
    InvalidGroupNameError,
    WorkerNotFoundError,
)
from separador_nominas.filename_service import sanitize_base_name


def _normalize_group_key(name: str) -> str:
    return " ".join(name.strip().casefold().split())


def create_group(
    session: ClassificationSession,
    display_name: str,
    *,
    export_mode: ExportMode = "combined",
) -> PayrollGroup:
    """Crea un grupo con nombre único (case-insensitive)."""
    raw = (display_name or "").strip()
    if not raw:
        raise EmptyGroupNameError(
            "El nombre del grupo no puede estar vacío."
        )
    safe = sanitize_base_name(raw)
    if not safe:
        raise InvalidGroupNameError(
            "El nombre del grupo no es válido para crear una carpeta en Windows.\n"
            "Prueba otro nombre sin caracteres especiales."
        )
    key = _normalize_group_key(raw)
    for group in session.groups.values():
        if _normalize_group_key(group.display_name) == key:
            raise DuplicateGroupNameError(
                "Ya existe un grupo con ese nombre.\n"
                "Elige un nombre distinto."
            )

    group = PayrollGroup(
        group_id=str(uuid.uuid4()),
        display_name=raw,
        safe_folder_name=safe,
        worker_ids=[],
        export_mode=export_mode,
    )
    session.groups[group.group_id] = group
    return group


def rename_group(
    session: ClassificationSession,
    group_id: str,
    new_name: str,
) -> PayrollGroup:
    """Renombra un grupo existente."""
    group = _require_group(session, group_id)
    raw = (new_name or "").strip()
    if not raw:
        raise EmptyGroupNameError("El nombre del grupo no puede estar vacío.")
    safe = sanitize_base_name(raw)
    if not safe:
        raise InvalidGroupNameError(
            "El nombre del grupo no es válido para crear una carpeta en Windows.\n"
            "Prueba otro nombre sin caracteres especiales."
        )
    key = _normalize_group_key(raw)
    for other in session.groups.values():
        if other.group_id == group_id:
            continue
        if _normalize_group_key(other.display_name) == key:
            raise DuplicateGroupNameError(
                "Ya existe un grupo con ese nombre.\n"
                "Elige un nombre distinto."
            )
    group.display_name = raw
    group.safe_folder_name = safe
    return group


def delete_group(session: ClassificationSession, group_id: str) -> None:
    """Elimina un grupo (los trabajadores quedan sin esa asignación)."""
    if group_id not in session.groups:
        raise InvalidGroupNameError("El grupo seleccionado no existe.")
    del session.groups[group_id]


def set_export_mode(
    session: ClassificationSession,
    group_id: str,
    export_mode: ExportMode,
) -> PayrollGroup:
    """Establece el modo de exportación de un grupo."""
    group = _require_group(session, group_id)
    if export_mode not in ("separate", "combined"):
        raise InvalidGroupNameError("El modo de exportación no es válido.")
    group.export_mode = export_mode
    return group


def add_workers_to_group(
    session: ClassificationSession,
    group_id: str,
    worker_ids: Iterable[str],
) -> tuple[int, int]:
    """
    Añade trabajadores al grupo.

    Returns:
        ``(añadidos, ya_estaban)``
    """
    group = _require_group(session, group_id)
    added = 0
    skipped = 0
    existing = set(group.worker_ids)
    for worker_id in worker_ids:
        if worker_id not in session.workers:
            raise WorkerNotFoundError(
                "Uno de los trabajadores seleccionados ya no está en la sesión."
            )
        if worker_id in existing:
            skipped += 1
            continue
        group.worker_ids.append(worker_id)
        existing.add(worker_id)
        added += 1
    return added, skipped


def remove_workers_from_group(
    session: ClassificationSession,
    group_id: str,
    worker_ids: Iterable[str],
) -> int:
    """Quita trabajadores del grupo. Devuelve cuántos se eliminaron."""
    group = _require_group(session, group_id)
    to_remove = set(worker_ids)
    before = len(group.worker_ids)
    group.worker_ids = [wid for wid in group.worker_ids if wid not in to_remove]
    return before - len(group.worker_ids)


def move_workers(
    session: ClassificationSession,
    worker_ids: Iterable[str],
    *,
    from_group_id: str,
    to_group_id: str,
) -> tuple[int, int]:
    """Quita de un grupo y añade a otro (permite multi-asignación previa)."""
    removed = remove_workers_from_group(session, from_group_id, worker_ids)
    added, skipped = add_workers_to_group(session, to_group_id, worker_ids)
    return removed, added + skipped


def unassigned_worker_ids(session: ClassificationSession) -> list[str]:
    """Trabajadores que no pertenecen a ningún grupo."""
    assigned: set[str] = set()
    for group in session.groups.values():
        assigned.update(group.worker_ids)
    return [wid for wid in session.workers if wid not in assigned]


def worker_group_ids(session: ClassificationSession, worker_id: str) -> list[str]:
    """Grupos a los que pertenece un trabajador (multi-asignación)."""
    return [
        group.group_id
        for group in session.groups.values()
        if worker_id in group.worker_ids
    ]


def workers_in_multiple_groups(session: ClassificationSession) -> list[str]:
    """IDs de trabajadores asignados a más de un grupo."""
    return [
        wid
        for wid in session.workers
        if len(worker_group_ids(session, wid)) > 1
    ]


def set_manual_label(
    session: ClassificationSession,
    worker_id: str,
    label: str | None,
) -> None:
    """Asigna una etiqueta descriptiva temporal (solo sesión)."""
    worker = session.workers.get(worker_id)
    if worker is None:
        raise WorkerNotFoundError(
            "El trabajador seleccionado ya no está en la sesión."
        )
    cleaned = (label or "").strip() or None
    worker.manual_label = cleaned


def page_count_for_group(session: ClassificationSession, group_id: str) -> int:
    """Suma de páginas de los trabajadores del grupo."""
    group = _require_group(session, group_id)
    total = 0
    for wid in group.worker_ids:
        worker = session.workers.get(wid)
        if worker is not None:
            total += len(worker.page_numbers)
    return total


def _require_group(session: ClassificationSession, group_id: str) -> PayrollGroup:
    group = session.groups.get(group_id)
    if group is None:
        raise InvalidGroupNameError("El grupo seleccionado no existe.")
    return group
