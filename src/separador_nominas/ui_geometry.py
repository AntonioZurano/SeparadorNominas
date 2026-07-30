"""Utilidades de geometría de ventanas Tkinter (sin lógica de negocio)."""

from __future__ import annotations

import tkinter as tk


def maximize_toplevel(window: tk.Misc) -> None:
    """
    Maximiza una ventana (Tk o Toplevel).

    Usa el estado «zoomed» del gestor de ventanas; no fullscreen sin bordes.
    """
    window.update_idletasks()
    try:
        window.state("zoomed")  # type: ignore[attr-defined]
        return
    except tk.TclError:
        pass
    try:
        window.attributes("-zoomed", True)  # type: ignore[attr-defined]
        return
    except tk.TclError:
        pass
    width = window.winfo_screenwidth()
    height = window.winfo_screenheight()
    window.geometry(f"{width}x{height}+0+0")  # type: ignore[attr-defined]
