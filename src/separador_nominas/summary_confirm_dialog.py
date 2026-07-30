"""Diálogo modal maximizado para confirmar un resumen de texto."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from separador_nominas.constants import APP_NAME
from separador_nominas.ui_geometry import maximize_toplevel


class SummaryConfirmDialog(tk.Toplevel):
    """Modal a pantalla maximizada con resumen + Generar / Cancelar."""

    def __init__(
        self,
        master: tk.Misc,
        summary: str,
        *,
        title: str | None = None,
        prompt: str = "¿Generar los archivos PDF ahora?",
        confirm_label: str = "Generar",
        cancel_label: str = "Cancelar",
    ) -> None:
        super().__init__(master)
        self.title(title or f"{APP_NAME} — Confirmar generación")
        self.transient(master.winfo_toplevel())
        self.resizable(True, True)
        self.minsize(720, 480)
        self._confirmed = False

        outer = ttk.Frame(self, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        text_frame = ttk.LabelFrame(outer, text="Resumen", padding=8)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self._text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=6,
            font=("Segoe UI", 10),
        )
        scroll = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self._text.yview
        )
        self._text.configure(yscrollcommand=scroll.set)
        self._text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self._text.insert("1.0", summary)
        self._text.configure(state=tk.DISABLED)

        ttk.Label(outer, text=prompt, font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=(12, 8)
        )

        buttons = ttk.Frame(outer)
        buttons.grid(row=2, column=0, sticky="e")
        ttk.Button(buttons, text=cancel_label, command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(8, 0)
        )
        ttk.Button(buttons, text=confirm_label, command=self._on_confirm).pack(
            side=tk.RIGHT
        )

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        maximize_toplevel(self)
        self.grab_set()
        self.focus_set()

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    def _on_confirm(self) -> None:
        self._confirmed = True
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        self._confirmed = False
        self.grab_release()
        self.destroy()


def ask_summary_confirm(
    master: tk.Misc,
    summary: str,
    *,
    title: str | None = None,
    prompt: str = "¿Generar los archivos PDF ahora?",
) -> bool:
    """Muestra el resumen maximizado y devuelve True si el usuario confirma."""
    dialog = SummaryConfirmDialog(
        master, summary, title=title, prompt=prompt
    )
    master.wait_window(dialog)
    return dialog.confirmed
