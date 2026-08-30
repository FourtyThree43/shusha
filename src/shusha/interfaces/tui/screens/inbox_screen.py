"""Interactive Acquisition Inbox Screen for Textual TUI."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from shusha.acquisition.inbox import AcquisitionInbox


class InboxView(Static):
    """View managing detected acquisition candidates with live actions."""

    def __init__(self, inbox: AcquisitionInbox | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.inbox = inbox

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="header-bar"):
                yield Label(
                    "📥 Acquisition Inbox (Clipboard / Browser / Drag & Drop)",
                    classes="title-label",
                )
                yield Button("Accept (A)", variant="success", id="btn_accept")
                yield Button("Ignore (I)", variant="warning", id="btn_ignore")
                yield Button("Refresh (R)", variant="default", id="btn_refresh")

            yield DataTable(id="inbox_table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#inbox_table", DataTable)
        table.add_columns(
            "ID", "Source", "Type", "Input / URL", "Recommended Backend", "Status"
        )
        self.refresh_items()

    def refresh_items(self) -> None:
        table = self.query_one("#inbox_table", DataTable)
        table.clear()
        if not self.inbox:
            return

        items = self.inbox.list_active()
        for item in items:
            table.add_row(
                str(item.id),
                item.source_kind.value,
                item.detected_kind.value,
                item.raw_input,
                str(item.preferred_backend or "auto"),
                item.status.value,
                key=str(item.id),
            )

    def accept_selected(self) -> None:
        table = self.query_one("#inbox_table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key and row_key.value and self.inbox:
                self.inbox.accept(row_key.value)
                self.refresh_items()

    def ignore_selected(self) -> None:
        table = self.query_one("#inbox_table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key and row_key.value and self.inbox:
                self.inbox.ignore(row_key.value)
                self.refresh_items()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_accept":
            self.accept_selected()
        elif event.button.id == "btn_ignore":
            self.ignore_selected()
        elif event.button.id == "btn_refresh":
            self.refresh_items()
