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
    PROGRESS_COMPLETE,
    PROGRESS_IDLE,
    STATUS_COMPLETED,
    STATUS_ERROR,
    STATUS_PROCESSING_TEMPLATE,
    STATUS_READY,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from separador_nominas.exceptions import SeparadorNominasError, UnexpectedError
from separador_nominas.filename_service import (
    suggest_base_name_from_pdf,
    suggest_output_directory,
)
from separador_nominas.pdf_service import SplitResult, split_pdf
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
        self._status_text = tk.StringVar(value=STATUS_READY)
        self._result_text = tk.StringVar(value="")
        self._progress_value = tk.DoubleVar(value=PROGRESS_IDLE)

        self._is_processing = False
        self._page_count: int | None = None
        self._last_destination: Path | None = None

        self._build_ui()
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

        # --- Configuración de nombres ---
        names_frame = ttk.LabelFrame(
            main, text="Configuración de nombres", padding=10
        )
        names_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        names_frame.columnconfigure(1, weight=1)

        ttk.Label(names_frame, text="Nombre base de los archivos").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self._base_name_entry = ttk.Entry(names_frame, textvariable=self._base_name)
        self._base_name_entry.grid(row=1, column=0, columnspan=3, sticky="ew")

        hint = ttk.Label(
            names_frame,
            text="Ejemplo: Nominas_Julio_2026 → Nominas_Julio_2026_001.pdf",
            foreground="#555555",
        )
        hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # --- Proceso ---
        process_frame = ttk.LabelFrame(main, text="Proceso", padding=10)
        process_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        process_frame.columnconfigure(0, weight=1)

        self._split_button = ttk.Button(
            process_frame,
            text="Separar nóminas",
            command=self._on_split,
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
        result_frame.grid(row=5, column=0, columnspan=3, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        ttk.Label(
            result_frame, textvariable=self._result_text, wraplength=580, justify="left"
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._open_folder_button = ttk.Button(
            result_frame,
            text="Abrir carpeta de destino",
            command=self._on_open_folder,
        )
        self._open_folder_button.grid(row=1, column=0, sticky="w")

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Activa o desactiva los controles durante el proceso."""
        state = tk.NORMAL if enabled else tk.DISABLED
        for child in self.root.winfo_children():
            self._set_widget_tree_state(child, state)
        # El campo de ruta debe permanecer de solo lectura.
        # Se reaplican estados específicos a continuación.
        self._split_button.configure(state=state)
        self._base_name_entry.configure(state=tk.NORMAL if enabled else tk.DISABLED)
        if enabled and self._last_destination is not None:
            self._open_folder_button.configure(state=tk.NORMAL)
        elif not enabled:
            self._open_folder_button.configure(state=tk.DISABLED)

    def _set_widget_tree_state(self, widget: tk.Misc, state: str) -> None:
        """Aplica estado a botones de forma recursiva (excepto progreso)."""
        if isinstance(widget, ttk.Button):
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

    def _on_split(self) -> None:
        """Inicia la separación en un hilo de fondo."""
        if self._is_processing:
            return

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
            self.root.after(0, lambda: self._on_split_error(message))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado: %s", type(exc).__name__)
            message = UnexpectedError(
                "Se ha producido un error inesperado.\n"
                "Inténtalo de nuevo o contacta con el administrador."
            ).user_message
            self.root.after(0, lambda: self._on_split_error(message))

    def _schedule_progress(
        self, current: int, total: int, _output_path: Path
    ) -> None:
        """Programa la actualización de progreso en el hilo principal."""
        self.root.after(0, lambda: self._update_progress(current, total))

    def _update_progress(self, current: int, total: int) -> None:
        """Actualiza barra y texto de estado."""
        percent = (current / total) * PROGRESS_COMPLETE if total else PROGRESS_IDLE
        self._progress_value.set(percent)
        self._status_text.set(
            STATUS_PROCESSING_TEMPLATE.format(current=current, total=total)
        )

    def _on_split_success(self, result: SplitResult) -> None:
        """Maneja la finalización correcta del proceso."""
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

    def _on_split_error(self, message: str) -> None:
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


def open_folder(path: Path) -> None:
    """Abre una carpeta con el explorador del sistema operativo."""
    resolved = path.resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(resolved))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(resolved)], check=False)
    else:
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
