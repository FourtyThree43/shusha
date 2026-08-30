"""Main Application Window Shell for Shusha 2.

Coordinates modern navigation rail, toolbar, multi-view content stack
(Dashboard, Downloads, Acquisition Inbox, Doctor & Diagnostics), and status bar.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Sequence
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId
from shusha.domain.statistics import GlobalStatistics
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.download_table import DownloadTable
from shusha.presentation.components.sidebar import AppSidebar
from shusha.presentation.components.status_bar import AppStatusBar
from shusha.presentation.components.toolbar import AppToolbar
from shusha.presentation.dispatcher import UiDispatcher
from shusha.presentation.theme import ResponsiveLayoutEngine
from shusha.presentation.views.add_download_dialog import AddDownloadDialog
from shusha.presentation.views.batch_add_dialog import BatchAddDialog
from shusha.presentation.views.create_torrent_dialog import CreateTorrentDialog
from shusha.presentation.views.dashboard_view import DashboardView
from shusha.presentation.views.doctor_view import DoctorView
from shusha.presentation.views.inbox_view import AcquisitionInboxView
from shusha.presentation.views.inspector_dialog import InspectorDialog
from shusha.presentation.views.media_grabber_dialog import MediaGrabberDialog
from shusha.presentation.views.plugins_dialog import PluginsDialog
from shusha.presentation.views.settings_dialog import SettingsDialog


class MainWindow(tb.Window):
    """Primary application window shell."""

    def __init__(self, ctx: AppContext) -> None:
        settings = ctx.settings_store.load_settings()
        self._current_theme = settings.theme or "darkly"
        super().__init__(
            title="Shusha 2 — Download Acquisition & Orchestration Platform",
            themename=self._current_theme,
            size=(1100, 680),
            minsize=(800, 500),
        )

        self.ctx = ctx
        self.dispatcher = UiDispatcher(self)

        self._all_downloads: list[Download] = []
        self._filter_type: str = "state"
        self._filter_value: str | None = None
        self._active_view_name: str = "transfers"

        self._setup_menu()
        self._setup_layout()
        self._bind_sync_events()
        self._initial_load()

        self.bind("<Configure>", self._on_window_resize)

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
        menu_file.add_command(
            label="Batch Add URLs...",
            accelerator="Ctrl+B",
            command=self._on_batch_add_clicked,
        )
        menu_file.add_separator()
        menu_file.add_command(
            label="Media Grabber...",
            accelerator="Ctrl+M",
            command=self._on_media_grabber_clicked,
        )
        menu_file.add_command(
            label="Acquisition Inbox...",
            accelerator="Ctrl+I",
            command=self._on_inbox_clicked,
        )
        menu_file.add_separator()
        menu_file.add_command(
            label="Create Torrent...",
            command=self._on_create_torrent_clicked,
        )
        menu_file.add_separator()
        menu_file.add_command(
            label="Settings...",
            accelerator="Ctrl+,",
            command=self._on_settings_clicked,
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

        # View Menu
        menu_view = tk.Menu(menubar, tearoff=0)
        menu_view.add_command(
            label="Dashboard", command=lambda: self._switch_view("dashboard")
        )
        menu_view.add_command(
            label="Downloads Workspace", command=lambda: self._switch_view("transfers")
        )
        menu_view.add_command(
            label="Acquisition Inbox", command=lambda: self._switch_view("inbox")
        )
        menu_view.add_command(
            label="Doctor & Diagnostics", command=lambda: self._switch_view("doctor")
        )
        menu_view.add_separator()
        menu_view.add_command(
            label="Plugins Manager...", command=self._on_plugins_clicked
        )
        menubar.add_cascade(label="View", menu=menu_view)

        # Help Menu
        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(
            label="Doctor & Diagnostics", command=lambda: self._switch_view("doctor")
        )
        menu_help.add_separator()
        menu_help.add_command(label="About Shusha", command=self._show_about)
        menubar.add_cascade(label="Help", menu=menu_help)

        self.config(menu=menubar)

        # Shortcuts
        self.bind("<Control-n>", lambda _: self._on_add_url_clicked())
        self.bind("<Control-o>", lambda _: self._on_add_torrent_clicked())
        self.bind("<Control-b>", lambda _: self._on_batch_add_clicked())
        self.bind("<Control-m>", lambda _: self._on_media_grabber_clicked())
        self.bind("<Control-i>", lambda _: self._on_inbox_clicked())
        self.bind("<Control-comma>", lambda _: self._on_settings_clicked())
        self.bind("<Control-q>", lambda _: self.quit())
        self.bind("<Delete>", lambda _: self._on_remove_clicked())

    def _setup_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Action Toolbar
        self.toolbar = AppToolbar(
            self,
            on_add_url=self._on_add_url_clicked,
            on_add_torrent=self._on_add_torrent_clicked,
            on_media_grabber=self._on_media_grabber_clicked,
            on_inbox=self._on_inbox_clicked,
            on_resume=self._on_resume_clicked,
            on_pause=self._on_pause_clicked,
            on_remove=self._on_remove_clicked,
            on_settings=self._on_settings_clicked,
            on_theme_toggle=self._on_theme_toggle,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=2)

        # 2. Main Paned Content (Sidebar + Content Switcher)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)

        # Navigation Rail Sidebar
        self.sidebar = AppSidebar(
            self.paned,
            on_nav_selected=self._switch_view,
            on_filter_selected=self._on_filter_changed,
        )
        self.paned.add(self.sidebar, weight=1)

        # Container Frame for Swappable Views
        self.view_container = ttk.Frame(self.paned)
        self.view_container.columnconfigure(0, weight=1)
        self.view_container.rowconfigure(0, weight=1)
        self.paned.add(self.view_container, weight=5)

        # Instantiate Views
        self.view_dashboard = DashboardView(self.view_container, self.ctx)
        self.view_transfers = DownloadTable(
            self.view_container,
            on_inspect=self._on_inspect_download,
            on_pause=self._handle_pause_batch,
            on_resume=self._handle_resume_batch,
            on_remove=self._handle_remove_batch,
        )
        self.view_inbox = AcquisitionInboxView(self.view_container, self.ctx)
        self.view_doctor = DoctorView(self.view_container, self.ctx)

        # Default View: Transfers Table
        self._switch_view("transfers")

        # 3. Status Bar
        self.status_bar = AppStatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _switch_view(self, view_name: str) -> None:
        """Switch the visible active view."""
        self._active_view_name = view_name
        # Hide all views
        for view in (
            self.view_dashboard,
            self.view_transfers,
            self.view_inbox,
            self.view_doctor,
        ):
            view.grid_forget()

        if view_name == "dashboard":
            self.view_dashboard.grid(row=0, column=0, sticky="nsew")
        elif view_name == "transfers":
            self.view_transfers.grid(row=0, column=0, sticky="nsew")
        elif view_name == "inbox":
            self.view_inbox.grid(row=0, column=0, sticky="nsew")
            self.view_inbox.refresh()
        elif view_name == "media":
            self.view_transfers.grid(row=0, column=0, sticky="nsew")
            self._on_media_grabber_clicked()
        elif view_name == "plugins":
            self.view_transfers.grid(row=0, column=0, sticky="nsew")
            self._on_plugins_clicked()
        elif view_name == "doctor":
            self.view_doctor.grid(row=0, column=0, sticky="nsew")
            self.view_doctor.run_checks()
        else:
            self.view_transfers.grid(row=0, column=0, sticky="nsew")

    def _on_window_resize(self, event: tk.Event[tk.Misc]) -> None:
        """Handle responsive breakpoint classification."""
        if event.widget == self:
            res_class = ResponsiveLayoutEngine.get_responsive_class(event.width)
            if res_class.value == "compact":
                self.title("Shusha 2")
            else:
                self.title("Shusha 2 — Download Acquisition & Orchestration Platform")

    def _on_theme_toggle(self) -> None:
        """Toggle between dark and light ttkbootstrap themes."""
        next_theme = (
            "cosmo"
            if self._current_theme in ("darkly", "cyborg", "superhero")
            else "darkly"
        )
        self._current_theme = next_theme
        self.style.theme_use(next_theme)

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
            filtered = self._all_downloads

        self.view_transfers.update_rows(filtered)

    def _on_downloads_updated(self, downloads: Sequence[Download]) -> None:
        self._all_downloads = list(downloads)
        self._apply_active_filter()

        # Update Dashboard metrics
        active = sum(1 for d in self._all_downloads if d.state.value == "ACTIVE")
        completed = sum(1 for d in self._all_downloads if d.state.value == "COMPLETE")
        self.view_dashboard.update_metrics(active, "0 B/s", "0 B/s", completed)

    def _on_stats_updated(self, stats: GlobalStatistics) -> None:
        self.status_bar.update_statistics(stats)
        active = stats.num_active
        down_str = stats.download_speed.human_readable()
        up_str = stats.upload_speed.human_readable()
        completed = sum(1 for d in self._all_downloads if d.state.value == "COMPLETE")
        self.view_dashboard.update_metrics(active, down_str, up_str, completed)

    # Action Handlers
    def _on_add_url_clicked(self) -> None:
        dlg = AddDownloadDialog(self, self.ctx)
        self.wait_window(dlg)

    def _on_add_torrent_clicked(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="Select BitTorrent or Metalink File",
            filetypes=[
                ("Torrents & Metalinks", "*.torrent *.metalink *.meta4"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            dlg = AddDownloadDialog(self, self.ctx, initial_url=f"file://{path}")
            self.wait_window(dlg)

    def _on_batch_add_clicked(self) -> None:
        dlg = BatchAddDialog(self, self.ctx)
        self.wait_window(dlg)

    def _on_media_grabber_clicked(self) -> None:
        dlg = MediaGrabberDialog(self, self.ctx)
        self.wait_window(dlg)

    def _on_inbox_clicked(self) -> None:
        self._switch_view("inbox")

    def _on_plugins_clicked(self) -> None:
        dlg = PluginsDialog(self, self.ctx)
        self.wait_window(dlg)

    def _on_create_torrent_clicked(self) -> None:
        dlg = CreateTorrentDialog(self)
        self.wait_window(dlg)

    def _on_settings_clicked(self) -> None:
        dlg = SettingsDialog(self, self.ctx)
        self.wait_window(dlg)

    def _on_inspect_download(self, download_id: DownloadId) -> None:
        dlg = InspectorDialog(self, self.ctx, download_id)
        self.wait_window(dlg)

    def _handle_pause_batch(self, ids: Sequence[DownloadId]) -> None:
        def worker() -> None:
            for gid in ids:
                with contextlib.suppress(Exception):
                    self.ctx.pause_download_uc.execute(gid)

        self.dispatcher.run_in_background(worker)

    def _handle_resume_batch(self, ids: Sequence[DownloadId]) -> None:
        def worker() -> None:
            for gid in ids:
                with contextlib.suppress(Exception):
                    self.ctx.resume_download_uc.execute(gid)

        self.dispatcher.run_in_background(worker)

    def _handle_remove_batch(self, ids: Sequence[DownloadId]) -> None:
        if not messagebox.askyesno(
            "Confirm Remove", f"Remove {len(ids)} download item(s)?"
        ):
            return

        def worker() -> None:
            for gid in ids:
                with contextlib.suppress(Exception):
                    self.ctx.remove_download_uc.execute(gid)

        self.dispatcher.run_in_background(worker)

    def _on_resume_clicked(self) -> None:
        selected = self.view_transfers.get_selected_ids()
        if selected:
            self._handle_resume_batch(selected)

    def _on_pause_clicked(self) -> None:
        selected = self.view_transfers.get_selected_ids()
        if selected:
            self._handle_pause_batch(selected)

    def _on_remove_clicked(self) -> None:
        selected = self.view_transfers.get_selected_ids()
        if selected:
            self._handle_remove_batch(selected)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Shusha 2",
            "Shusha 2 — Universal Download Acquisition & Orchestration Platform\n\n"
            "Built with Python 3.14, ttkbootstrap & Textual.\n"
            "Powered by aria2c & yt-dlp.\n\n"
            "License: MIT",
        )
