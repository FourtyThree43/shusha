"""Interactive Add Download Modal Screen for Textual TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select


class AddDownloadModal(ModalScreen[dict[str, str] | None]):
    """Modal dialog for enqueuing new downloads in terminal TUI."""

    DEFAULT_CSS = """
    AddDownloadModal {
        align: center middle;
    }
    #dialog {
        padding: 1 2;
        width: 70;
        height: auto;
        border: thick $accent;
        background: $surface;
    }
    #title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .field-label {
        margin-top: 1;
        color: $text-muted;
    }
    #actions {
        margin-top: 1;
        align: right middle;
    }
    Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Add New Download", id="title")

            yield Label("Download URL / Magnet / File:", classes="field-label")
            yield Input(placeholder="https://... or magnet:?xt=...", id="input_url")

            with Grid(), Vertical():
                yield Label("Target Backend Engine:", classes="field-label")
                yield Select(
                    [
                        ("aria2 (Multi-source / Torrent)", "aria2"),
                        ("yt-dlp (Media Stream)", "yt-dlp"),
                        ("Auto-Detect", "auto"),
                    ],
                    value="auto",
                    id="select_backend",
                )

            with Horizontal(id="actions"):
                yield Button("Cancel", variant="default", id="btn_cancel")
                yield Button("Enqueue Download", variant="primary", id="btn_submit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_submit":
            url_input = self.query_one("#input_url", Input).value.strip()
            if not url_input:
                return
            backend_select = self.query_one("#select_backend", Select).value
            backend = str(backend_select) if backend_select else "auto"
            self.dismiss({"url": url_input, "backend": backend})
