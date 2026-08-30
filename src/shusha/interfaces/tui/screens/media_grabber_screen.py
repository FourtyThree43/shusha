"""Interactive Media Grabber Screen for Textual TUI."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Static

from shusha.application.command_bus import CommandBus
from shusha.application.commands import CreateJobCommand
from shusha.backends.ytdlp.inspector import MediaInspector
from shusha.backends.ytdlp.media import MediaMetadata
from shusha.domain.identifiers import make_backend_id


class MediaGrabberView(Static):
    """Inspects streaming media URLs, displays formats, and initiates downloads."""

    def __init__(self, command_bus: CommandBus | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.command_bus = command_bus
        self._inspector = MediaInspector()
        self._current_media: MediaMetadata | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="header-bar"):
                yield Label(
                    "🎬 Media Grabber — Stream Inspector (yt-dlp)",
                    classes="title-label",
                )

            with Horizontal(classes="search-bar"):
                yield Input(
                    placeholder="Paste video/stream URL (YouTube, Vimeo, Twitch, SoundCloud)...",
                    id="input_media_url",
                )
                yield Button("Inspect", variant="primary", id="btn_inspect")

            yield Label("Available Formats & Quality Options:", classes="section-label")
            yield DataTable(id="formats_table", cursor_type="row", zebra_stripes=True)

            with Horizontal(classes="action-bar"):
                yield Label("Ready.", id="lbl_status")
                yield Button(
                    "Download Selected Format (D)", variant="success", id="btn_download"
                )

    def on_mount(self) -> None:
        table = self.query_one("#formats_table", DataTable)
        table.add_columns(
            "Format ID", "Ext", "Resolution", "FPS", "Codecs (V/A)", "Filesize"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_inspect":
            self._on_inspect()
        elif event.button.id == "btn_download":
            self._on_download()

    def _on_inspect(self) -> None:
        url = self.query_one("#input_media_url", Input).value.strip()
        status_lbl = self.query_one("#lbl_status", Label)
        if not url:
            status_lbl.update("Please enter a media URL.")
            return

        status_lbl.update("Inspecting stream metadata...")
        table = self.query_one("#formats_table", DataTable)
        table.clear()

        try:
            self._current_media = self._inspector.inspect(url)
            for fmt in self._current_media.formats:
                codecs = f"{fmt.vcodec or 'none'} / {fmt.acodec or 'none'}"
                size_str = fmt.filesize.human_readable() if fmt.filesize else "unknown"
                table.add_row(
                    fmt.format_id,
                    fmt.ext,
                    fmt.resolution or "audio only",
                    str(fmt.fps or "-"),
                    codecs,
                    size_str,
                    key=fmt.format_id,
                )
            status_lbl.update(
                f"Loaded: {self._current_media.title} ({len(self._current_media.formats)} formats)"
            )
        except Exception as e:
            status_lbl.update(f"Inspection error: {e}")

    def _on_download(self) -> None:
        status_lbl = self.query_one("#lbl_status", Label)
        if not self._current_media:
            status_lbl.update("No media loaded. Inspect a URL first.")
            return

        table = self.query_one("#formats_table", DataTable)
        format_id = "best"
        if table.cursor_row is not None and table.row_count > 0:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key and row_key.value:
                format_id = row_key.value

        if self.command_bus:
            cmd = CreateJobCommand(
                name=self._current_media.title,
                source_input=self._current_media.webpage_url
                or self.query_one("#input_media_url", Input).value.strip(),
                backend_id=make_backend_id("yt-dlp"),
                options={"format": format_id},
            )
            self.command_bus.dispatch(cmd)
            status_lbl.update(
                f"Enqueued '{self._current_media.title}' [format: {format_id}]"
            )
