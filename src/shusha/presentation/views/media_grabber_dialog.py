"""Media Grabber Inspection and Format Selection Dialog (E11-I08)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from shusha.application.commands import CreateJobCommand
from shusha.backends.ytdlp.inspector import MediaInspector
from shusha.backends.ytdlp.media import MediaMetadata
from shusha.domain.identifiers import make_backend_id
from shusha.presentation.app_context import AppContext
from shusha.presentation.theme import SpacingTokens


class MediaGrabberDialog(tk.Toplevel):
    """Inspects streaming media URLs, displays formats, and initiates downloads."""

    def __init__(
        self,
        parent: tk.Misc | None = None,
        context: AppContext | None = None,
        initial_url: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.context = context
        self.spacing = SpacingTokens()
        self.title("Media Grabber — Stream Inspector")
        self.geometry("700x520")
        if parent and isinstance(parent, tk.Wm):
            self.transient(parent)

        self._inspector = MediaInspector()
        self._current_media: MediaMetadata | None = None

        self._build_ui(initial_url)

    def _build_ui(self, initial_url: str) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # URL Input Bar
        input_frame = ttk.LabelFrame(self, text="Media URL", padding=self.spacing.sm)
        input_frame.grid(
            row=0, column=0, sticky="ew", padx=self.spacing.md, pady=self.spacing.sm
        )
        input_frame.columnconfigure(0, weight=1)

        self.url_var = tk.StringVar(value=initial_url)
        self.entry_url = ttk.Entry(input_frame, textvariable=self.url_var)
        self.entry_url.grid(row=0, column=0, sticky="ew", padx=(0, self.spacing.sm))

        self.btn_inspect = ttk.Button(
            input_frame, text="Inspect Media", command=self._on_inspect
        )
        self.btn_inspect.grid(row=0, column=1)

        # Formats Table
        table_frame = ttk.LabelFrame(
            self, text="Available Formats & Quality", padding=self.spacing.sm
        )
        table_frame.grid(
            row=1, column=0, sticky="nsew", padx=self.spacing.md, pady=self.spacing.sm
        )
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("format_id", "ext", "resolution", "fps", "codecs", "filesize")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("format_id", text="Format ID")
        self.tree.heading("ext", text="Ext")
        self.tree.heading("resolution", text="Resolution")
        self.tree.heading("fps", text="FPS")
        self.tree.heading("codecs", text="Codecs (V/A)")
        self.tree.heading("filesize", text="Estimated Size")

        self.tree.column("format_id", width=80, anchor="center")
        self.tree.column("ext", width=60, anchor="center")
        self.tree.column("resolution", width=100, anchor="center")
        self.tree.column("fps", width=60, anchor="center")
        self.tree.column("codecs", width=150, anchor="w")
        self.tree.column("filesize", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bottom Actions Bar
        actions_frame = ttk.Frame(self, padding=self.spacing.sm)
        actions_frame.grid(
            row=2, column=0, sticky="ew", padx=self.spacing.md, pady=self.spacing.sm
        )

        self.lbl_status = ttk.Label(actions_frame, text="Ready.")
        self.lbl_status.pack(side="left")

        self.btn_cancel = ttk.Button(actions_frame, text="Cancel", command=self.destroy)
        self.btn_cancel.pack(side="right", padx=(self.spacing.sm, 0))

        self.btn_download = ttk.Button(
            actions_frame, text="Download Selected Format", command=self._on_download
        )
        self.btn_download.pack(side="right")

    def _on_inspect(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(
                "Input Required", "Please enter a valid media stream URL."
            )
            return

        self.lbl_status.config(text="Inspecting stream metadata...")
        try:
            self._current_media = self._inspector.inspect(url)
            self._populate_formats(self._current_media)
            self.lbl_status.config(text=f"Loaded: {self._current_media.title}")
        except Exception as e:
            self.lbl_status.config(text="Inspection failed.")
            messagebox.showerror("Inspection Error", str(e))

    def _populate_formats(self, media: MediaMetadata) -> None:
        self.tree.delete(*self.tree.get_children())
        for fmt in media.formats:
            codecs = f"{fmt.vcodec or 'none'} / {fmt.acodec or 'none'}"
            size_str = fmt.filesize.human_readable() if fmt.filesize else "unknown"
            self.tree.insert(
                "",
                "end",
                iid=fmt.format_id,
                values=(
                    fmt.format_id,
                    fmt.ext,
                    fmt.resolution or "audio only",
                    str(fmt.fps or "-"),
                    codecs,
                    size_str,
                ),
            )

    def _on_download(self) -> None:
        if not self._current_media or not self.context:
            return
        selected = self.tree.selection()
        format_id = selected[0] if selected else "best"

        if self.context.command_bus:
            source_input = self._current_media.webpage_url or self.url_var.get()
            cmd = CreateJobCommand(
                name=self._current_media.title,
                source_input=source_input,
                backend_id=make_backend_id("yt-dlp"),
                options={"format": format_id},
            )
            self.context.command_bus.dispatch(cmd)
            messagebox.showinfo(
                "Job Created", f"Added '{self._current_media.title}' to download queue."
            )
            self.destroy()
