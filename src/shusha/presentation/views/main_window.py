"""
Main Application Window Shell for Shusha 2.
Coordinates menu, toolbar, sidebar navigation, download table, and status bar.
"""

import contextlib
import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ttkbootstrap as tb

from shusha.application.use_cases.download_use_cases import AddDownloadRequest
from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId
from shusha.domain.statistics import GlobalStatistics
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.download_table import DownloadTable
from shusha.presentation.components.sidebar import AppSidebar
from shusha.presentation.components.status_bar import AppStatusBar
from shusha.presentation.components.toolbar import AppToolbar
from shusha.presentation.dispatcher import UiDispatcher


class MainWindow(tb.Window):
    """Primary application window shell."""

    def __init__(self, ctx: AppContext) -> None:
        # Load theme preference
        settings = ctx.settings_store.load_settings()
        super().__init__(
            title="Shusha 2 — Download Manager",
            themename=settings.theme or "darkly",
            size=(1024, 640),
            minsize=(800, 500),
        )

        self.ctx = ctx
        self.dispatcher = UiDispatcher(self)

        self._all_downloads: list[Download] = []
        self._filter_type: str = "state"
        self._filter_value: str | None = None

        self._setup_menu()
        self._setup_layout()
        self._bind_sync_events()
        self._initial_load()

    def _setup_menu(self) -> None:
        menubar = tk.Menu(self)

        # File Menu
        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(
            label="Add URL...", accelerator="Ctrl+N", command=self._on_add_url_clicked
        )
        menu_file.add_command(
            label="Add Torrent...",
            accelerator="Ctrl+O",
            command=self._on_add_torrent_clicked,
        )
        menu_file.add_separator()
        menu_file.add_command(label="Exit", accelerator="Ctrl+Q", command=self.quit)
        menubar.add_cascade(label="File", menu=menu_file)

        # Download Menu
        menu_dl = tk.Menu(menubar, tearoff=0)
        menu_dl.add_command(label="Resume", command=self._on_resume_clicked)
        menu_dl.add_command(label="Pause", command=self._on_pause_clicked)
        menu_dl.add_separator()
        menu_dl.add_command(
            label="Remove", accelerator="Delete", command=self._on_remove_clicked
        )
        menubar.add_cascade(label="Download", menu=menu_dl)

        # Help Menu
        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="About Shusha", command=self._show_about)
        menubar.add_cascade(label="Help", menu=menu_help)

        self.config(menu=menubar)

        # Shortcuts
        self.bind("<Control-n>", lambda _: self._on_add_url_clicked())
        self.bind("<Control-o>", lambda _: self._on_add_torrent_clicked())
        self.bind("<Control-q>", lambda _: self.quit())
        self.bind("<Delete>", lambda _: self._on_remove_clicked())

    def _setup_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Toolbar
        self.toolbar = AppToolbar(
            self,
            on_add_url=self._on_add_url_clicked,
            on_add_torrent=self._on_add_torrent_clicked,
            on_resume=self._on_resume_clicked,
            on_pause=self._on_pause_clicked,
            on_remove=self._on_remove_clicked,
            on_settings=self._on_settings_clicked,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=2)

        # 2. Main Paned Content
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)

        # Sidebar
        self.sidebar = AppSidebar(paned, on_filter_selected=self._on_filter_changed)
        paned.add(self.sidebar, weight=1)

        # Download Table
        self.table = DownloadTable(
            paned,
            on_inspect=self._on_inspect_download,
            on_pause=self._handle_pause_batch,
            on_resume=self._handle_resume_batch,
            on_remove=self._handle_remove_batch,
        )
        paned.add(self.table, weight=4)

        # 3. Status Bar
        self.status_bar = AppStatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _bind_sync_events(self) -> None:
        """Subscribe to background synchronization events."""
        self.ctx.sync_coordinator.subscribe_downloads(
            lambda downloads: self.dispatcher.dispatch(
                lambda: self._on_downloads_updated(downloads)
            )
        )
        self.ctx.sync_coordinator.subscribe_stats(
            lambda stats: self.dispatcher.dispatch(
                lambda: self._on_stats_updated(stats)
            )
        )

    def _initial_load(self) -> None:
        """Load cached database state and check daemon health."""
        categories = self.ctx.category_repo.list_all()
        self.sidebar.update_categories(categories)

        cached_downloads = self.ctx.download_repo.list_all()
        self._on_downloads_updated(cached_downloads)

        # Probe daemon health in background
        def check_daemon() -> None:
            health = self.ctx.daemon_supervisor.get_health()
            self.dispatcher.dispatch(
                lambda: self.status_bar.update_daemon_status(
                    health.status.value == "HEALTHY",
                    version=health.version,
                )
            )

        self.dispatcher.run_in_background(check_daemon)

    def _on_filter_changed(self, filter_type: str, filter_value: str | None) -> None:
        self._filter_type = filter_type
        self._filter_value = filter_value
        self._apply_active_filter()

    def _apply_active_filter(self) -> None:
        """Filter the displayed downloads in the table."""
        if self._filter_type == "category" and self._filter_value:
            filtered = [
                dl
                for dl in self._all_downloads
                if str(dl.category_id or "") == self._filter_value
            ]
        elif self._filter_type == "state" and self._filter_value:
            filtered = [
                dl
                for dl in self._all_downloads
                if dl.state.value.lower() == self._filter_value.lower()
            ]
        else:
            filtered = list(self._all_downloads)

        self.table.update_rows(filtered)

    def _on_downloads_updated(self, downloads: list[Download]) -> None:
        self._all_downloads = downloads
        self._apply_active_filter()

    def _on_stats_updated(self, stats: GlobalStatistics) -> None:
        self.status_bar.update_statistics(stats)

    # User Actions
    def _on_add_url_clicked(self) -> None:
        # Prompt for download URL
        dialog = tb.dialogs.Querybox.get_string(
            title="Add URL",
            prompt="Enter HTTP/HTTPS/FTP/SFTP/Magnet URL:",
            parent=self,
        )
        if dialog and dialog.strip():
            url = dialog.strip()

            def perform_add() -> None:
                self.ctx.add_download_uc.execute(AddDownloadRequest(uris=[url]))

            self.dispatcher.run_in_background(perform_add)

    def _on_add_torrent_clicked(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select Torrent File",
            filetypes=[("Torrent Files", "*.torrent"), ("All Files", "*.*")],
            parent=self,
        )
        if filepath:
            torrent_path = Path(filepath)
            if torrent_path.exists():
                content = torrent_path.read_bytes()

                def perform_add() -> None:
                    self.ctx.add_download_uc.execute(
                        AddDownloadRequest(torrent_bytes=content)
                    )

                self.dispatcher.run_in_background(perform_add)

    def _on_resume_clicked(self) -> None:
        selected = self.table.get_selected_ids()
        if selected:
            self._handle_resume_batch(selected)

    def _on_pause_clicked(self) -> None:
        selected = self.table.get_selected_ids()
        if selected:
            self._handle_pause_batch(selected)

    def _on_remove_clicked(self) -> None:
        selected = self.table.get_selected_ids()
        if selected:
            self._handle_remove_batch(selected)

    def _handle_pause_batch(self, download_ids: Sequence[DownloadId]) -> None:
        def perform_pause() -> None:
            for dl_id in download_ids:
                with contextlib.suppress(Exception):
                    self.ctx.pause_download_uc.execute(dl_id)

        self.dispatcher.run_in_background(perform_pause)

    def _handle_resume_batch(self, download_ids: Sequence[DownloadId]) -> None:
        def perform_resume() -> None:
            for dl_id in download_ids:
                with contextlib.suppress(Exception):
                    self.ctx.resume_download_uc.execute(dl_id)

        self.dispatcher.run_in_background(perform_resume)

    def _handle_remove_batch(self, download_ids: Sequence[DownloadId]) -> None:
        confirm = messagebox.askyesno(
            "Confirm Remove",
            f"Are you sure you want to remove {len(download_ids)} download(s)?",
            parent=self,
        )
        if confirm:

            def perform_remove() -> None:
                for dl_id in download_ids:
                    with contextlib.suppress(Exception):
                        self.ctx.remove_download_uc.execute(dl_id, delete_files=False)

            self.dispatcher.run_in_background(perform_remove)

    def _on_inspect_download(self, download_id: DownloadId) -> None:
        pass  # In Epic 8, we attach the full Inspector dialog

    def _on_settings_clicked(self) -> None:
        pass  # In Epic 8, we attach the full Settings dialog

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Shusha",
            "Shusha 2 — High Performance Desktop Download Manager\nBuilt with Python 3.14, ttkbootstrap & aria2c.",
            parent=self,
        )
