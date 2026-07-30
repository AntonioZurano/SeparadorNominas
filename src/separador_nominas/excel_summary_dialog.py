"""Diálogo modal de resumen tras el cruce Excel ↔ PDF."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from separador_nominas.classification_models import (
    ClassificationSession,
    WorkerRecord,
)
from separador_nominas.classification_service import unassigned_worker_ids
from separador_nominas.constants import APP_NAME
from separador_nominas.department_assignment_service import AssignmentApplyResult
from separador_nominas.spreadsheet_models import SpreadsheetImportResult
from separador_nominas.ui_geometry import maximize_toplevel

_UNCLASSIFIED_KEY = "__unclassified__"
_CONFLICTS_KEY = "__conflicts__"


class ExcelMatchSummaryDialog(tk.Toplevel):
    """
    Ventana modal con resumen de departamentos y trabajadores detectados.

    Similar al panel de clasificación por grupos: lista de departamentos a la
    izquierda y detalle (documento, nombre, páginas) a la derecha.
    """

    def __init__(
        self,
        master: tk.Misc,
        session: ClassificationSession,
        apply_result: AssignmentApplyResult,
        import_result: SpreadsheetImportResult,
    ) -> None:
        super().__init__(master)
        self.title(f"{APP_NAME} — Resumen Excel")
        self.transient(master.winfo_toplevel())
        self.resizable(True, True)
        self.minsize(720, 480)

        self._session = session
        self._apply = apply_result
        self._import = import_result
        # Lista de (key, label) para el Listbox
        self._dept_entries: list[tuple[str, str]] = []

        self._build()
        self._populate_departments()
        self._select_first_department()

        self.protocol("WM_DELETE_WINDOW", self._on_continue)
        maximize_toplevel(self)
        self.grab_set()
        self.focus_set()

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        summary = self._apply.summary
        header = (
            f"PDF: {self._session.page_count} páginas, "
            f"{len(self._session.workers)} trabajadores.  "
            f"Excel: {self._import.row_count_read} filas, "
            f"{len(self._import.departments)} departamentos.  "
            f"Asignados: {summary.matched_workers}.  "
            f"Sin clasificar: {summary.pages_unclassified} páginas.  "
            f"Conflictos: {summary.conflicts_pending}."
        )
        ttk.Label(outer, text=header, wraplength=1100).grid(
            row=0, column=0, sticky="ew", pady=(0, 10)
        )

        paned = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew")

        left = ttk.LabelFrame(paned, text="Departamentos", padding=8)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self._dept_list = tk.Listbox(left, exportselection=False, height=16)
        self._dept_list.grid(row=0, column=0, sticky="nsew")
        dept_scroll = ttk.Scrollbar(
            left, orient=tk.VERTICAL, command=self._dept_list.yview
        )
        dept_scroll.grid(row=0, column=1, sticky="ns")
        self._dept_list.configure(yscrollcommand=dept_scroll.set)
        self._dept_list.bind("<<ListboxSelect>>", self._on_dept_select)
        paned.add(left, weight=1)

        right = ttk.LabelFrame(paned, text="Trabajadores", padding=8)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        columns = ("document", "name", "pages")
        self._workers = ttk.Treeview(
            right,
            columns=columns,
            show="headings",
            selectmode="none",
            height=16,
        )
        self._workers.heading("document", text="DNI/NIE")
        self._workers.heading("name", text="Nombre")
        self._workers.heading("pages", text="Páginas")
        self._workers.column("document", width=120, minwidth=80)
        self._workers.column("name", width=260, minwidth=120)
        self._workers.column("pages", width=80, minwidth=60, anchor=tk.CENTER)
        self._workers.grid(row=0, column=0, sticky="nsew")
        workers_scroll = ttk.Scrollbar(
            right, orient=tk.VERTICAL, command=self._workers.yview
        )
        workers_scroll.grid(row=0, column=1, sticky="ns")
        self._workers.configure(yscrollcommand=workers_scroll.set)
        paned.add(right, weight=3)

        notes = ttk.LabelFrame(outer, text="Avisos", padding=8)
        notes.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        notes.columnconfigure(0, weight=1)
        self._notes = tk.Text(
            notes,
            wrap=tk.WORD,
            height=5,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        notes_scroll = ttk.Scrollbar(
            notes, orient=tk.VERTICAL, command=self._notes.yview
        )
        self._notes.configure(yscrollcommand=notes_scroll.set)
        self._notes.grid(row=0, column=0, sticky="ew")
        notes_scroll.grid(row=0, column=1, sticky="ns")
        self._notes.insert("1.0", self._build_notes_text())
        self._notes.configure(state=tk.DISABLED)

        buttons = ttk.Frame(outer)
        buttons.grid(row=3, column=0, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Continuar", command=self._on_continue).pack(
            side=tk.RIGHT
        )

    def _build_notes_text(self) -> str:
        lines: list[str] = []
        if self._apply.unmatched_spreadsheet:
            lines.append(
                "Registros Excel sin coincidencia en el PDF "
                f"({len(self._apply.unmatched_spreadsheet)}):"
            )
            for item in self._apply.unmatched_spreadsheet[:30]:
                lines.append(
                    f"- Fila {item.source_row}: sin coincidencia "
                    f"({item.department_name})"
                )
            if len(self._apply.unmatched_spreadsheet) > 30:
                rest = len(self._apply.unmatched_spreadsheet) - 30
                lines.append(f"- … y {rest} más")
            lines.append("")
        if self._apply.unresolved_conflicts:
            lines.append("Conflictos (mismo documento, departamentos distintos):")
            for conflict in self._apply.unresolved_conflicts:
                rows = ", ".join(map(str, conflict.source_rows))
                depts = " / ".join(conflict.department_names)
                lines.append(f"- Filas {rows}: {depts}")
            lines.append("")
        if self._import.warnings:
            lines.append(f"Advertencias de filas Excel: {len(self._import.warnings)}")
        if self._import.errors:
            lines.append(f"Errores de filas Excel: {len(self._import.errors)}")
        if not lines:
            return (
                "No hay avisos adicionales. Revisa departamentos y trabajadores "
                "arriba y pulsa Continuar para generar o cancelar."
            )
        return "\n".join(lines).rstrip()

    def _populate_departments(self) -> None:
        self._dept_entries.clear()
        self._dept_list.delete(0, tk.END)
        for group in self._session.groups.values():
            pages = sum(
                len(self._session.workers[wid].page_numbers)
                for wid in group.worker_ids
                if wid in self._session.workers
            )
            label = (
                f"{group.display_name}  "
                f"({len(group.worker_ids)} trab. / {pages} pág.)"
            )
            self._dept_entries.append((group.group_id, label))
            self._dept_list.insert(tk.END, label)

        unassigned = unassigned_worker_ids(self._session)
        if unassigned:
            pages = sum(
                len(self._session.workers[wid].page_numbers)
                for wid in unassigned
                if wid in self._session.workers
            )
            label = f"Sin clasificar  ({len(unassigned)} trab. / {pages} pág.)"
            self._dept_entries.append((_UNCLASSIFIED_KEY, label))
            self._dept_list.insert(tk.END, label)

        if self._apply.unresolved_conflicts:
            label = (
                f"Conflictos  ({len(self._apply.unresolved_conflicts)} documentos)"
            )
            self._dept_entries.append((_CONFLICTS_KEY, label))
            self._dept_list.insert(tk.END, label)

    def _select_first_department(self) -> None:
        if not self._dept_entries:
            self._fill_workers([])
            return
        self._dept_list.selection_set(0)
        self._dept_list.activate(0)
        self._on_dept_select()

    def _on_dept_select(self, *_args: object) -> None:
        selection = self._dept_list.curselection()
        if not selection:
            return
        key = self._dept_entries[selection[0]][0]
        if key == _UNCLASSIFIED_KEY:
            workers = [
                self._session.workers[wid]
                for wid in unassigned_worker_ids(self._session)
                if wid in self._session.workers
            ]
            self._fill_workers(workers)
            return
        if key == _CONFLICTS_KEY:
            self._fill_conflict_rows()
            return
        group = self._session.groups.get(key)
        if group is None:
            self._fill_workers([])
            return
        workers = [
            self._session.workers[wid]
            for wid in group.worker_ids
            if wid in self._session.workers
        ]
        self._fill_workers(workers)

    def _fill_workers(self, workers: list[WorkerRecord]) -> None:
        self._workers.delete(*self._workers.get_children())
        ordered = sorted(
            workers,
            key=lambda w: (
                (w.document_id or "").upper(),
                w.ui_name.upper(),
            ),
        )
        for worker in ordered:
            pages = ", ".join(str(p) for p in sorted(worker.page_numbers))
            self._workers.insert(
                "",
                tk.END,
                values=(
                    worker.document_id or "—",
                    worker.ui_name,
                    pages or "—",
                ),
            )

    def _fill_conflict_rows(self) -> None:
        self._workers.delete(*self._workers.get_children())
        for conflict in self._apply.unresolved_conflicts:
            depts = " / ".join(conflict.department_names)
            rows = ", ".join(map(str, conflict.source_rows))
            self._workers.insert(
                "",
                tk.END,
                values=(
                    conflict.document_id,
                    f"Conflicto (filas {rows})",
                    depts,
                ),
            )

    def _on_continue(self) -> None:
        self.grab_release()
        self.destroy()


def show_excel_match_summary_dialog(
    master: tk.Misc,
    session: ClassificationSession,
    apply_result: AssignmentApplyResult,
    import_result: SpreadsheetImportResult,
) -> None:
    """Abre el modal y espera a que el usuario pulse Continuar."""
    dialog = ExcelMatchSummaryDialog(master, session, apply_result, import_result)
    master.wait_window(dialog)
