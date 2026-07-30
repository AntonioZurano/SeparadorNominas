"""Interfaz gráfica de Separador de Nóminas PDF (Tkinter)."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from separador_nominas.classification_service import set_export_mode
from separador_nominas.classification_view import ClassificationView
from separador_nominas.constants import (
    APP_CHANNEL_LABEL,
    APP_IS_PRERELEASE,
    APP_NAME,
    APP_VERSION,
    APP_VERSION_DISPLAY,
    LOGGER_NAME,
    PROCESS_MODE_CLASSIFY,
    PROCESS_MODE_CLASSIFY_EXCEL,
    PROCESS_MODE_GROUP,
    PROCESS_MODE_SPLIT,
    PROGRESS_COMPLETE,
    PROGRESS_IDLE,
    STATUS_ANALYZING_SPREADSHEET,
    STATUS_ANALYZING_TEMPLATE,
    STATUS_BETA_NOTICE,
    STATUS_CANCELLED_BY_USER,
    STATUS_CLASSIFY_EXCEL_HINT,
    STATUS_CLASSIFY_STEPS_HINT,
    STATUS_CLASSIFYING,
    STATUS_CLEAR_SESSION_CONFIRM,
    STATUS_COMPLETED,
    STATUS_CONFIRM_PROMPT,
    STATUS_ERROR,
    STATUS_MATCHING_DEPARTMENTS,
    STATUS_OPENING_PDF,
    STATUS_PROCESSING_TEMPLATE,
    STATUS_READY,
    STATUS_REANALYZE_CLASSIFY_CONFIRM,
    STATUS_WAITING_CONFIRMATION,
    STATUS_WRITING_CLASSIFICATION,
    STATUS_WRITING_GROUPS,
    STATUS_WRITING_TEMPLATE,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from separador_nominas.department_assignment_service import (
    apply_spreadsheet_to_session,
    format_excel_match_summary,
)
from separador_nominas.exceptions import SeparadorNominasError, UnexpectedError
from separador_nominas.filename_service import (
    suggest_base_name_from_pdf,
    suggest_output_directory,
)
from separador_nominas.group_export_service import export_classification_session
from separador_nominas.grouped_pdf_service import (
    analyze_payroll_pdf,
    format_grouping_summary,
    write_grouped_pdfs,
)
from separador_nominas.pdf_service import SplitResult, split_pdf
from separador_nominas.recognition_models import GroupingAnalysis, GroupingProcessResult
from separador_nominas.session_service import SessionService
from separador_nominas.spreadsheet_import_view import SpreadsheetImportView
from separador_nominas.spreadsheet_models import SpreadsheetClassificationState
from separador_nominas.spreadsheet_service import (
    import_department_assignments,
    list_sheet_names,
    peek_header_row,
    validate_spreadsheet_path,
)
from separador_nominas.validators import inspect_pdf
from separador_nominas.worker_recognition_service import analyze_classification_pdf

logger = logging.getLogger(LOGGER_NAME)


class SeparadorNominasApp:
    """Ventana principal de la aplicación."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        title_suffix = (
            f" — {APP_CHANNEL_LABEL}" if APP_IS_PRERELEASE else f" — {APP_VERSION}"
        )
        self.root.title(f"{APP_NAME}{title_suffix}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._pdf_path = tk.StringVar(value="")
        self._excel_path = tk.StringVar(value="")
        self._destination_path = tk.StringVar(value="")
        self._base_name = tk.StringVar(value="")
        self._process_mode = tk.StringVar(value=PROCESS_MODE_SPLIT)
        self._status_text = tk.StringVar(value=STATUS_READY)
        self._progress_value = tk.DoubleVar(value=PROGRESS_IDLE)

        self._is_processing = False
        self._awaiting_confirm = False
        self._pending_analysis: GroupingAnalysis | None = None
        self._pending_destination: str | None = None
        self._pending_classify_export = False
        self._pending_excel_export = False
        self._page_count: int | None = None
        self._last_destination: Path | None = None
        self._session_service = SessionService()
        self._beta_notice_shown = False

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._on_mode_changed()
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.DISABLED)
        self._maybe_show_beta_notice()

    def _maybe_show_beta_notice(self) -> None:
        """Muestra el aviso beta una sola vez por sesión (sin persistencia)."""
        if not APP_IS_PRERELEASE or self._beta_notice_shown:
            return
        self._beta_notice_shown = True
        self.root.after(
            200,
            lambda: messagebox.showinfo(
                f"{APP_NAME} — {APP_CHANNEL_LABEL}",
                STATUS_BETA_NOTICE,
                parent=self.root,
            ),
        )

    def _build_ui(self) -> None:
        """Construye los widgets de la interfaz."""
        main = ttk.Frame(self.root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        title_text = (
            f"{APP_NAME} — {APP_CHANNEL_LABEL}"
            if APP_IS_PRERELEASE
            else APP_NAME
        )
        header = ttk.Frame(main)
        header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        ttk.Label(header, text=title_text, font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text=f"Versión {APP_VERSION_DISPLAY}",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        # --- Archivo de origen ---
        source_frame = ttk.LabelFrame(main, text="Archivo de origen", padding=10)
        source_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        source_frame.columnconfigure(1, weight=1)

        ttk.Label(source_frame, text="Archivo PDF de nóminas").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Entry(
            source_frame, textvariable=self._pdf_path, state="readonly"
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self._pdf_button = ttk.Button(
            source_frame, text="Seleccionar PDF", command=self._on_select_pdf
        )
        self._pdf_button.grid(row=1, column=2, sticky="e")

        self._excel_label = ttk.Label(
            source_frame, text="Archivo Excel de departamentos"
        )
        self._excel_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 4))
        self._excel_entry = ttk.Entry(
            source_frame, textvariable=self._excel_path, state="readonly"
        )
        self._excel_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self._excel_button = ttk.Button(
            source_frame, text="Seleccionar Excel", command=self._on_select_excel
        )
        self._excel_button.grid(row=3, column=2, sticky="e")
        self._excel_label.grid_remove()
        self._excel_entry.grid_remove()
        self._excel_button.grid_remove()

        # --- Carpeta de destino ---
        dest_frame = ttk.LabelFrame(main, text="Carpeta de destino", padding=10)
        dest_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        dest_frame.columnconfigure(1, weight=1)

        ttk.Label(dest_frame, text="Carpeta de destino").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Entry(
            dest_frame, textvariable=self._destination_path, state="readonly"
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self._folder_button = ttk.Button(
            dest_frame, text="Seleccionar carpeta", command=self._on_select_folder
        )
        self._folder_button.grid(row=1, column=2, sticky="e")

        # --- Modo de proceso ---
        mode_frame = ttk.LabelFrame(main, text="Modo de proceso", padding=10)
        mode_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Radiobutton(
            mode_frame,
            text="Separar una página por archivo",
            variable=self._process_mode,
            value=PROCESS_MODE_SPLIT,
            command=self._on_mode_changed,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            mode_frame,
            text="Reconocer y agrupar por trabajador",
            variable=self._process_mode,
            value=PROCESS_MODE_GROUP,
            command=self._on_mode_changed,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Radiobutton(
            mode_frame,
            text="Clasificar trabajadores en grupos",
            variable=self._process_mode,
            value=PROCESS_MODE_CLASSIFY,
            command=self._on_mode_changed,
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Radiobutton(
            mode_frame,
            text="Clasificar automáticamente mediante Excel",
            variable=self._process_mode,
            value=PROCESS_MODE_CLASSIFY_EXCEL,
            command=self._on_mode_changed,
        ).grid(row=3, column=0, sticky="w", pady=(4, 0))

        # --- Configuración de nombres ---
        names_frame = ttk.LabelFrame(
            main, text="Configuración de nombres", padding=10
        )
        names_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        names_frame.columnconfigure(1, weight=1)

        ttk.Label(names_frame, text="Nombre base de los archivos").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self._base_name_entry = ttk.Entry(names_frame, textvariable=self._base_name)
        self._base_name_entry.grid(row=1, column=0, columnspan=3, sticky="ew")

        self._names_hint = ttk.Label(
            names_frame,
            text="Ejemplo: Nominas_Julio_2026 → Nominas_Julio_2026_001.pdf",
            foreground="#555555",
        )
        self._names_hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # --- Proceso ---
        process_frame = ttk.LabelFrame(main, text="Proceso", padding=10)
        process_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        process_frame.columnconfigure(0, weight=1)

        process_buttons = ttk.Frame(process_frame)
        process_buttons.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        process_buttons.columnconfigure(0, weight=1)

        self._split_button = ttk.Button(
            process_buttons,
            text="Separar nóminas",
            command=self._on_start,
        )
        self._split_button.grid(row=0, column=0, sticky="w")

        self._clear_session_button = ttk.Button(
            process_buttons,
            text="Limpiar sesión",
            command=self._on_clear_session,
        )
        self._clear_session_button.grid(row=0, column=1, sticky="e")
        self._clear_session_button.grid_remove()

        self._steps_hint = ttk.Label(
            process_frame,
            text="",
            foreground="#555555",
            wraplength=640,
        )
        self._steps_hint.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self._steps_hint.grid_remove()

        progress_row = ttk.Frame(process_frame)
        progress_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        progress_row.columnconfigure(0, weight=1)

        self._progress = ttk.Progressbar(
            progress_row,
            variable=self._progress_value,
            maximum=PROGRESS_COMPLETE,
            mode="determinate",
        )
        self._progress.grid(row=0, column=0, sticky="ew")

        # Fila propia para Generar/Cancelar: evita que el resumen largo
        # empuje el segundo botón fuera del área visible.
        self._confirm_frame = ttk.Frame(process_frame)
        self._confirm_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self._confirm_frame.columnconfigure(0, weight=1)
        self._confirm_summary = tk.StringVar(value="")
        ttk.Label(
            self._confirm_frame,
            textvariable=self._confirm_summary,
            foreground="#333333",
            wraplength=520,
            justify=tk.LEFT,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._confirm_accept_button = ttk.Button(
            self._confirm_frame,
            text="Generar",
            command=self._on_confirm_accept,
            width=10,
        )
        self._confirm_accept_button.grid(row=0, column=1, padx=(0, 4), sticky="e")
        self._confirm_cancel_button = ttk.Button(
            self._confirm_frame,
            text="Cancelar",
            command=self._on_confirm_cancel,
            width=10,
        )
        self._confirm_cancel_button.grid(row=0, column=2, sticky="e")
        self._hide_confirm_actions()

        ttk.Label(process_frame, textvariable=self._status_text).grid(
            row=4, column=0, sticky="w"
        )

        # --- Resultado / clasificación ---
        result_frame = ttk.LabelFrame(main, text="Resultado", padding=10)
        result_frame.grid(row=6, column=0, columnspan=3, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)

        text_frame = ttk.Frame(result_frame)
        text_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self._result_text_frame = text_frame

        self._result_box = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=10,
            relief=tk.SOLID,
            borderwidth=1,
            padx=6,
            pady=4,
            font=("Segoe UI", 9),
        )
        self._result_scroll = ttk.Scrollbar(
            text_frame,
            orient=tk.VERTICAL,
            command=self._result_box.yview,
        )
        self._result_box.configure(yscrollcommand=self._result_scroll.set)
        self._result_box.grid(row=0, column=0, sticky="nsew")
        self._result_scroll.grid(row=0, column=1, sticky="ns")
        self._result_box.configure(state=tk.DISABLED)
        self._result_box.bind("<MouseWheel>", self._on_result_mousewheel)
        self._result_box.bind("<Button-4>", self._on_result_mousewheel)
        self._result_box.bind("<Button-5>", self._on_result_mousewheel)

        self._classification_view = ClassificationView(
            result_frame,
            on_changed=self._on_classification_changed,
        )
        self._classification_view.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._classification_view.grid_remove()

        self._spreadsheet_view = SpreadsheetImportView(
            result_frame,
            on_changed=self._on_classification_changed,
        )
        self._spreadsheet_view.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._spreadsheet_view.grid_remove()

        self._open_folder_button = ttk.Button(
            result_frame,
            text="Abrir carpeta de destino",
            command=self._on_open_folder,
        )
        self._open_folder_button.grid(row=1, column=0, sticky="w")

    def _hide_confirm_actions(self) -> None:
        """Oculta el panel de confirmación embebido."""
        self._awaiting_confirm = False
        self._pending_analysis = None
        self._pending_destination = None
        self._pending_classify_export = False
        self._pending_excel_export = False
        self._confirm_summary.set("")
        self._confirm_frame.grid_remove()
        self._confirm_accept_button.configure(state=tk.DISABLED)
        self._confirm_cancel_button.configure(state=tk.DISABLED)

    def _show_confirm_actions(
        self,
        analysis: GroupingAnalysis | None,
        destination: str,
        *,
        classify: bool = False,
        excel: bool = False,
        summary_label: str = "",
    ) -> None:
        """Muestra Generar/Cancelar junto a la barra sin diálogo modal."""
        self._pending_analysis = analysis
        self._pending_destination = destination
        self._pending_classify_export = classify
        self._pending_excel_export = excel
        self._awaiting_confirm = True
        if summary_label:
            self._confirm_summary.set(summary_label)
        elif analysis is not None:
            self._confirm_summary.set(
                f"{STATUS_CONFIRM_PROMPT}  "
                f"{len(analysis.groups)} trab. / "
                f"{len(analysis.unrecognized_page_numbers)} no rec."
            )
        else:
            self._confirm_summary.set(STATUS_CONFIRM_PROMPT)
        self._confirm_frame.grid()
        self._confirm_accept_button.configure(state=tk.NORMAL)
        self._confirm_cancel_button.configure(state=tk.NORMAL)

    def _on_confirm_accept(self) -> None:
        """Confirma la escritura de PDF agrupados o clasificación."""
        if not self._awaiting_confirm:
            return
        destination = self._pending_destination
        if destination is None:
            return

        if self._pending_classify_export or self._pending_excel_export:
            session = self._session_service.session
            if session is None:
                return
            if self._pending_excel_export:
                state = self._session_service.spreadsheet_state
                summary = "Se generarán los PDF por departamento."
                if state and state.match_summary:
                    summary = (
                        f"Asignados: {state.match_summary.matched_workers}. "
                        f"No clasificadas: "
                        f"{state.match_summary.pages_unclassified} páginas."
                    )
            else:
                summary = self._classification_view.build_export_summary()
            if not messagebox.askyesno(
                APP_NAME,
                f"{summary}\n\n¿Generar los archivos PDF ahora?",
            ):
                return
            destination_local = destination
            excel_mode = self._pending_excel_export
            self._hide_confirm_actions()
            self._status_text.set(STATUS_WRITING_CLASSIFICATION)
            self._progress_value.set(PROGRESS_IDLE)
            self._is_processing = True
            self._set_controls_enabled(False)
            self._show_result_text_area()
            self._set_result_text("Generando archivos PDF...")
            self.root.update_idletasks()
            worker = threading.Thread(
                target=self._run_write_classification,
                args=(destination_local, excel_mode),
                daemon=True,
            )
            worker.start()
            return

        analysis = self._pending_analysis
        if analysis is None:
            return

        self._hide_confirm_actions()
        self._status_text.set(STATUS_WRITING_GROUPS)
        self._progress_value.set(PROGRESS_IDLE)
        self._set_result_text("Generando archivos PDF...")
        self.root.update_idletasks()
        worker = threading.Thread(
            target=self._run_write_groups,
            args=(analysis, destination),
            daemon=True,
        )
        worker.start()

    def _on_confirm_cancel(self) -> None:
        """Cancela la escritura tras el análisis."""
        if not self._awaiting_confirm:
            return
        self._hide_confirm_actions()
        self._is_processing = False
        self._status_text.set(STATUS_CANCELLED_BY_USER)
        self._set_controls_enabled(True)
        logger.info("Escritura cancelada por el usuario")

    def _on_result_mousewheel(self, event: tk.Event[tk.Misc]) -> str:
        """Desplaza el área de resultado con la rueda del ratón."""
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self._result_box.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self._result_box.yview_scroll(1, "units")
        return "break"

    def _set_result_text(self, text: str) -> None:
        """Actualiza el área de resultado (con scroll) de forma segura."""
        self._result_box.configure(state=tk.NORMAL)
        self._result_box.delete("1.0", tk.END)
        if text:
            self._result_box.insert("1.0", text)
        self._result_box.configure(state=tk.DISABLED)
        self._result_box.yview_moveto(0.0)

    def _on_mode_changed(self) -> None:
        """Ajusta controles según el modo seleccionado."""
        mode = self._process_mode.get()
        show_excel = mode == PROCESS_MODE_CLASSIFY_EXCEL
        if show_excel:
            self._excel_label.grid()
            self._excel_entry.grid()
            self._excel_button.grid()
        else:
            self._excel_label.grid_remove()
            self._excel_entry.grid_remove()
            self._excel_button.grid_remove()

        if mode == PROCESS_MODE_GROUP:
            self._split_button.configure(text="Reconocer y agrupar")
            self._names_hint.configure(
                text=(
                    "En este modo el nombre del archivo se obtiene del trabajador "
                    "reconocido. Las páginas sin nombre van a No_reconocidas/."
                )
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.DISABLED)
            self._clear_session_button.grid_remove()
            self._set_classify_step_labels(False)
            if not self._session_service.has_session():
                self._show_result_text_area()
        elif mode == PROCESS_MODE_CLASSIFY:
            self._names_hint.configure(
                text=(
                    "Detecta DNI/NIE y nombre, crea grupos (p. ej. departamentos) "
                    "y exporta por trabajador o en un PDF conjunto por grupo."
                )
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.DISABLED)
            self._set_classify_step_labels(True)
            if self._session_service.has_session():
                self._clear_session_button.grid()
                self._show_classification_area()
            else:
                self._clear_session_button.grid_remove()
                self._show_result_text_area()
        elif mode == PROCESS_MODE_CLASSIFY_EXCEL:
            self._names_hint.configure(
                text=(
                    "Relaciona DNI/NIE del PDF con el Excel de departamentos "
                    "y genera un PDF por departamento. Sin persistencia."
                )
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.DISABLED)
            self._set_classify_excel_step_labels(True)
            if self._session_service.has_session():
                self._clear_session_button.grid()
                self._show_spreadsheet_area()
            else:
                self._clear_session_button.grid_remove()
                self._show_result_text_area()
        else:
            self._names_hint.configure(
                text="Ejemplo: Nominas_Julio_2026 → Nominas_Julio_2026_001.pdf"
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.NORMAL)
            self._clear_session_button.grid_remove()
            self._set_classify_step_labels(False)
            self._show_result_text_area()

    def _set_classify_step_labels(self, enabled: bool) -> None:
        """Numera botones del flujo de clasificación (pasos 1–7)."""
        if enabled:
            self._pdf_button.configure(text="1. Seleccionar PDF")
            self._folder_button.configure(text="2. Seleccionar carpeta")
            self._split_button.configure(text="3. Analizar y clasificar")
            self._confirm_accept_button.configure(text="6. Generar", width=12)
            self._open_folder_button.configure(text="7. Abrir carpeta de destino")
            self._steps_hint.configure(text=STATUS_CLASSIFY_STEPS_HINT)
            self._steps_hint.grid()
            self._classification_view.set_step_labels(True)
        else:
            self._pdf_button.configure(text="Seleccionar PDF")
            self._folder_button.configure(text="Seleccionar carpeta")
            mode = self._process_mode.get()
            if mode == PROCESS_MODE_GROUP:
                self._split_button.configure(text="Reconocer y agrupar")
            elif mode == PROCESS_MODE_CLASSIFY_EXCEL:
                self._split_button.configure(text="Analizar con Excel")
            else:
                self._split_button.configure(text="Separar nóminas")
            self._confirm_accept_button.configure(text="Generar", width=10)
            self._open_folder_button.configure(text="Abrir carpeta de destino")
            self._steps_hint.configure(text="")
            self._steps_hint.grid_remove()
            self._classification_view.set_step_labels(False)

    def _set_classify_excel_step_labels(self, enabled: bool) -> None:
        """Etiquetas del flujo Excel."""
        if enabled:
            self._pdf_button.configure(text="Seleccionar PDF")
            self._excel_button.configure(text="Seleccionar Excel")
            self._folder_button.configure(text="Seleccionar carpeta")
            self._split_button.configure(text="Analizar con Excel")
            self._confirm_accept_button.configure(text="Generar", width=10)
            self._open_folder_button.configure(text="Abrir carpeta de destino")
            self._steps_hint.configure(text=STATUS_CLASSIFY_EXCEL_HINT)
            self._steps_hint.grid()
            self._classification_view.set_step_labels(False)
        else:
            self._set_classify_step_labels(False)

    def _show_result_text_area(self) -> None:
        self._classification_view.grid_remove()
        self._spreadsheet_view.grid_remove()
        self._result_text_frame.grid()

    def _show_classification_area(self) -> None:
        self._result_text_frame.grid_remove()
        self._spreadsheet_view.grid_remove()
        self._classification_view.grid()

    def _show_spreadsheet_area(self) -> None:
        self._result_text_frame.grid_remove()
        self._classification_view.grid_remove()
        self._spreadsheet_view.grid()

    def _on_classification_changed(self) -> None:
        """Actualiza el resumen de confirmación si está visible."""
        if self._awaiting_confirm and self._pending_classify_export:
            session = self._session_service.session
            if session is not None:
                self._confirm_summary.set(
                    f"{STATUS_CONFIRM_PROMPT}  "
                    f"{len(session.groups)} grupos / "
                    f"{len(session.workers)} trab."
                )

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Activa o desactiva los controles durante el proceso."""
        state = tk.NORMAL if enabled else tk.DISABLED
        for child in self.root.winfo_children():
            self._set_widget_tree_state(child, state)
        self._split_button.configure(state=state)
        if enabled:
            self._on_mode_changed()
        else:
            self._base_name_entry.configure(state=tk.DISABLED)
        if enabled and self._last_destination is not None:
            self._open_folder_button.configure(state=tk.NORMAL)
        elif not enabled:
            self._open_folder_button.configure(state=tk.DISABLED)
        # El panel de confirmación solo se habilita en _show_confirm_actions.
        if not self._awaiting_confirm:
            self._confirm_accept_button.configure(state=tk.DISABLED)
            self._confirm_cancel_button.configure(state=tk.DISABLED)
        else:
            self._confirm_frame.grid()
            self._confirm_accept_button.configure(state=tk.NORMAL)
            self._confirm_cancel_button.configure(state=tk.NORMAL)
            if self._process_mode.get() == PROCESS_MODE_CLASSIFY:
                self._confirm_accept_button.configure(text="6. Generar", width=12)

    def _set_widget_tree_state(self, widget: tk.Misc, state: str) -> None:
        """Aplica estado a botones de forma recursiva (excepto progreso)."""
        if isinstance(widget, (ttk.Button, ttk.Radiobutton)):
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._set_widget_tree_state(child, state)

    def _start_indeterminate_progress(self) -> None:
        """Activa la barra en modo indeterminado (espera sin porcentaje)."""
        self._progress.stop()
        self._progress.configure(mode="indeterminate")
        self._progress.start(12)

    def _stop_indeterminate_progress(self) -> None:
        """Restaura la barra a modo determinado al 0 %."""
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress_value.set(PROGRESS_IDLE)

    def _on_select_pdf(self) -> None:
        """Abre el diálogo de selección de PDF."""
        if self._is_processing:
            return

        selected = filedialog.askopenfilename(
            title="Seleccionar PDF de nóminas",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not selected:
            self._status_text.set(STATUS_READY)
            return

        self._is_processing = True
        self._set_controls_enabled(False)
        self._set_result_text("")
        self._status_text.set(STATUS_OPENING_PDF)
        self._start_indeterminate_progress()
        logger.info("Validando PDF seleccionado en segundo plano")

        worker = threading.Thread(
            target=self._run_inspect_pdf,
            args=(selected,),
            daemon=True,
        )
        worker.start()

    def _run_inspect_pdf(self, selected: str) -> None:
        """Valida el PDF fuera del hilo de la interfaz."""
        try:
            path, page_count = inspect_pdf(selected)
            self.root.after(
                0,
                lambda: self._on_pdf_inspect_success(path, page_count),
            )
        except SeparadorNominasError as exc:
            message = exc.user_message
            self.root.after(0, lambda: self._on_pdf_inspect_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Error inesperado al seleccionar PDF: %s",
                type(exc).__name__,
            )
            self.root.after(
                0,
                lambda: self._on_pdf_inspect_error(
                    "No se ha podido abrir el PDF seleccionado.\n"
                    "Comprueba que el archivo no esté dañado "
                    "ni protegido con contraseña."
                ),
            )

    def _on_pdf_inspect_success(self, path: Path, page_count: int) -> None:
        """Aplica en la UI el resultado de la validación del PDF."""
        self._stop_indeterminate_progress()
        self._is_processing = False
        if self._session_service.has_session():
            self._session_service.clear_session()
            self._classification_view.set_session(None)
            self._spreadsheet_view.clear()
            self._clear_session_button.grid_remove()
            self._hide_confirm_actions()
        self._pdf_path.set(str(path))
        self._page_count = page_count
        self._base_name.set(suggest_base_name_from_pdf(path))
        self._destination_path.set(str(suggest_output_directory(path)))
        self._status_text.set(
            f"PDF seleccionado: {page_count} página{'s' if page_count != 1 else ''}."
        )
        self._last_destination = None
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.DISABLED)
        self._show_result_text_area()
        self._set_result_text("")

    def _on_pdf_inspect_error(self, message: str) -> None:
        """Maneja un error al validar el PDF seleccionado."""
        self._stop_indeterminate_progress()
        self._is_processing = False
        self._status_text.set(STATUS_ERROR)
        self._set_controls_enabled(True)
        self._show_error(message)

    def _on_select_folder(self) -> None:
        """Abre el diálogo de selección de carpeta."""
        if self._is_processing:
            return

        selected = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not selected:
            return

        self._destination_path.set(selected)

    def _on_select_excel(self) -> None:
        """Abre el diálogo de selección de Excel y carga metadatos."""
        if self._is_processing:
            return
        selected = filedialog.askopenfilename(
            title="Seleccionar Excel de departamentos",
            filetypes=[
                ("Excel", "*.xlsx *.xls"),
                ("Excel 2007+", "*.xlsx"),
                ("Excel 97-2003", "*.xls"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not selected:
            return
        try:
            path = validate_spreadsheet_path(selected)
            sheets = list_sheet_names(path)
            sheet = sheets[0]
            _used, headers = peek_header_row(path, sheet_name=sheet)
            self._excel_path.set(str(path))
            self._spreadsheet_view.set_workbook_meta(
                sheets, selected_sheet=sheet, headers=headers
            )
            self._session_service.set_spreadsheet_state(
                SpreadsheetClassificationState(source_spreadsheet=path)
            )
            self._status_text.set(
                f"Excel seleccionado: {len(sheets)} hoja"
                f"{'s' if len(sheets) != 1 else ''}."
            )
            self._show_spreadsheet_area()
        except SeparadorNominasError as exc:
            self._show_error(exc.user_message)
        except Exception:  # noqa: BLE001
            logger.exception("Error al abrir Excel")
            self._show_error(
                "No se ha podido abrir el archivo Excel.\n"
                "Comprueba que no esté dañado ni protegido."
            )

    def _start_classify_excel_process(self) -> None:
        """Analiza PDF + Excel y prepara la clasificación automática."""
        pdf = self._pdf_path.get().strip()
        excel = self._excel_path.get().strip()
        destination = self._destination_path.get().strip()
        if not excel:
            self._show_error("No se ha seleccionado ningún archivo Excel.")
            return

        if self._session_service.has_session():
            if not messagebox.askyesno(
                APP_NAME,
                STATUS_REANALYZE_CLASSIFY_CONFIRM,
            ):
                return

        sheet = self._spreadsheet_view.selected_sheet()
        mapping = self._spreadsheet_view.selected_column_mapping()

        self._is_processing = True
        self._set_controls_enabled(False)
        self._hide_confirm_actions()
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_IDLE)
        self._show_result_text_area()
        self._set_result_text("")
        self._status_text.set(STATUS_ANALYZING_SPREADSHEET)
        logger.info("Inicio del análisis Excel + PDF")

        worker = threading.Thread(
            target=self._run_classify_excel_analyze,
            args=(pdf, excel, destination, sheet, mapping),
            daemon=True,
        )
        worker.start()

    def _run_classify_excel_analyze(
        self,
        pdf: str,
        excel: str,
        destination: str,
        sheet: str | None,
        mapping: object,
    ) -> None:
        """Hilo: importa Excel, analiza PDF y aplica asignaciones."""
        try:
            imported = import_department_assignments(
                excel,
                sheet_name=sheet,
                column_mapping=mapping,  # type: ignore[arg-type]
            )
            self.root.after(
                0, lambda: self._status_text.set(STATUS_MATCHING_DEPARTMENTS)
            )
            session = analyze_classification_pdf(
                pdf,
                progress_callback=self._schedule_analyze_progress,
            )
            applied = apply_spreadsheet_to_session(session, imported)
            summary = format_excel_match_summary(session, applied, imported)
            self.root.after(
                0,
                lambda: self._on_classify_excel_ready(
                    session, imported, applied, summary, destination, excel
                ),
            )
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _on_classify_excel_ready(
        self,
        session: object,
        imported: object,
        applied: object,
        summary: str,
        destination: str,
        excel: str,
    ) -> None:
        """Muestra la vista previa tras el cruce Excel-PDF."""
        from separador_nominas.classification_models import ClassificationSession
        from separador_nominas.department_assignment_service import (
            AssignmentApplyResult,
        )
        from separador_nominas.spreadsheet_models import SpreadsheetImportResult

        assert isinstance(session, ClassificationSession)
        assert isinstance(imported, SpreadsheetImportResult)
        assert isinstance(applied, AssignmentApplyResult)

        self._session_service.set_session(session)
        state = SpreadsheetClassificationState(
            source_spreadsheet=Path(excel),
            sheet_name=imported.sheet_name,
            import_result=imported,
            match_summary=applied.summary,
            unresolved_conflict_docs={
                c.document_id for c in applied.unresolved_conflicts
            },
        )
        self._session_service.set_spreadsheet_state(state)
        self._spreadsheet_view.set_summary_text(summary)
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_WAITING_CONFIRMATION)
        self._is_processing = False
        self._show_spreadsheet_area()
        self._clear_session_button.grid()
        self._set_controls_enabled(True)
        label = (
            f"{STATUS_CONFIRM_PROMPT}  "
            f"{applied.summary.matched_workers} asignados / "
            f"{applied.summary.pages_unclassified} no clasif."
        )
        self._show_confirm_actions(
            None,
            destination,
            excel=True,
            summary_label=label,
        )
        self.root.update_idletasks()

    def _on_start(self) -> None:
        """Inicia el proceso según el modo seleccionado."""
        if self._is_processing:
            return

        mode = self._process_mode.get()
        if mode == PROCESS_MODE_GROUP:
            self._start_group_process()
        elif mode == PROCESS_MODE_CLASSIFY:
            self._start_classify_process()
        elif mode == PROCESS_MODE_CLASSIFY_EXCEL:
            self._start_classify_excel_process()
        else:
            self._start_split_process()

    def _start_split_process(self) -> None:
        """Inicia la separación página a página en un hilo de fondo."""
        pdf = self._pdf_path.get().strip()
        destination = self._destination_path.get().strip()
        base_name = self._base_name.get()

        self._is_processing = True
        self._set_controls_enabled(False)
        self._hide_confirm_actions()
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_IDLE)
        self._set_result_text("")
        self._status_text.set(STATUS_READY)
        logger.info("Inicio del proceso de separación")

        worker = threading.Thread(
            target=self._run_split,
            args=(pdf, destination, base_name),
            daemon=True,
        )
        worker.start()

    def _start_group_process(self) -> None:
        """Inicia el análisis de reconocimiento en un hilo de fondo."""
        pdf = self._pdf_path.get().strip()
        destination = self._destination_path.get().strip()

        self._is_processing = True
        self._set_controls_enabled(False)
        self._hide_confirm_actions()
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_IDLE)
        self._show_result_text_area()
        self._set_result_text("")
        self._status_text.set(STATUS_READY)
        logger.info("Inicio del análisis de reconocimiento")

        worker = threading.Thread(
            target=self._run_analyze,
            args=(pdf, destination),
            daemon=True,
        )
        worker.start()

    def _start_classify_process(self) -> None:
        """Inicia el análisis de clasificación en un hilo de fondo."""
        pdf = self._pdf_path.get().strip()
        destination = self._destination_path.get().strip()

        # Conservar el panel Generar si el usuario cancela el reanálisis
        # (evita perderlo por click-through del modal sobre Cancelar).
        restore_confirm = (
            self._awaiting_confirm
            and self._pending_classify_export
            and self._pending_destination
        )
        saved_destination = self._pending_destination or destination

        if self._session_service.has_session():
            session = self._session_service.session
            has_work = bool(
                session
                and (
                    session.groups
                    or session.workers
                    or any(g.worker_ids for g in session.groups.values())
                )
            )
            if has_work:
                if restore_confirm:
                    self._confirm_accept_button.configure(state=tk.DISABLED)
                    self._confirm_cancel_button.configure(state=tk.DISABLED)
                self.root.update_idletasks()
                if not messagebox.askyesno(
                    APP_NAME,
                    STATUS_REANALYZE_CLASSIFY_CONFIRM,
                ):
                    if restore_confirm:
                        self._restore_classify_generate_button(saved_destination)
                    return

        self._is_processing = True
        self._set_controls_enabled(False)
        self._hide_confirm_actions()
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_IDLE)
        self._show_result_text_area()
        self._set_result_text("")
        self._status_text.set(STATUS_READY)
        logger.info("Inicio del análisis de clasificación")

        worker = threading.Thread(
            target=self._run_classify_analyze,
            args=(pdf, destination),
            daemon=True,
        )
        worker.start()

    def _restore_classify_generate_button(self, destination: str) -> None:
        """Vuelve a mostrar «6. Generar» tras cancelar el reanálisis."""
        session = self._session_service.session
        if session is None:
            self._hide_confirm_actions()
            return
        label = (
            f"{STATUS_CONFIRM_PROMPT}  "
            f"{len(session.groups)} grupos / "
            f"{len(session.workers)} trab."
        )
        self._show_classification_area()
        self._show_confirm_actions(
            None,
            destination,
            classify=True,
            summary_label=label,
        )
        if self._process_mode.get() == PROCESS_MODE_CLASSIFY:
            self._confirm_accept_button.configure(text="6. Generar", width=12)
        self._status_text.set(STATUS_CLASSIFYING)

    def _run_classify_analyze(self, pdf: str, destination: str) -> None:
        """Analiza el PDF para clasificación."""
        try:
            session = analyze_classification_pdf(
                pdf,
                progress_callback=self._schedule_analyze_progress,
            )
            self.root.after(
                0,
                lambda: self._on_classify_analysis_ready(session, destination),
            )
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _on_classify_analysis_ready(self, session: object, destination: str) -> None:
        """Muestra el panel de clasificación tras el análisis."""
        from separador_nominas.classification_models import ClassificationSession

        assert isinstance(session, ClassificationSession)
        self._session_service.set_session(session)
        self._classification_view.set_session(session)
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_CLASSIFYING)
        self._is_processing = False
        self._show_classification_area()
        self._clear_session_button.grid()
        self._set_controls_enabled(True)
        # Mostrar Generar DESPUÉS de reactivar controles (mode_changed no lo oculta).
        self._restore_classify_generate_button(destination)
        self.root.update_idletasks()

    def _run_write_classification(
        self, destination: str, excel_mode: bool = False
    ) -> None:
        """Exporta la clasificación fuera del hilo de la interfaz."""
        session = self._session_service.session
        if session is None:
            self.root.after(
                0,
                lambda: self._on_process_error(
                    "No hay una sesión de clasificación activa."
                ),
            )
            return
        try:
            if excel_mode:
                from separador_nominas.classification_models import ExportMode

                mode = self._spreadsheet_view.export_mode()
                export_mode: ExportMode = (
                    "separate" if mode == "separate" else "combined"
                )
                for group in session.groups.values():
                    set_export_mode(session, group.group_id, export_mode)
            result = export_classification_session(
                session,
                destination,
                progress_callback=self._schedule_write_progress,
                create_destination=True,
                unclassified_mode=(
                    "combined_folder" if excel_mode else "omit"
                ),
            )
            self.root.after(0, lambda: self._on_classify_success(result))
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _on_classify_success(self, result: object) -> None:
        """Finalización correcta de la exportación por grupos."""
        from separador_nominas.classification_models import ClassificationExportResult

        assert isinstance(result, ClassificationExportResult)
        self._hide_confirm_actions()
        self._is_processing = False
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_COMPLETED)
        self._last_destination = result.destination_dir
        self._show_result_text_area()
        lines = [
            f"Archivos generados: {result.files_created}",
            f"Archivos de grupos: {len(result.group_files)}",
            f"Archivos en No_reconocidas: {len(result.unrecognized_files)}",
            f"Reconocidos sin asignar omitidos: {result.unassigned_recognized_count}",
            f"Carpeta de destino:\n{result.destination_dir}",
        ]
        self._set_result_text("\n".join(lines))
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.NORMAL)
        if self._session_service.has_session():
            self._clear_session_button.grid()

    def _on_clear_session(self) -> None:
        """Pide confirmación y limpia la sesión de clasificación."""
        if self._is_processing:
            return
        if not self._session_service.has_session():
            return
        if not messagebox.askyesno(APP_NAME, STATUS_CLEAR_SESSION_CONFIRM):
            return
        self._session_service.clear_session()
        self._classification_view.set_session(None)
        self._spreadsheet_view.clear()
        self._excel_path.set("")
        self._hide_confirm_actions()
        self._clear_session_button.grid_remove()
        self._show_result_text_area()
        self._set_result_text("")
        self._status_text.set(STATUS_READY)
        logger.info("Sesión limpiada por el usuario")

    def _on_close(self) -> None:
        """Limpia la sesión en memoria al cerrar la ventana."""
        self._session_service.clear_session()
        self.root.destroy()

    def _run_split(self, pdf: str, destination: str, base_name: str) -> None:
        """Ejecuta la separación fuera del hilo de la interfaz."""
        try:
            result = split_pdf(
                pdf,
                destination,
                base_name,
                progress_callback=self._schedule_progress,
                create_destination=True,
            )
            self.root.after(0, lambda: self._on_split_success(result))
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _run_analyze(self, pdf: str, destination: str) -> None:
        """Analiza el PDF y solicita confirmación antes de escribir."""
        try:
            analysis = analyze_payroll_pdf(
                pdf,
                progress_callback=self._schedule_analyze_progress,
            )
            self.root.after(
                0,
                lambda: self._on_analysis_ready(analysis, destination),
            )
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _on_analysis_ready(
        self, analysis: GroupingAnalysis, destination: str
    ) -> None:
        """Muestra el resumen y el panel de confirmación (sin modal)."""
        summary = format_grouping_summary(analysis)
        self._stop_indeterminate_progress()
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_WAITING_CONFIRMATION)
        self._set_result_text(summary)
        self._show_confirm_actions(analysis, destination)
        self.root.update_idletasks()

    def _run_write_groups(
        self, analysis: GroupingAnalysis, destination: str
    ) -> None:
        """Escribe los PDF agrupados fuera del hilo de la interfaz."""
        try:
            result = write_grouped_pdfs(
                analysis,
                destination,
                progress_callback=self._schedule_write_progress,
                create_destination=True,
            )
            self.root.after(0, lambda: self._on_group_success(result))
        except SeparadorNominasError as exc:
            logger.error("Error de dominio: %s", type(exc).__name__)
            message = exc.user_message
            self.root.after(0, lambda: self._on_process_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_process_error(message))

    def _schedule_progress(
        self, current: int, total: int, _output_path: Path
    ) -> None:
        """Programa la actualización de progreso en el hilo principal."""
        self.root.after(0, lambda: self._update_progress(current, total))

    def _schedule_analyze_progress(self, current: int, total: int) -> None:
        """Progreso durante el análisis de reconocimiento."""
        self.root.after(0, lambda: self._update_analyze_progress(current, total))

    def _schedule_write_progress(
        self, current: int, total: int, _output_path: Path
    ) -> None:
        """Progreso durante la escritura de grupos."""
        self.root.after(0, lambda: self._update_write_progress(current, total))

    def _update_progress(self, current: int, total: int) -> None:
        """Actualiza barra y texto de estado (modo separación)."""
        percent = (current / total) * PROGRESS_COMPLETE if total else PROGRESS_IDLE
        self._progress_value.set(percent)
        self._status_text.set(
            STATUS_PROCESSING_TEMPLATE.format(current=current, total=total)
        )

    def _update_analyze_progress(self, current: int, total: int) -> None:
        """Actualiza barra y texto durante el análisis."""
        percent = (current / total) * PROGRESS_COMPLETE if total else PROGRESS_IDLE
        self._progress_value.set(percent)
        self._status_text.set(
            STATUS_ANALYZING_TEMPLATE.format(current=current, total=total)
        )

    def _update_write_progress(self, current: int, total: int) -> None:
        """Actualiza barra durante la escritura de archivos agrupados."""
        percent = (current / total) * PROGRESS_COMPLETE if total else PROGRESS_IDLE
        self._progress_value.set(percent)
        self._status_text.set(
            STATUS_WRITING_TEMPLATE.format(current=current, total=total)
        )
        self.root.update_idletasks()

    def _on_split_success(self, result: SplitResult) -> None:
        """Maneja la finalización correcta del proceso de separación."""
        self._is_processing = False
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_COMPLETED)
        self._last_destination = result.destination_dir
        self._set_result_text(
            f"Se han generado {result.files_created} archivo"
            f"{'s' if result.files_created != 1 else ''}.\n"
            f"Carpeta de destino:\n{result.destination_dir}"
        )
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.NORMAL)
        messagebox.showinfo(
            APP_NAME,
            f"Proceso completado correctamente.\n\n"
            f"Archivos generados: {result.files_created}",
        )

    def _on_group_success(self, result: GroupingProcessResult) -> None:
        """Maneja la finalización correcta del modo agrupar."""
        self._hide_confirm_actions()
        self._is_processing = False
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_COMPLETED)
        self._last_destination = result.destination_dir
        summary_lines = [
            f"Trabajadores reconocidos: {result.recognized_worker_count}",
            f"Archivos de trabajador: {len(result.output_files)}",
            f"Páginas no reconocidas: {len(result.unrecognized_page_numbers)}",
            f"Archivos en No_reconocidas: {len(result.unrecognized_files)}",
            f"Carpeta de destino:\n{result.destination_dir}",
        ]
        self._set_result_text("\n".join(summary_lines))
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.NORMAL)

    def _on_process_error(self, message: str) -> None:
        """Maneja un error durante el proceso."""
        self._hide_confirm_actions()
        self._stop_indeterminate_progress()
        self._is_processing = False
        self._status_text.set(STATUS_ERROR)
        self._set_controls_enabled(True)
        self._show_error(message)

    def _show_error(self, message: str) -> None:
        """Muestra un mensaje de error comprensible."""
        messagebox.showerror(APP_NAME, message)

    def _on_open_folder(self) -> None:
        """Abre la carpeta de destino en el explorador del sistema."""
        destination = self._last_destination
        if destination is None:
            raw = self._destination_path.get().strip()
            if raw:
                destination = Path(raw)
        if destination is None or not destination.exists():
            self._show_error("La carpeta de destino no está disponible.")
            return

        try:
            open_folder(destination)
        except OSError:
            self._show_error("No se ha podido abrir la carpeta de destino.")


def _running_in_wsl() -> bool:
    """True si el proceso se ejecuta dentro de WSL."""
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        version = Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "microsoft" in version or "wsl" in version


def open_folder(path: Path) -> None:
    """Abre una carpeta con el explorador del sistema operativo."""
    resolved = path.resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(resolved))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(resolved)], check=False)
        return
    if _running_in_wsl():
        # En WSL, xdg-open no abre el Explorador de Windows de forma fiable.
        try:
            win_path = subprocess.check_output(
                ["wslpath", "-w", str(resolved)],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise OSError(
                "No se ha podido convertir la ruta para el Explorador de Windows."
            ) from exc
        # explorer.exe puede devolver código distinto de 0 aunque abra bien.
        subprocess.run(
            ["explorer.exe", win_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    subprocess.run(["xdg-open", str(resolved)], check=False)


def _maximize_main_window(root: tk.Tk) -> None:
    """
    Maximiza la ventana principal al arrancar.

    Usa el estado «zoomed» del gestor de ventanas (no fullscreen sin bordes),
    para que quepan los paneles de clasificación/Excel en pantallas normales.
    """
    root.update_idletasks()
    try:
        root.state("zoomed")
        return
    except tk.TclError:
        pass
    try:
        root.attributes("-zoomed", True)
        return
    except tk.TclError:
        pass
    # Último recurso: ocupar casi toda el área disponible.
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+0+0")


def run_app() -> None:
    """Crea la ventana principal y arranca el bucle de eventos."""
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass

    SeparadorNominasApp(root)
    _maximize_main_window(root)
    root.mainloop()
