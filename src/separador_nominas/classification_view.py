"""Vista Tkinter del modo clasificación (solo UI; sin lógica PDF)."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, simpledialog, ttk

from separador_nominas.classification_models import ClassificationSession
from separador_nominas.classification_service import (
    add_workers_to_group,
    create_group,
    delete_group,
    remove_workers_from_group,
    rename_group,
    set_export_mode,
    set_manual_label,
    unassigned_worker_ids,
    worker_group_ids,
)
from separador_nominas.constants import (
    APP_NAME,
    EXPORT_MODE_COMBINED,
    EXPORT_MODE_SEPARATE,
)
from separador_nominas.exceptions import SeparadorNominasError
from separador_nominas.group_export_service import format_classification_export_summary


class ClassificationView(ttk.Frame):
    """Panel de dos zonas: grupos (izq.) y trabajadores (der.)."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._session: ClassificationSession | None = None
        self._on_changed = on_changed
        self._selected_worker_ids: set[str] = set()
        self._active_group_id: str | None = None
        self._filter_var = tk.StringVar(value="")
        self._status_filter = tk.StringVar(value="all")
        self._assign_filter = tk.StringVar(value="all")
        self._export_mode_var = tk.StringVar(value=EXPORT_MODE_COMBINED)
        self._step_labels_enabled = False
        self._build()

    def set_step_labels(self, enabled: bool) -> None:
        """Activa o desactiva la numeración de pasos 4 y 5."""
        self._step_labels_enabled = enabled
        if enabled:
            self._create_group_button.configure(text="4. Crear")
            self._add_to_group_button.configure(text="5. Añadir al grupo")
            self._remove_from_group_button.configure(text="Quitar del grupo")
        else:
            self._create_group_button.configure(text="Crear")
            self._add_to_group_button.configure(text="Añadir al grupo")
            self._remove_from_group_button.configure(text="Quitar del grupo")

    def _build(self) -> None:
        self.columnconfigure(0, weight=1, minsize=220)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)

        # Resaltado azul claro al seleccionar filas (tema ttk).
        style = ttk.Style(self)
        style.map(
            "Treeview",
            background=[("selected", "#0078D7")],
            foreground=[("selected", "#ffffff")],
        )

        left = ttk.LabelFrame(self, text="Grupos", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        btn_row = ttk.Frame(left)
        btn_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._create_group_button = ttk.Button(
            btn_row, text="Crear", command=self._on_create_group, width=10
        )
        self._create_group_button.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            btn_row, text="Renombrar", command=self._on_rename_group, width=10
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            btn_row, text="Eliminar", command=self._on_delete_group, width=8
        ).pack(side=tk.LEFT)

        self._groups_list = tk.Listbox(left, exportselection=False, height=12)
        self._groups_list.grid(row=1, column=0, sticky="nsew")
        self._groups_list.bind("<<ListboxSelect>>", self._on_group_select)

        export_frame = ttk.LabelFrame(
            left, text="Formato de salida del grupo", padding=6
        )
        export_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Radiobutton(
            export_frame,
            text="Un archivo por trabajador",
            variable=self._export_mode_var,
            value=EXPORT_MODE_SEPARATE,
            command=self._on_export_mode_changed,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            export_frame,
            text="Un único archivo con todo el grupo",
            variable=self._export_mode_var,
            value=EXPORT_MODE_COMBINED,
            command=self._on_export_mode_changed,
        ).grid(row=1, column=0, sticky="w")

        assign_row = ttk.Frame(left)
        assign_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self._add_to_group_button = ttk.Button(
            assign_row, text="Añadir al grupo", command=self._on_add_to_group
        )
        self._add_to_group_button.pack(side=tk.LEFT, padx=(0, 4))
        self._remove_from_group_button = ttk.Button(
            assign_row, text="Quitar del grupo", command=self._on_remove_from_group
        )
        self._remove_from_group_button.pack(side=tk.LEFT)

        right = ttk.LabelFrame(self, text="Trabajadores detectados", padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        filter_row = ttk.Frame(right)
        filter_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        filter_row.columnconfigure(1, weight=1)
        ttk.Label(filter_row, text="Buscar").grid(row=0, column=0, padx=(0, 4))
        search = ttk.Entry(filter_row, textvariable=self._filter_var)
        search.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self._filter_var.trace_add("write", lambda *_: self.refresh_workers())

        ttk.Label(filter_row, text="Estado").grid(row=0, column=2, padx=(0, 4))
        status_box = ttk.Combobox(
            filter_row,
            textvariable=self._status_filter,
            values=("all", "recognized", "partial", "unrecognized"),
            width=12,
            state="readonly",
        )
        status_box.grid(row=0, column=3, padx=(0, 8))
        status_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_workers())

        ttk.Label(filter_row, text="Asignación").grid(row=0, column=4, padx=(0, 4))
        assign_box = ttk.Combobox(
            filter_row,
            textvariable=self._assign_filter,
            values=("all", "assigned", "unassigned"),
            width=12,
            state="readonly",
        )
        assign_box.grid(row=0, column=5)
        assign_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_workers())

        sel_row = ttk.Frame(right)
        sel_row.grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Button(
            sel_row, text="Seleccionar todos", command=self._select_all_visible
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            sel_row, text="Deseleccionar todos", command=self._clear_selection
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            sel_row, text="Etiqueta manual", command=self._on_manual_label
        ).pack(side=tk.LEFT)
        self._selection_count = tk.StringVar(value="Seleccionados: 0")
        ttk.Label(sel_row, textvariable=self._selection_count).pack(
            side=tk.LEFT, padx=(12, 0)
        )

        columns = ("doc", "name", "pages", "status", "groups")
        self._tree = ttk.Treeview(
            right,
            columns=columns,
            show="headings",
            selectmode="extended",
            height=14,
        )
        self._tree.heading("doc", text="DNI/NIE")
        self._tree.heading("name", text="Nombre")
        self._tree.heading("pages", text="Páginas")
        self._tree.heading("status", text="Estado")
        self._tree.heading("groups", text="Grupos")
        self._tree.column("doc", width=110)
        self._tree.column("name", width=220)
        self._tree.column("pages", width=70, anchor="center")
        self._tree.column("status", width=100)
        self._tree.column("groups", width=140)
        self._tree.grid(row=2, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        # Ctrl+A selecciona todos los visibles.
        self._tree.bind("<Control-a>", self._on_ctrl_a)
        self._tree.bind("<Control-A>", self._on_ctrl_a)
        scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self._tree.yview)
        scroll.grid(row=2, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scroll.set)

        self._hint = ttk.Label(
            right,
            text=(
                "Clic, Ctrl+clic o Mayús+clic para seleccionar (fondo azul). "
                "«Seleccionar todos» marca todas las filas visibles. "
                "Un trabajador puede pertenecer a varios grupos."
            ),
            foreground="#555555",
        )
        self._hint.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def set_session(self, session: ClassificationSession | None) -> None:
        """Asocia una sesión y refresca la vista."""
        self._session = session
        self._selected_worker_ids.clear()
        self._active_group_id = None
        self.refresh_all()

    @property
    def session(self) -> ClassificationSession | None:
        return self._session

    def refresh_all(self) -> None:
        self.refresh_groups()
        self.refresh_workers()
        if self._on_changed:
            self._on_changed()

    def refresh_groups(self) -> None:
        self._groups_list.delete(0, tk.END)
        self._group_ids: list[str] = []
        if self._session is None:
            return
        for group in self._session.groups.values():
            n = len(group.worker_ids)
            pages = sum(
                len(self._session.workers[wid].page_numbers)
                for wid in group.worker_ids
                if wid in self._session.workers
            )
            label = f"{group.display_name}  ({n} trab., {pages} pág.)"
            self._groups_list.insert(tk.END, label)
            self._group_ids.append(group.group_id)

        unassigned = (
            len(unassigned_worker_ids(self._session)) if self._session else 0
        )
        self._groups_list.insert(tk.END, f"Sin asignar  ({unassigned} trab.)")
        self._group_ids.append("")  # marcador visual

        if self._active_group_id and self._active_group_id in self._group_ids:
            index = self._group_ids.index(self._active_group_id)
            self._groups_list.selection_set(index)
            group = self._session.groups.get(self._active_group_id)
            if group is not None:
                self._export_mode_var.set(group.export_mode)

    def refresh_workers(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        if self._session is None:
            return

        query = self._filter_var.get().strip().casefold()
        status_f = self._status_filter.get()
        assign_f = self._assign_filter.get()
        unassigned = set(unassigned_worker_ids(self._session))

        rows = list(self._session.workers.values())
        rows.sort(
            key=lambda w: (
                w.document_id or "",
                w.ui_name.casefold(),
                w.worker_id,
            )
        )

        for worker in rows:
            if status_f != "all" and worker.recognition_status != status_f:
                continue
            is_unassigned = worker.worker_id in unassigned
            if assign_f == "assigned" and is_unassigned:
                continue
            if assign_f == "unassigned" and not is_unassigned:
                continue

            doc = worker.document_id or "----------"
            name = worker.ui_name
            if query and query not in doc.casefold() and query not in name.casefold():
                continue

            gids = worker_group_ids(self._session, worker.worker_id)
            group_names = [
                self._session.groups[gid].display_name
                for gid in gids
                if gid in self._session.groups
            ]
            status_label = {
                "recognized": "Reconocido",
                "partial": "Parcial",
                "unrecognized": "Revisar",
            }.get(worker.recognition_status, worker.recognition_status)
            if len(group_names) > 1:
                status_label += " *"

            self._tree.insert(
                "",
                tk.END,
                iid=worker.worker_id,
                values=(
                    doc,
                    name,
                    str(len(worker.page_numbers)),
                    status_label,
                    ", ".join(group_names),
                ),
            )

        self._apply_visual_selection()

    def build_export_summary(self) -> str:
        if self._session is None:
            return ""
        return format_classification_export_summary(self._session)

    def _notify(self) -> None:
        if self._on_changed:
            self._on_changed()

    def _on_group_select(self, _event: object = None) -> None:
        selection = self._groups_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        group_id = self._group_ids[index]
        if not group_id:
            self._active_group_id = None
            return
        self._active_group_id = group_id
        if self._session and group_id in self._session.groups:
            self._export_mode_var.set(self._session.groups[group_id].export_mode)

    def _on_create_group(self) -> None:
        if self._session is None:
            return
        name = simpledialog.askstring("Nuevo grupo", "Nombre del grupo:", parent=self)
        if name is None:
            return
        try:
            group = create_group(self._session, name)
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return
        self._active_group_id = group.group_id
        self.refresh_all()

    def _on_rename_group(self) -> None:
        if self._session is None or not self._active_group_id:
            messagebox.showinfo(APP_NAME, "Selecciona un grupo primero.", parent=self)
            return
        current = self._session.groups[self._active_group_id].display_name
        name = simpledialog.askstring(
            "Renombrar grupo",
            "Nuevo nombre:",
            initialvalue=current,
            parent=self,
        )
        if name is None:
            return
        try:
            rename_group(self._session, self._active_group_id, name)
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return
        self.refresh_all()

    def _on_delete_group(self) -> None:
        if self._session is None or not self._active_group_id:
            messagebox.showinfo(APP_NAME, "Selecciona un grupo primero.", parent=self)
            return
        if not messagebox.askyesno(
            APP_NAME,
            "¿Eliminar el grupo seleccionado? Los trabajadores no se borran.",
            parent=self,
        ):
            return
        try:
            delete_group(self._session, self._active_group_id)
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return
        self._active_group_id = None
        self.refresh_all()

    def _on_export_mode_changed(self) -> None:
        if self._session is None or not self._active_group_id:
            return
        try:
            set_export_mode(
                self._session,
                self._active_group_id,
                self._export_mode_var.get(),  # type: ignore[arg-type]
            )
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
        self.refresh_groups()
        self._notify()

    def _selected_ids_for_action(self) -> list[str]:
        """IDs con selección visual (fondo azul) en la tabla."""
        return list(self._tree.selection())

    def _on_add_to_group(self) -> None:
        if self._session is None or not self._active_group_id:
            messagebox.showinfo(APP_NAME, "Selecciona un grupo primero.", parent=self)
            return
        selected = self._selected_ids_for_action()
        if not selected:
            messagebox.showinfo(
                APP_NAME,
                "Selecciona al menos un trabajador en la lista "
                "(aparecerán con fondo azul).",
                parent=self,
            )
            return
        group = self._session.groups.get(self._active_group_id)
        if group is None:
            messagebox.showerror(APP_NAME, "El grupo seleccionado no existe.", parent=self)
            return
        group_name = group.display_name
        already_in_group = set(group.worker_ids)
        try:
            added, skipped = add_workers_to_group(
                self._session,
                self._active_group_id,
                selected,
            )
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return

        newly_ids = [wid for wid in selected if wid not in already_in_group]
        new_labels = [
            self._session.workers[wid].ui_name
            for wid in newly_ids
            if wid in self._session.workers
        ]

        if added == 0:
            msg = (
                f"Nadie nuevo se ha añadido al grupo «{group_name}».\n"
                f"Ya estaban en ese grupo: {skipped}."
            )
        elif added == 1:
            label = new_labels[0] if new_labels else "1 trabajador"
            msg = f"Añadido «{label}» al grupo «{group_name}»."
            if skipped:
                msg += f"\nYa estaban en el grupo: {skipped}."
        else:
            preview = ", ".join(new_labels[:5])
            if len(new_labels) > 5:
                preview += f"… (+{len(new_labels) - 5} más)"
            msg = (
                f"Añadidos {added} trabajadores al grupo «{group_name}».\n"
                f"{preview}"
            )
            if skipped:
                msg += f"\nYa estaban en el grupo: {skipped}."

        messagebox.showinfo(APP_NAME, msg, parent=self)
        self.refresh_all()

    def _on_remove_from_group(self) -> None:
        if self._session is None or not self._active_group_id:
            messagebox.showinfo(APP_NAME, "Selecciona un grupo primero.", parent=self)
            return
        selected = self._selected_ids_for_action()
        if not selected:
            messagebox.showinfo(
                APP_NAME,
                "Selecciona al menos un trabajador en la lista "
                "(aparecerán con fondo azul).",
                parent=self,
            )
            return
        try:
            remove_workers_from_group(
                self._session,
                self._active_group_id,
                selected,
            )
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return
        self.refresh_all()

    def _on_tree_select(self, _event: object = None) -> None:
        """Sincroniza el set interno con la selección visual del Treeview."""
        visible = set(self._tree.get_children())
        current = set(self._tree.selection())
        for iid in visible - current:
            self._selected_worker_ids.discard(iid)
        self._selected_worker_ids.update(current)
        self._update_selection_count()

    def _apply_visual_selection(self) -> None:
        """Restaura el fondo azul tras reconstruir filas (p. ej. al filtrar)."""
        visible_selected = [
            iid
            for iid in self._tree.get_children()
            if iid in self._selected_worker_ids
        ]
        # Evita bucles: desactiva temporalmente el handler si hace falta.
        if visible_selected:
            self._tree.selection_set(visible_selected)
        else:
            self._tree.selection_remove(*self._tree.get_children())
        self._update_selection_count()

    def _update_selection_count(self) -> None:
        count = len(self._tree.selection())
        self._selection_count.set(f"Seleccionados: {count}")

    def _select_all_visible(self) -> None:
        children = self._tree.get_children()
        if not children:
            return
        self._selected_worker_ids.update(children)
        self._tree.selection_set(children)
        self._update_selection_count()
        # Asegura foco para que el resaltado se vea de inmediato.
        self._tree.focus_set()
        if children:
            self._tree.focus(children[0])
            self._tree.see(children[0])

    def _clear_selection(self) -> None:
        self._selected_worker_ids.clear()
        children = self._tree.get_children()
        if children:
            self._tree.selection_remove(*children)
        self._update_selection_count()

    def _on_ctrl_a(self, _event: object = None) -> str:
        self._select_all_visible()
        return "break"

    def _on_manual_label(self) -> None:
        selected = self._selected_ids_for_action()
        if self._session is None or len(selected) != 1:
            messagebox.showinfo(
                APP_NAME,
                "Selecciona un único trabajador (fondo azul) "
                "para editar su etiqueta.",
                parent=self,
            )
            return
        worker_id = selected[0]
        worker = self._session.workers[worker_id]
        label = simpledialog.askstring(
            "Etiqueta temporal",
            "Nombre descriptivo (solo en esta sesión):",
            initialvalue=worker.manual_label or worker.display_name or "",
            parent=self,
        )
        if label is None:
            return
        try:
            set_manual_label(self._session, worker_id, label)
        except SeparadorNominasError as exc:
            messagebox.showerror(APP_NAME, exc.user_message, parent=self)
            return
        self.refresh_workers()
        self._notify()
