"""
Modern Virtualized Download Table Component for Shusha 2.
Supports sorting, multi-selection, live updating, and contextual actions.
"""

import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as tb

from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId
from shusha.presentation.components.base import BaseFrame


class DownloadTable(BaseFrame):
    """Data table for displaying active and historical downloads."""

    COLUMNS = ("name", "progress", "size", "speed", "eta", "state", "category")

    def __init__(
        self,
        parent: tk.Misc,
        on_inspect: Callable[[DownloadId], None] | None = None,
        on_pause: Callable[[list[DownloadId]], None] | None = None,
        on_resume: Callable[[list[DownloadId]], None] | None = None,
        on_remove: Callable[[list[DownloadId]], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.on_inspect = on_inspect
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_remove = on_remove

        self._downloads: dict[DownloadId, Download] = {}
        self._sort_col: str = "name"
        self._sort_reverse: bool = False

        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = tb.Treeview(
            self,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
            bootstyle="primary",
        )

        # Configure column headings & widths
        self.tree.heading("name", text="Name", command=lambda: self._sort_by("name"))
        self.tree.heading(
            "progress", text="Progress", command=lambda: self._sort_by("progress")
        )
        self.tree.heading("size", text="Size", command=lambda: self._sort_by("size"))
        self.tree.heading("speed", text="Speed", command=lambda: self._sort_by("speed"))
        self.tree.heading("eta", text="ETA", command=lambda: self._sort_by("eta"))
        self.tree.heading(
            "state", text="Status", command=lambda: self._sort_by("state")
        )
        self.tree.heading(
            "category", text="Category", command=lambda: self._sort_by("category")
        )

        self.tree.column("name", width=260, minwidth=150, stretch=True)
        self.tree.column("progress", width=90, minwidth=70, anchor="center")
        self.tree.column("size", width=110, minwidth=80, anchor="e")
        self.tree.column("speed", width=100, minwidth=80, anchor="e")
        self.tree.column("eta", width=80, minwidth=60, anchor="center")
        self.tree.column("state", width=90, minwidth=70, anchor="center")
        self.tree.column("category", width=90, minwidth=60, anchor="center")

        # Scrollbars
        v_scroll = tb.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = tb.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Double click to inspect
        self.tree.bind("<Double-1>", self._on_double_click)

    def _setup_context_menu(self) -> None:
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Inspect", command=self._trigger_inspect)
        self.menu.add_separator()
        self.menu.add_command(label="Resume", command=self._trigger_resume)
        self.menu.add_command(label="Pause", command=self._trigger_pause)
        self.menu.add_separator()
        self.menu.add_command(label="Remove", command=self._trigger_remove)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event: tk.Event[tk.Misc]) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.menu.tk_popup(event.x_root, event.y_root)

    def _sort_by(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False
        self.update_rows(list(self._downloads.values()))

    def _on_double_click(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.get_selected_ids()
        if selected and self.on_inspect:
            self.on_inspect(selected[0])

    def _trigger_inspect(self) -> None:
        selected = self.get_selected_ids()
        if selected and self.on_inspect:
            self.on_inspect(selected[0])

    def _trigger_pause(self) -> None:
        selected = self.get_selected_ids()
        if selected and self.on_pause:
            self.on_pause(selected)

    def _trigger_resume(self) -> None:
        selected = self.get_selected_ids()
        if selected and self.on_resume:
            self.on_resume(selected)

    def _trigger_remove(self) -> None:
        selected = self.get_selected_ids()
        if selected and self.on_remove:
            self.on_remove(selected)

    def get_selected_ids(self) -> list[DownloadId]:
        """Return list of DownloadId for selected rows."""
        return [DownloadId(item_id) for item_id in self.tree.selection()]

    def update_rows(self, downloads: list[Download]) -> None:
        """Incrementally update or insert rows into the Treeview."""
        self._downloads = {dl.download_id: dl for dl in downloads}

        # Sorting
        def sort_key(dl: Download) -> tuple[int, float, str]:
            match self._sort_col:
                case "name":
                    return (0, 0.0, dl.name.lower())
                case "progress":
                    return (1, float(dl.progress.value), "")
                case "size":
                    return (
                        2,
                        float(dl.total_length.bytes if dl.total_length else 0),
                        "",
                    )
                case "speed":
                    return (3, float(dl.download_speed.bytes_per_sec), "")
                case "eta":
                    return (4, float(dl.eta.seconds if dl.eta else 99999999), "")
                case "state":
                    return (5, 0.0, dl.state.value)
                case "category":
                    return (6, 0.0, str(dl.category_id or ""))
                case _:
                    return (0, 0.0, dl.name.lower())

        sorted_downloads = sorted(downloads, key=sort_key, reverse=self._sort_reverse)
        existing_ids = set(self.tree.get_children())
        updated_ids: set[str] = set()

        for dl in sorted_downloads:
            row_id = str(dl.download_id)
            updated_ids.add(row_id)

            size_str = (
                f"{dl.completed_length.human_readable()} / {dl.total_length.human_readable()}"
                if dl.total_length
                else dl.completed_length.human_readable()
            )
            speed_str = (
                dl.download_speed.human_readable()
                if dl.download_speed.bytes_per_sec > 0
                else "-"
            )
            eta_str = dl.eta.human_readable() if dl.eta else "-"
            cat_str = str(dl.category_id) if dl.category_id else "-"

            values = (
                dl.name,
                dl.progress.human_readable(),
                size_str,
                speed_str,
                eta_str,
                dl.state.value,
                cat_str,
            )

            if self.tree.exists(row_id):
                self.tree.item(row_id, values=values)
            else:
                self.tree.insert("", "end", iid=row_id, values=values)

        # Remove rows that no longer exist
        for old_id in existing_ids - updated_ids:
            self.tree.delete(old_id)
