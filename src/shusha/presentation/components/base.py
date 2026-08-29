"""
Base UI components, windows, and dialogs for Shusha 2 using ttkbootstrap.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

import ttkbootstrap as tb


class BaseFrame(ttk.Frame):
    """Base ttk frame with consistent padding and theme awareness."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        padding: int | tuple[int, int] | tuple[int, int, int, int] | str | None = None,
    ) -> None:
        if padding is not None:
            super().__init__(master, padding=padding)
        else:
            super().__init__(master)


class BaseDialog(tb.Toplevel):
    """
    Base modal dialog supporting:
    - Escape key binding to close
    - Enter key binding to submit
    - Centered window geometry
    - Explicit submit/cancel callbacks
    """

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        title: str,
        on_submit: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        min_width: int = 400,
        min_height: int = 250,
    ) -> None:
        super().__init__(title=title, master=parent)
        self.minsize(min_width, min_height)
        self.transient(parent)
        self.grab_set()

        self._on_submit = on_submit
        self._on_cancel = on_cancel

        self.bind("<Escape>", lambda _: self.cancel())
        self.bind("<Return>", lambda _: self.submit())

        # Center dialog relative to parent
        self.update_idletasks()
        try:
            p_x = parent.winfo_rootx()
            p_y = parent.winfo_rooty()
            p_w = parent.winfo_width()
            p_h = parent.winfo_height()
            pos_x = max(0, p_x + (p_w - min_width) // 2)
            pos_y = max(0, p_y + (p_h - min_height) // 2)
            self.geometry(f"+{pos_x}+{pos_y}")
        except Exception:
            pass

    def submit(self) -> None:
        if self._on_submit:
            self._on_submit()
        self.destroy()

    def cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self.destroy()
