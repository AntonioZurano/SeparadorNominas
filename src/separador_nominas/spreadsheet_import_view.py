"""Vista Tkinter del modo clasificación automática mediante Excel."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from separador_nominas.constants import (
    EXPORT_MODE_COMBINED,
    EXPORT_MODE_SEPARATE,
)
from separador_nominas.spreadsheet_models import ColumnMapping
from separador_nominas.spreadsheet_service import (
    detect_column_mapping,
    iter_column_labels,
)


class SpreadsheetImportView(ttk.Frame):
    """Panel de configuración Excel + resumen de coincidencias."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._on_changed = on_changed
        self._sheet_names: tuple[str, ...] = ()
        self._headers: list[object] = []
        self._mapping: ColumnMapping | None = None
        self._export_mode_var = tk.StringVar(value=EXPORT_MODE_COMBINED)
        self._sheet_var = tk.StringVar(value="")
        self._doc_col_var = tk.StringVar(value="")
        self._dept_col_var = tk.StringVar(value="")
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        cfg = ttk.LabelFrame(self, text="Excel de departamentos", padding=8)
        cfg.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        cfg.columnconfigure(1, weight=1)

        ttk.Label(cfg, text="Hoja").grid(row=0, column=0, sticky="w")
        self._sheet_combo = ttk.Combobox(
            cfg, textvariable=self._sheet_var, state="readonly"
        )
        self._sheet_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._sheet_combo.bind("<<ComboboxSelected>>", self._notify)

        ttk.Label(cfg, text="Columna DNI/NIE").grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )
        self._doc_combo = ttk.Combobox(
            cfg, textvariable=self._doc_col_var, state="readonly"
        )
        self._doc_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))

        ttk.Label(cfg, text="Columna departamento").grid(
            row=2, column=0, sticky="w", pady=(6, 0)
        )
        self._dept_combo = ttk.Combobox(
            cfg, textvariable=self._dept_col_var, state="readonly"
        )
        self._dept_combo.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))

        export = ttk.LabelFrame(self, text="Formato de salida", padding=8)
        export.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Radiobutton(
            export,
            text="Un PDF conjunto por departamento (recomendado)",
            variable=self._export_mode_var,
            value=EXPORT_MODE_COMBINED,
            command=self._notify,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            export,
            text="Un PDF por trabajador dentro de cada departamento",
            variable=self._export_mode_var,
            value=EXPORT_MODE_SEPARATE,
            command=self._notify,
        ).grid(row=1, column=0, sticky="w")

        summary = ttk.LabelFrame(self, text="Vista previa", padding=8)
        summary.grid(row=2, column=0, sticky="nsew")
        summary.columnconfigure(0, weight=1)
        summary.rowconfigure(0, weight=1)

        self._summary_box = tk.Text(
            summary,
            wrap=tk.WORD,
            height=12,
            relief=tk.SOLID,
            borderwidth=1,
            padx=6,
            pady=4,
            font=("Segoe UI", 9),
        )
        scroll = ttk.Scrollbar(
            summary, orient=tk.VERTICAL, command=self._summary_box.yview
        )
        self._summary_box.configure(yscrollcommand=scroll.set)
        self._summary_box.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self._summary_box.configure(state=tk.DISABLED)

    def _notify(self, *_args: object) -> None:
        if self._on_changed is not None:
            self._on_changed()

    def clear(self) -> None:
        """Limpia selectores y resumen."""
        self._sheet_names = ()
        self._headers = []
        self._mapping = None
        self._sheet_var.set("")
        self._doc_col_var.set("")
        self._dept_col_var.set("")
        self._sheet_combo.configure(values=())
        self._doc_combo.configure(values=())
        self._dept_combo.configure(values=())
        self.set_summary_text("")

    def set_workbook_meta(
        self,
        sheet_names: tuple[str, ...],
        *,
        selected_sheet: str,
        headers: list[object],
        mapping: ColumnMapping | None = None,
    ) -> None:
        """Rellena hoja y columnas tras seleccionar un Excel."""
        self._sheet_names = sheet_names
        self._headers = list(headers)
        self._sheet_combo.configure(values=list(sheet_names))
        self._sheet_var.set(selected_sheet)
        detected = mapping or detect_column_mapping(headers)
        self._mapping = detected
        labels = list(iter_column_labels(headers, width=max(len(headers), 2)))
        self._doc_combo.configure(values=labels)
        self._dept_combo.configure(values=labels)
        if 0 <= detected.document_column_index < len(labels):
            self._doc_col_var.set(labels[detected.document_column_index])
        if 0 <= detected.department_column_index < len(labels):
            self._dept_col_var.set(labels[detected.department_column_index])

    def selected_sheet(self) -> str | None:
        value = self._sheet_var.get().strip()
        return value or None

    def selected_column_mapping(self) -> ColumnMapping | None:
        """Mapeo según combos (índice desde etiqueta «A - …»)."""
        doc_idx = self._index_from_label(self._doc_col_var.get())
        dept_idx = self._index_from_label(self._dept_col_var.get())
        if doc_idx is None or dept_idx is None:
            return self._mapping
        header_used = bool(self._mapping and self._mapping.header_row_used)
        # Si el usuario eligió columnas distintas de la detección con encabezado
        # pero los valores de la primera fila parecen encabezados, conservar flag.
        return ColumnMapping(
            document_column_index=doc_idx,
            department_column_index=dept_idx,
            document_header=self._doc_col_var.get() or None,
            department_header=self._dept_col_var.get() or None,
            header_row_used=header_used,
        )

    def export_mode(self) -> str:
        return self._export_mode_var.get()

    def set_summary_text(self, text: str) -> None:
        self._summary_box.configure(state=tk.NORMAL)
        self._summary_box.delete("1.0", tk.END)
        if text:
            self._summary_box.insert("1.0", text)
        self._summary_box.configure(state=tk.DISABLED)
        self._summary_box.yview_moveto(0.0)

    @staticmethod
    def _index_from_label(label: str) -> int | None:
        if not label:
            return None
        letter = label.split(" - ", 1)[0].strip().upper()
        if not letter.isalpha():
            return None
        value = 0
        for ch in letter:
            value = value * 26 + (ord(ch) - 64)
        return value - 1
