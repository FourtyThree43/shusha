# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT

import contextlib
import os
import subprocess
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Any

import ttkbootstrap as ttk
from ttkbootstrap import TableRow, Tableview, ToastNotification, ToolTip

from shusha.controller.api import ShushaAPI as Api
from shusha.models.logger import LoggerService
from shusha.models.structs_downloads import Download
from shusha.models.structs_stats import Stats
from shusha.models.utilities import send_desktop_notification, user_log_dir
from shusha.views.add_win import AddWindow
from shusha.views.settings_win import SettingsWindow
from shusha.views.status_win import DownloadWindow
from shusha.views.torrent_win import TorrentFilesWindow

logger = LoggerService(__name__)
SCRIPT_PATH = Path(__file__).parent
ASSETS_PATH = SCRIPT_PATH / Path("../resources/assets/")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class Aria2Gui(ttk.Frame):
    """
    The main application window class.

    :param master: The parent widget.
    """

    def __init__(self, master):
        """
        Initializes the main application window and sets up various components and attributes.

        :param master: The parent widget.
        """
        super().__init__(master, padding=10)
        self.pack(fill=tk.BOTH, expand=tk.YES)

        self.api = Api()
        self.start_server()
        self.download_gid = None

        self.downloads_map: dict[str, Download] = {}
        self.stats_vars: dict[str, tk.StringVar] = {}
        self.active_category: str = "All"
        self.notified_completed: set[str] = set()
        self.notified_failed: set[str] = set()

        self.colors = ttk.Style().colors

        image_files = {
            "add-download": "icons8-add-64.png",
            "start-download": "icons8-circled-play-64.png",
            "pause-download": "icons8-pause-button-64.png",
            "refresh": "icons8-refresh-64.png",
            "move-up": "icons8-arrow-64.png",
            "move-down": "icons8-scroll-down-64.png",
            "remove-download": "icons8-remove-64.png",
            "logs": "icons8-log-64.png",
            "settings": "icons8-slider_2-64.png",
            "start-queue-": "icons8-circled-play-64.png",
            "pause-queue": "icons8-pause-button-64.png",
            "clear-queue": "icons8-clear-64.png",
            "queue-settings": "icons8-slider-64.png",
        }

        self.photoimages = []
        for key, val in image_files.items():
            _path = relative_to_assets(val)
            if _path.exists():
                with contextlib.suppress(Exception):
                    self.photoimages.append(ttk.PhotoImage(name=key, file=str(_path)))

        self.create_buttonbar()
        self.create_table_view()
        self.create_bottom_bar()
        self.create_context_menu()

        self.after(1000, self.get_stats)

    def create_buttonbar(self):
        """
        Create and configure the button bar with various action buttons and their respective tooltips.
        """
        self.buttonbar = ttk.Labelframe(self, text="Actions")
        self.buttonbar.pack(fill=tk.X, expand=tk.YES, anchor=tk.N)

        opts_row = ttk.Frame(self.buttonbar)
        opts_row.pack(fill=tk.X, expand=tk.YES)

        add_btn = ttk.Button(
            master=opts_row,
            text="Add",
            image="add-download",
            command=self.open_toplevel,
            width=8,
            bootstyle="outline-dark",
        )
        add_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(add_btn, text="Add new download", bootstyle="warning")

        start_btn = ttk.Button(
            master=opts_row,
            text="Start",
            image="start-download",
            command=self.start_selected_download,
            width=8,
            bootstyle="outline-dark",
        )
        start_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(start_btn, text="Resume selected download", bootstyle="warning")

        pause_btn = ttk.Button(
            master=opts_row,
            text="Pause",
            image="pause-download",
            command=self.pause_selected_download,
            width=8,
            bootstyle="outline-dark",
        )
        pause_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(pause_btn, text="Pause selected download", bootstyle="warning")

        refresh_btn = ttk.Button(
            master=opts_row,
            text="Refresh",
            image="refresh",
            command=self.refresh_downloads_table,
            width=8,
            bootstyle="outline-dark",
        )
        refresh_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(refresh_btn, text="Refresh downloads list", bootstyle="warning")

        mvup_btn = ttk.Button(
            master=opts_row,
            text="Move Up",
            image="move-up",
            command=self.move_download_up,
            width=8,
            bootstyle="outline-dark",
        )
        mvup_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(mvup_btn, text="Move download up", bootstyle="warning")

        mvdown_btn = ttk.Button(
            master=opts_row,
            text="Move Down",
            image="move-down",
            command=self.move_download_down,
            width=8,
            bootstyle="outline-dark",
        )
        mvdown_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(mvdown_btn, text="Move download down", bootstyle="warning")

        rem_btn = ttk.Button(
            master=opts_row,
            text="Remove",
            image="remove-download",
            command=self.remove_selected_download,
            width=8,
            bootstyle="outline-dark",
        )
        rem_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(rem_btn, text="Remove download", bootstyle="danger")

        sett_btn = ttk.Button(
            master=opts_row,
            text="Settings",
            image="settings",
            command=self.open_settings_window,
            width=8,
            bootstyle="outline-dark",
        )
        sett_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(sett_btn, text="Open settings", bootstyle="warning")

        logs_btn = ttk.Button(
            master=opts_row,
            text="Logs",
            image="logs",
            command=self.open_logs_directory,
            width=8,
            bootstyle="outline-dark",
        )
        logs_btn.pack(side=tk.RIGHT, padx=(0, 1), pady=1)
        ToolTip(logs_btn, text="Open logs folder", bootstyle="warning")

    def create_table_view(self):
        """
        Creates and populates a table view with the specified columns and row data.
        """
        self.table_lf = ttk.Labelframe(self, text="Downloads List")
        self.table_lf.pack(fill=tk.BOTH, expand=tk.YES, side=tk.TOP)

        _columns = [
            "Filename",
            "Status",
            "Size",
            "Progress",
            "Speed",
            "ETA",
            "GID",
        ]

        self.dt = Tableview(
            master=self.table_lf,
            coldata=_columns,
            rowdata=[],
            paginated=True,
            searchable=True,
            bootstyle="warning",
            stripecolor=(self.colors.dark, None),
        )
        self.dt.pack(fill=tk.BOTH, expand=tk.YES, padx=10)

        # Bind events
        if hasattr(self.dt, "view"):
            self.dt.view.bind("<Double-1>", self.on_double_click_row)
            self.dt.view.bind("<Button-3>", self.show_context_menu)
            self.dt.view.bind("<Button-2>", self.show_context_menu)

    def create_context_menu(self):
        """Create right-click context menu for download rows."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Resume / Start", command=self.start_selected_download
        )
        self.context_menu.add_command(
            label="Pause", command=self.pause_selected_download
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Remove (Keep Files)",
            command=lambda: self.remove_selected_download(files=False),
        )
        self.context_menu.add_command(
            label="Delete (With Files)",
            command=lambda: self.remove_selected_download(files=True),
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Open Containing Folder", command=self.open_selected_folder
        )
        self.context_menu.add_command(
            label="Copy Download Info", command=self.copy_selected_link
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Inspect Details", command=self.open_selected_details
        )
        self.context_menu.add_command(
            label="Select Files (Torrent)...", command=self.open_selective_files
        )

    def show_context_menu(self, event):
        """Display context menu on right-click."""
        with contextlib.suppress(Exception):
            row_id = self.dt.view.identify_row(event.y)
            if row_id:
                self.dt.view.selection_set(row_id)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_double_click_row(self, event=None):
        """Handle double click on table row to open detailed stats."""
        self.open_selected_details()

    def create_bottom_bar(self):
        """
        Create a bottom bar containing buttons, dropdowns, and leak-free stats.
        """
        self.bottom_bar = ttk.Labelframe(self, text="Queue Actions")
        self.bottom_bar.pack(fill=tk.X, expand=tk.YES, anchor=tk.S)

        opts_row = ttk.Frame(self.bottom_bar)
        opts_row.pack(fill=tk.X, expand=tk.YES)

        _categories = [
            "All",
            "Active",
            "Completed",
            "Paused",
            "Waiting",
            "Error",
            "Inactive",
        ]

        self.category_combo = ttk.Combobox(
            master=opts_row,
            values=_categories,
            width=12,
            state="readonly",
        )
        self.category_combo.set("All")
        self.category_combo.pack(side=tk.LEFT, padx=10, pady=1)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_changed)
        ToolTip(self.category_combo, text="Filter by category", bootstyle="warning")

        start_btn = ttk.Button(
            master=opts_row,
            text="Start",
            image="start-queue-",
            command=self.start_queue,
            width=8,
            bootstyle="outline-dark",
        )
        start_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(start_btn, text="Resume all downloads", bootstyle="warning")

        pause_btn = ttk.Button(
            master=opts_row,
            text="Pause",
            image="pause-queue",
            command=self.pause_queue,
            width=8,
            bootstyle="outline-dark",
        )
        pause_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(pause_btn, text="Pause all downloads", bootstyle="warning")

        clear_btn = ttk.Button(
            master=opts_row,
            text="Clear",
            image="clear-queue",
            command=self.clear_queue,
            width=8,
            bootstyle="outline-dark",
        )
        clear_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(clear_btn, text="Clear completed/stopped tasks", bootstyle="danger")

        sett_btn = ttk.Button(
            master=opts_row,
            text="Queue Settings",
            image="queue-settings",
            command=self.open_settings_window,
            width=8,
            bootstyle="outline-dark",
        )
        sett_btn.pack(side=tk.LEFT, padx=(1, 0), pady=1)
        ToolTip(sett_btn, text="Open settings dialog", bootstyle="warning")

        # Static label structure with StringVars to prevent memory leaks
        self.stats_frame = tk.Frame(opts_row)
        self.stats_frame.pack(side=tk.RIGHT, padx=10, pady=5)

        stat_keys = [
            "Download Speed",
            "Active",
            "Waiting",
            "Stopped",
            "Upload Speed",
        ]
        for col_idx, key in enumerate(stat_keys):
            self.stats_vars[key] = tk.StringVar(
                value="0 B/s" if "Speed" in key else "0"
            )
            tk.Label(
                self.stats_frame, text=f"{key}:", font=("TkDefaultFont", 8, "bold")
            ).grid(row=0, column=col_idx, sticky="w", padx=4)
            tk.Label(
                self.stats_frame,
                textvariable=self.stats_vars[key],
                font=("TkDefaultFont", 8),
            ).grid(row=1, column=col_idx, sticky="e", padx=4)

    def show_toast(self, message="This is a toast message"):
        """Show a toast notification with the given message."""
        try:
            toast = ToastNotification(
                title="Shusha Download Manager",
                message=message,
                duration=3000,
            )
            toast.show_toast()
        except Exception:
            pass

    def _thread(self, target: Callable, *args: Any) -> None:
        """Helper method to run the target function in a separate daemon thread."""
        threading.Thread(target=target, args=args, daemon=True).start()

    def stats_thread(self):
        """Perform statistics polling in background."""
        try:
            global_stats = self.api.get_stats()
            self.update_stats_frame(global_stats)
        except Exception as e:
            logger.log(f"Stats polling notice: {e}", level="debug")
        finally:
            self.after(1000, self.get_stats)

    def get_stats(self):
        """Trigger background statistics thread."""
        self._thread(self.stats_thread)

    def update_stats_frame(self, global_stats: Stats):
        """Update the stats labels via StringVar without recreating widgets."""
        if not global_stats:
            return
        stats_map = {
            "Download Speed": global_stats.download_speed_string(),
            "Active": str(global_stats.num_active),
            "Waiting": str(global_stats.num_waiting),
            "Stopped": str(global_stats.num_stopped),
            "Upload Speed": global_stats.upload_speed_string(),
        }
        for key, val in stats_map.items():
            if key in self.stats_vars:
                self.stats_vars[key].set(val)

    def open_toplevel(self):
        """Open the AddWindow modal dialog."""

        def handle_result(uris: list[tk.StringVar], options: dict):
            for uri in uris:
                self.download_thread(uri, options)

        AddWindow(callback=handle_result)

    def download_thread(self, uri, options: dict):
        """Start a download from URI or torrent file in a separate thread."""
        try:
            uri_str = str(uri.get()) if hasattr(uri, "get") else str(uri)
            uri_str = uri_str.strip()
            if not uri_str:
                return

            downloads: list[Download] = []
            if uri_str.lower().endswith(".torrent") and Path(uri_str).is_file():
                downloads = self.api.add_torrent(uri_str, options=options)
            elif uri_str.lower().endswith(".metalink") and Path(uri_str).is_file():
                downloads = self.api.add_metalink(uri_str, options=options)
            else:
                dl = self.api.add_uris([uri_str], options)
                if dl:
                    downloads = [dl]

            for download in downloads:
                if download:
                    msg = f"Added Download: {download.name or download.gid}"
                    self.show_toast(message=msg)
                    self.add_download_to_table(download)

            if downloads:
                self.refresh_downloads_table()

        except Exception as e:
            logger.log(f"Error starting download: {e}", level="error")

    def add_download_to_table(self, download: Download):
        """Add a download to the tableview."""
        if self.dt and download:
            if download.gid:
                self.downloads_map[str(download.gid)] = download
            data = self.get_download_row_data(download)
            _row = self.dt.insert_row(index="end", values=data)
            self.dt.load_table_data()

            if not download.is_complete and not download.has_failed:
                self.after(1000, self.update_rows_periodically, download, _row)

    def update_rows_periodically(self, download: Download, _row: TableRow):
        """Update single download row periodically."""
        if (
            not download
            or download.gid is None
            or download.is_complete
            or download.has_failed
        ):
            return

        try:
            download.update()
            new_data = self.get_download_row_data(download)
            _row.configure(iid=_row.iid, values=new_data)
            self.dt.load_table_data()
            self.after(1000, self.update_rows_periodically, download, _row)
        except Exception:
            pass

    def get_download_row_data(self, download: Download):
        """Extract table row data array from Download object."""
        return [
            download.name or "Unknown",
            download.status or "active",
            download.total_length_string(),
            download.progress_string(),
            download.download_speed_string(),
            download.eta_string(),
            str(download.gid or ""),
        ]

    def get_selected_download(self) -> Download | None:
        """Retrieve the currently selected Download object from tableview."""
        if not self.dt:
            return None
        selected_rows = self.dt.get_rows(selected=True)
        if not selected_rows:
            return None
        selected_row = selected_rows[0]
        row_values = selected_row.values
        if not row_values:
            return None

        # GID is stored in the last column
        gid = str(row_values[-1])
        if gid and gid in self.downloads_map:
            return self.downloads_map[gid]

        # Fallback to direct API lookup
        if gid:
            try:
                dl = self.api.get_download(gid)
                if dl:
                    self.downloads_map[gid] = dl
                    return dl
            except Exception:
                pass
        return None

    def start_selected_download(self):
        """Resume the currently selected download."""
        dl = self.get_selected_download()
        if dl and dl.gid:
            self._thread(self._start_download_bg, dl)
        else:
            self.show_toast("No download selected")

    def _start_download_bg(self, dl: Download):
        try:
            self.api.resume(dl.gid)
            self.show_toast(f"Resumed: {dl.name}")
            self.refresh_downloads_table()
        except Exception as e:
            logger.log(f"Error resuming download: {e}", level="error")

    def pause_selected_download(self):
        """Pause the currently selected download."""
        dl = self.get_selected_download()
        if dl and dl.gid:
            self._thread(self._pause_download_bg, dl)
        else:
            self.show_toast("No download selected")

    def _pause_download_bg(self, dl: Download):
        try:
            self.api.pause(dl.gid)
            self.show_toast(f"Paused: {dl.name}")
            self.refresh_downloads_table()
        except Exception as e:
            logger.log(f"Error pausing download: {e}", level="error")

    def remove_selected_download(self, files: bool = False):
        """Remove the selected download from table and aria2."""
        dl = self.get_selected_download()
        if dl and dl.gid:
            self._thread(self._remove_download_bg, dl, files)
        else:
            self.show_toast("No download selected")

    def _remove_download_bg(self, dl: Download, files: bool):
        try:
            self.api.remove(dl.gid, files=files)
            self.show_toast(f"Removed: {dl.name}")
            self.refresh_downloads_table()
        except Exception as e:
            logger.log(f"Error removing download: {e}", level="error")

    def move_download_up(self):
        """Increase queue priority of selected download."""
        dl = self.get_selected_download()
        if dl and dl.gid:
            try:
                self.api.client.change_position(dl.gid, -1, "POS_CUR")
                self.refresh_downloads_table()
            except Exception as e:
                logger.log(f"Error reordering download: {e}", level="error")

    def move_download_down(self):
        """Decrease queue priority of selected download."""
        dl = self.get_selected_download()
        if dl and dl.gid:
            try:
                self.api.client.change_position(dl.gid, 1, "POS_CUR")
                self.refresh_downloads_table()
            except Exception as e:
                logger.log(f"Error reordering download: {e}", level="error")

    def refresh_downloads_table(self):
        """Query aria2 downloads and synchronize tableview rows."""
        self._thread(self._refresh_downloads_bg)

    def _refresh_downloads_bg(self):
        try:
            downloads = self.api.get_downloads()
            self.downloads_map = {str(d.gid): d for d in downloads if d.gid}

            # Check for newly completed or failed downloads and dispatch notifications
            for d in downloads:
                if d.gid:
                    gid_str = str(d.gid)
                    if d.is_complete and gid_str not in self.notified_completed:
                        self.notified_completed.add(gid_str)
                        name = d.name or gid_str
                        send_desktop_notification(
                            "Download Complete", f"{name} has finished downloading."
                        )
                    elif d.has_failed and gid_str not in self.notified_failed:
                        self.notified_failed.add(gid_str)
                        name = d.name or gid_str
                        send_desktop_notification(
                            "Download Failed", f"{name} encountered a download error."
                        )

            def matches(d: Download, category: str) -> bool:
                cat = category.lower()
                if cat == "all":
                    return True
                if cat == "active":
                    return bool(d.is_active)
                if cat == "completed":
                    return bool(d.is_complete)
                if cat == "paused":
                    return bool(d.is_paused)
                if cat == "waiting":
                    return bool(d.is_waiting)
                if cat == "error":
                    return bool(d.has_failed)
                if cat == "inactive":
                    return bool(d.is_paused or d.is_complete or d.has_failed)
                return True

            filtered = [d for d in downloads if matches(d, self.active_category)]
            row_data = [self.get_download_row_data(d) for d in filtered]

            def _update_ui():
                if self.dt:
                    self.dt.purge_table_data()
                    for r in row_data:
                        self.dt.insert_row("end", r)
                    self.dt.load_table_data()

            self.after(0, _update_ui)
        except Exception as e:
            logger.log(f"Refresh downloads notice: {e}", level="debug")

    def minimize_to_tray(self):
        """Minimize main application window to tray/background."""
        withdraw_fn = getattr(self.master, "withdraw", None)
        if callable(withdraw_fn):
            withdraw_fn()
            self.show_toast("Shusha minimized to background")

    def restore_from_tray(self):
        """Restore main application window from background."""
        deiconify_fn = getattr(self.master, "deiconify", None)
        if callable(deiconify_fn):
            deiconify_fn()
            lift_fn = getattr(self.master, "lift", None)
            if callable(lift_fn):
                lift_fn()

    def on_category_changed(self, event=None):
        """Handle category filter combobox selection."""
        self.active_category = self.category_combo.get()
        self.refresh_downloads_table()

    def open_selected_folder(self):
        """Open the folder containing the selected download."""
        dl = self.get_selected_download()
        if not dl or not dl.dir:
            self.show_toast("No download location available")
            return

        folder_path = str(dl.dir)
        try:
            startfile = getattr(os, "startfile", None)
            if startfile:
                startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            logger.log(f"Failed to open folder {folder_path}: {e}", level="error")

    def copy_selected_link(self):
        """Copy selected download filename or GID to clipboard."""
        dl = self.get_selected_download()
        if dl:
            info = dl.name or str(dl.gid)
            self.clipboard_clear()
            self.clipboard_append(info)
            self.show_toast(f"Copied: {info}")

    def open_selected_details(self):
        """Open detailed live status meter dialog for selected download."""
        dl = self.get_selected_download()
        if dl:
            dw = DownloadWindow(api=self.api)
            dw.update_stats_frame(dl)
        else:
            DownloadWindow(api=self.api)

    def open_selective_files(self):
        """Open torrent files inspection and selective download window."""
        dl = self.get_selected_download()
        if dl:
            TorrentFilesWindow(
                master=self,
                api=self.api,
                download=dl,
                on_applied=self.refresh_downloads_table,
            )
        else:
            self.show_toast("No download selected")

    def open_settings_window(self):
        """Open the graphical SettingsWindow dialog."""
        SettingsWindow(master=self, api=self.api, on_saved=self.refresh_downloads_table)

    def open_logs_directory(self):
        """Open application logs directory."""
        log_dir = str(user_log_dir("shusha"))
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            startfile = getattr(os, "startfile", None)
            if startfile:
                startfile(log_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", log_dir])
            else:
                subprocess.Popen(["xdg-open", log_dir])
        except Exception as e:
            self.show_toast(f"Logs directory: {log_dir}")
            logger.log(f"Logs folder: {e}", level="info")

    def start_queue(self):
        """Resume all paused/waiting downloads in the queue."""

        def _bg():
            try:
                self.api.resume_all()
                self.show_toast("Resumed all downloads")
                self.refresh_downloads_table()
            except Exception as e:
                logger.log(f"Error resuming queue: {e}", level="error")

        self._thread(_bg)

    def pause_queue(self):
        """Pause all active downloads in the queue."""

        def _bg():
            try:
                self.api.pause_all()
                self.show_toast("Paused all downloads")
                self.refresh_downloads_table()
            except Exception as e:
                logger.log(f"Error pausing queue: {e}", level="error")

        self._thread(_bg)

    def clear_queue(self):
        """Clear all completed and stopped downloads."""

        def _bg():
            try:
                self.api.purge()
                self.show_toast("Cleared completed / stopped tasks")
                self.refresh_downloads_table()
            except Exception as e:
                logger.log(f"Error clearing queue: {e}", level="error")

        self._thread(_bg)

    def pause_download(self):
        """Method to pause a download."""
        if self.download_gid:
            logger.log("Stopping download...")
            self._thread(self.api.pause, self.download_gid)

    def stop_downloads(self):
        """Method to stop all downloads."""
        logger.log("Stopping downloads...")
        self._thread(self.api.pause_all)

    def start_server(self):
        """Method to start the Aria2 server."""
        self._thread(self.api.start_server)

    def stop_server(self):
        """Method to stop the Aria2 server."""
        self._thread(self.api.stop_server)

    def cleanup(self):
        """Method to perform cleanup operations."""
        logger.log("Performing cleanup...")
        if self.download_gid:
            self.stop_downloads()
        self.stop_server()


if __name__ == "__main__":

    def on_close():
        my_app_instance.cleanup()
        app.destroy()

    app = ttk.Window(
        title="App",
        themename="darkly",
        size=(1270, 550),
        resizable=(False, False),
        position=(10, 140),
    )

    my_app_instance = Aria2Gui(app)
    app.wm_protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()
