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

from separador_nominas.constants import (
    APP_NAME,
    APP_VERSION,
    LOGGER_NAME,
    PROCESS_MODE_GROUP,
    PROCESS_MODE_SPLIT,
    PROGRESS_COMPLETE,
    PROGRESS_IDLE,
    STATUS_ANALYZING_TEMPLATE,
    STATUS_CANCELLED_BY_USER,
    STATUS_COMPLETED,
    STATUS_ERROR,
    STATUS_PROCESSING_TEMPLATE,
    STATUS_READY,
    STATUS_WAITING_CONFIRMATION,
    STATUS_WRITING_GROUPS,
    STATUS_WRITING_TEMPLATE,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from separador_nominas.exceptions import SeparadorNominasError, UnexpectedError
from separador_nominas.filename_service import (
    suggest_base_name_from_pdf,
    suggest_output_directory,
)
from separador_nominas.grouped_pdf_service import (
    analyze_payroll_pdf,
    format_grouping_summary,
    write_grouped_pdfs,
)
from separador_nominas.pdf_service import SplitResult, split_pdf
from separador_nominas.recognition_models import GroupingAnalysis, GroupingProcessResult
from separador_nominas.validators import get_pdf_page_count, validate_pdf_path

logger = logging.getLogger(LOGGER_NAME)


class SeparadorNominasApp:
    """Ventana principal de la aplicación."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_NAME} — {APP_VERSION}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._pdf_path = tk.StringVar(value="")
        self._destination_path = tk.StringVar(value="")
        self._base_name = tk.StringVar(value="")
        self._process_mode = tk.StringVar(value=PROCESS_MODE_SPLIT)
        self._status_text = tk.StringVar(value=STATUS_READY)
        self._result_text = tk.StringVar(value="")
        self._progress_value = tk.DoubleVar(value=PROGRESS_IDLE)

        self._is_processing = False
        self._page_count: int | None = None
        self._last_destination: Path | None = None

        self._build_ui()
        self._on_mode_changed()
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.DISABLED)

    def _build_ui(self) -> None:
        """Construye los widgets de la interfaz."""
        main = ttk.Frame(self.root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        title = ttk.Label(main, text=APP_NAME, font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

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
        ttk.Button(
            source_frame, text="Seleccionar PDF", command=self._on_select_pdf
        ).grid(row=1, column=2, sticky="e")

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
        ttk.Button(
            dest_frame, text="Seleccionar carpeta", command=self._on_select_folder
        ).grid(row=1, column=2, sticky="e")

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

        self._split_button = ttk.Button(
            process_frame,
            text="Separar nóminas",
            command=self._on_start,
        )
        self._split_button.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self._progress = ttk.Progressbar(
            process_frame,
            variable=self._progress_value,
            maximum=PROGRESS_COMPLETE,
            mode="determinate",
        )
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(process_frame, textvariable=self._status_text).grid(
            row=2, column=0, sticky="w"
        )

        # --- Resultado ---
        result_frame = ttk.LabelFrame(main, text="Resultado", padding=10)
        result_frame.grid(row=6, column=0, columnspan=3, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)

        ttk.Label(
            result_frame, textvariable=self._result_text, wraplength=620, justify="left"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._open_folder_button = ttk.Button(
            result_frame,
            text="Abrir carpeta de destino",
            command=self._on_open_folder,
        )
        self._open_folder_button.grid(row=1, column=0, sticky="w")

    def _on_mode_changed(self) -> None:
        """Ajusta controles según el modo seleccionado."""
        group_mode = self._process_mode.get() == PROCESS_MODE_GROUP
        if group_mode:
            self._split_button.configure(text="Reconocer y agrupar")
            self._names_hint.configure(
                text=(
                    "En este modo el nombre del archivo se obtiene del trabajador "
                    "reconocido. Las páginas sin nombre van a No_reconocidas/."
                )
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.DISABLED)
        else:
            self._split_button.configure(text="Separar nóminas")
            self._names_hint.configure(
                text="Ejemplo: Nominas_Julio_2026 → Nominas_Julio_2026_001.pdf"
            )
            if not self._is_processing:
                self._base_name_entry.configure(state=tk.NORMAL)

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

    def _set_widget_tree_state(self, widget: tk.Misc, state: str) -> None:
        """Aplica estado a botones de forma recursiva (excepto progreso)."""
        if isinstance(widget, (ttk.Button, ttk.Radiobutton)):
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._set_widget_tree_state(child, state)

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

        try:
            path = validate_pdf_path(selected)
            page_count = get_pdf_page_count(path)
        except SeparadorNominasError as exc:
            self._show_error(exc.user_message)
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Error inesperado al seleccionar PDF: %s",
                type(exc).__name__,
            )
            self._show_error(
                "No se ha podido abrir el PDF seleccionado.\n"
                "Comprueba que el archivo no esté dañado ni protegido con contraseña."
            )
            return

        self._pdf_path.set(str(path))
        self._page_count = page_count
        self._base_name.set(suggest_base_name_from_pdf(path))
        self._destination_path.set(str(suggest_output_directory(path)))
        self._status_text.set(
            f"PDF seleccionado: {page_count} página{'s' if page_count != 1 else ''}."
        )
        self._result_text.set("")
        self._progress_value.set(PROGRESS_IDLE)
        self._open_folder_button.configure(state=tk.DISABLED)
        self._last_destination = None

    def _on_select_folder(self) -> None:
        """Abre el diálogo de selección de carpeta."""
        if self._is_processing:
            return

        selected = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not selected:
            return

        self._destination_path.set(selected)

    def _on_start(self) -> None:
        """Inicia el proceso según el modo seleccionado."""
        if self._is_processing:
            return

        if self._process_mode.get() == PROCESS_MODE_GROUP:
            self._start_group_process()
        else:
            self._start_split_process()

    def _start_split_process(self) -> None:
        """Inicia la separación página a página en un hilo de fondo."""
        pdf = self._pdf_path.get().strip()
        destination = self._destination_path.get().strip()
        base_name = self._base_name.get()

        self._is_processing = True
        self._set_controls_enabled(False)
        self._progress_value.set(PROGRESS_IDLE)
        self._result_text.set("")
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
        self._progress_value.set(PROGRESS_IDLE)
        self._result_text.set("")
        self._status_text.set(STATUS_READY)
        logger.info("Inicio del análisis de reconocimiento")

        worker = threading.Thread(
            target=self._run_analyze,
            args=(pdf, destination),
            daemon=True,
        )
        worker.start()

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
        """Muestra el resumen y pide confirmación antes de guardar."""
        summary = format_grouping_summary(analysis)
        self._progress_value.set(PROGRESS_COMPLETE)
        self._status_text.set(STATUS_WAITING_CONFIRMATION)
        self._result_text.set(summary)

        confirmed = messagebox.askyesno(
            APP_NAME,
            "Se ha completado el análisis.\n\n"
            f"Trabajadores reconocidos: {len(analysis.groups)}\n"
            f"Páginas no reconocidas: {len(analysis.unrecognized_page_numbers)}\n\n"
            "¿Generar los archivos PDF en la carpeta de destino?",
        )
        if not confirmed:
            self._is_processing = False
            self._status_text.set(STATUS_CANCELLED_BY_USER)
            self._set_controls_enabled(True)
            logger.info("Escritura cancelada por el usuario")
            return

        self._status_text.set(STATUS_WRITING_GROUPS)
        self._progress_value.set(PROGRESS_IDLE)
        self._result_text.set("Generando archivos PDF...")
        self.root.update_idletasks()
        worker = threading.Thread(
            target=self._run_write_groups,
            args=(analysis, destination),
            daemon=True,
        )
        worker.start()

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
        self._result_text.set(
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
        self._result_text.set("\n".join(summary_lines))
        self._set_controls_enabled(True)
        self._open_folder_button.configure(state=tk.NORMAL)
        messagebox.showinfo(
            APP_NAME,
            "Proceso completado correctamente.\n\n"
            f"Trabajadores: {result.recognized_worker_count}\n"
            f"No reconocidas: {len(result.unrecognized_files)}",
        )

    def _on_process_error(self, message: str) -> None:
        """Maneja un error durante el proceso."""
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
    root.mainloop()
