"""Comprehensive Graphical Settings Window for Shusha-DM.

Provides configuration tabs for:
- General: Download folders, themes, notifications, tray behavior.
- Downloads & Performance: Concurrency, connection splits, disk cache, speed throttles.
- Aria2 RPC: Daemon host, port, authentication secrets, session intervals.
- BitTorrent & Trackers: DHT, PEX, seed ratio, max peers, tracker aggregation.
- Bandwidth Scheduler: Automated time-window speed throttling.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from tkinter import filedialog
from typing import Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService
from shusha.models.scheduler import ScheduleRule
from shusha.models.settings import AppSettings
from shusha.models.tracker_service import TrackerService
from shusha.models.utilities import user_downloads_dir, user_log_dir

logger = LoggerService(__name__)

AVAILABLE_THEMES = [
    "bootstrap-light",
    "bootstrap-dark",
    "pydata-light",
    "pydata-dark",
    "nord-light",
    "nord-dark",
    "solarized-light",
    "solarized-dark",
    "catppuccin-light",
    "catppuccin-dark",
    "gruvbox-light",
    "gruvbox-dark",
    "dracula-light",
    "dracula-dark",
    "tokyo-night-light",
    "tokyo-night-dark",
    "one-light",
    "one-dark",
    "everforest-light",
    "everforest-dark",
    "vapor-light",
    "vapor-dark",
    "minty-light",
    "minty-dark",
    "pulse-light",
    "pulse-dark",
    "united-light",
    "united-dark",
    "sandstone-light",
    "sandstone-dark",
]

FILE_ALLOC_MODES = ["none", "prealloc", "trunc", "falloc"]
DISK_CACHE_OPTIONS = ["16M", "32M", "64M", "128M"]


class SettingsWindow(ttk.Toplevel):
    """Graphical Settings Window for configuring application directories and aria2 options."""

    def __init__(
        self,
        master: Any = None,
        api: Any = None,
        on_saved: Any = None,
    ) -> None:
        super().__init__(
            title="Settings - Shusha",
            master=master,
            size=(680, 580),
            resizable=(True, True),
        )
        self.minsize(580, 480)

        self.api = api
        self.on_saved = on_saved
        self.app_settings = AppSettings()

        # Load existing configuration
        user_config = self.app_settings.config_dict.get("USER", {})
        aria2_config = user_config.get("aria2", {})
        aria2_options = user_config.get("aria2.options", {})
        bt_config = user_config.get("bittorrent", {})
        sched_config = user_config.get("scheduler", {})

        # 1. General Variables
        default_dl = user_config.get("download_dir") or str(user_downloads_dir())
        default_log = user_config.get("logs_dir") or str(user_log_dir("shusha"))
        self.download_dir_var = tk.StringVar(value=str(default_dl))
        self.logs_dir_var = tk.StringVar(value=str(default_log))

        raw_theme = user_config.get("theme", "bootstrap-dark")
        if raw_theme in ("darkly", "default"):
            raw_theme = "bootstrap-dark"
        self.theme_var = tk.StringVar(value=raw_theme)

        self.notify_on_complete_var = tk.BooleanVar(
            value=bool(user_config.get("notify_on_complete", True))
        )
        self.minimize_to_tray_var = tk.BooleanVar(
            value=bool(user_config.get("minimize_to_tray", True))
        )
        self.autostart_daemon_var = tk.BooleanVar(
            value=bool(user_config.get("autostart_daemon", True))
        )

        # 2. Performance Variables
        self.max_concurrent_var = tk.StringVar(
            value=str(aria2_options.get("max_concurrent_downloads", 5))
        )
        self.split_var = tk.StringVar(value=str(aria2_options.get("split", 8)))
        self.max_conn_server_var = tk.StringVar(
            value=str(aria2_options.get("max_connection_per_server", 8))
        )
        self.min_split_size_var = tk.StringVar(
            value=str(aria2_options.get("min_split_size", "20M"))
        )
        self.file_alloc_var = tk.StringVar(
            value=str(aria2_options.get("file_allocation", "none"))
        )
        self.disk_cache_var = tk.StringVar(
            value=str(aria2_options.get("disk_cache", "32M"))
        )
        self.max_download_limit_var = tk.StringVar(
            value=str(aria2_options.get("max_overall_download_limit", "0"))
        )
        self.max_upload_limit_var = tk.StringVar(
            value=str(aria2_options.get("max_overall_upload_limit", "0"))
        )

        # 3. RPC & Daemon Variables
        self.rpc_host_var = tk.StringVar(
            value=str(aria2_config.get("host", "localhost"))
        )
        self.rpc_port_var = tk.StringVar(value=str(aria2_config.get("port", 6800)))
        self.rpc_secret_var = tk.StringVar(value=str(aria2_config.get("secret", "")))
        self.session_interval_var = tk.StringVar(
            value=str(aria2_config.get("save_session_interval", 30))
        )

        # 4. BitTorrent Variables
        self.autosync_trackers_var = tk.BooleanVar(
            value=bool(bt_config.get("autosync_trackers", True))
        )
        self.enable_dht_var = tk.BooleanVar(
            value=bool(bt_config.get("enable_dht", True))
        )
        self.enable_pex_var = tk.BooleanVar(
            value=bool(bt_config.get("enable_pex", True))
        )
        self.bt_max_peers_var = tk.StringVar(
            value=str(bt_config.get("max_peers", 55))
        )
        self.seed_ratio_var = tk.StringVar(
            value=str(bt_config.get("seed_ratio", "1.0"))
        )

        # 5. Bandwidth Scheduler Variables
        self.enable_scheduler_var = tk.BooleanVar(
            value=bool(sched_config.get("enabled", False))
        )
        self.sched_start_hour_var = tk.StringVar(
            value=str(sched_config.get("start_hour", 9))
        )
        self.sched_end_hour_var = tk.StringVar(
            value=str(sched_config.get("end_hour", 18))
        )
        self.sched_dl_limit_var = tk.StringVar(
            value=str(sched_config.get("download_limit", "1M"))
        )
        self.sched_ul_limit_var = tk.StringVar(
            value=str(sched_config.get("upload_limit", "256K"))
        )

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tab 1: General
        self._build_general_tab(notebook)

        # Tab 2: Downloads & Performance
        self._build_performance_tab(notebook)

        # Tab 3: Aria2 RPC
        self._build_rpc_tab(notebook)

        # Tab 4: BitTorrent & Trackers
        self._build_bittorrent_tab(notebook)

        # Tab 5: Scheduler
        self._build_scheduler_tab(notebook)

        # Bottom Button Bar
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            btn_bar,
            text="Cancel",
            bootstyle="secondary",
            command=self.destroy,
            width=10,
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            btn_bar,
            text="Save & Apply",
            bootstyle="success",
            command=self._save_and_apply,
            width=14,
        ).pack(side=tk.RIGHT)

    def _build_general_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="General")

        # Storage Frame
        dl_lf = ttk.Labelframe(tab, text="Storage Paths", padding=10)
        dl_lf.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dl_lf, text="Download Directory:").pack(anchor=tk.W, pady=(0, 2))
        dl_row = ttk.Frame(dl_lf)
        dl_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Entry(dl_row, textvariable=self.download_dir_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(
            dl_row,
            text="Browse...",
            bootstyle="secondary-outline",
            command=lambda: self._browse_dir(self.download_dir_var),
        ).pack(side=tk.RIGHT)

        ttk.Label(dl_lf, text="Logs Directory:").pack(anchor=tk.W, pady=(0, 2))
        log_row = ttk.Frame(dl_lf)
        log_row.pack(fill=tk.X)
        ttk.Entry(log_row, textvariable=self.logs_dir_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(
            log_row,
            text="Browse...",
            bootstyle="secondary-outline",
            command=lambda: self._browse_dir(self.logs_dir_var),
        ).pack(side=tk.RIGHT)

        # Appearance & Behavior
        pref_lf = ttk.Labelframe(tab, text="UI & Behavior", padding=10)
        pref_lf.pack(fill=tk.X)

        ttk.Label(pref_lf, text="Theme:").pack(anchor=tk.W, pady=(0, 2))
        theme_combo = ttk.Combobox(
            pref_lf,
            textvariable=self.theme_var,
            values=AVAILABLE_THEMES,
            state="readonly",
        )
        theme_combo.pack(fill=tk.X, pady=(0, 8))
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)

        ttk.Checkbutton(
            pref_lf,
            text="Show desktop notification when downloads complete",
            variable=self.notify_on_complete_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            pref_lf,
            text="Minimize to system tray on window close",
            variable=self.minimize_to_tray_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            pref_lf,
            text="Auto-start Aria2 daemon on launch",
            variable=self.autostart_daemon_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

    def _build_performance_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Downloads & Performance")

        limits_lf = ttk.Labelframe(tab, text="Connections & Allocation", padding=10)
        limits_lf.pack(fill=tk.X, pady=(0, 10))

        grid_f = ttk.Frame(limits_lf)
        grid_f.pack(fill=tk.X)

        rows = [
            ("Max Concurrent Downloads:", self.max_concurrent_var, "entry"),
            ("Split Connections per Task:", self.split_var, "entry"),
            ("Max Connections per Server:", self.max_conn_server_var, "entry"),
            ("Min Split Size:", self.min_split_size_var, "entry"),
            ("File Allocation Mode:", self.file_alloc_var, "combo_alloc"),
            ("Disk Cache Size:", self.disk_cache_var, "combo_cache"),
        ]

        for idx, (label_text, var, widget_type) in enumerate(rows):
            ttk.Label(grid_f, text=label_text).grid(
                row=idx, column=0, sticky=tk.W, pady=3
            )
            if widget_type == "entry":
                ttk.Entry(grid_f, textvariable=var, width=12).grid(
                    row=idx, column=1, sticky=tk.E, pady=3, padx=5
                )
            elif widget_type == "combo_alloc":
                ttk.Combobox(
                    grid_f,
                    textvariable=var,
                    values=FILE_ALLOC_MODES,
                    width=10,
                    state="readonly",
                ).grid(row=idx, column=1, sticky=tk.E, pady=3, padx=5)
            elif widget_type == "combo_cache":
                ttk.Combobox(
                    grid_f,
                    textvariable=var,
                    values=DISK_CACHE_OPTIONS,
                    width=10,
                    state="readonly",
                ).grid(row=idx, column=1, sticky=tk.E, pady=3, padx=5)

        # Speed limits
        speed_lf = ttk.Labelframe(
            tab, text="Global Speed Limits (0 = Unlimited)", padding=10
        )
        speed_lf.pack(fill=tk.X)

        speed_grid = ttk.Frame(speed_lf)
        speed_grid.pack(fill=tk.X)

        ttk.Label(speed_grid, text="Max Download Speed (KiB/s):").grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(speed_grid, textvariable=self.max_download_limit_var, width=12).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(speed_grid, text="Max Upload Speed (KiB/s):").grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(speed_grid, textvariable=self.max_upload_limit_var, width=12).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

    def _build_rpc_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Aria2 RPC")

        rpc_lf = ttk.Labelframe(tab, text="Daemon Connection Settings", padding=10)
        rpc_lf.pack(fill=tk.X, pady=(0, 10))

        rpc_grid = ttk.Frame(rpc_lf)
        rpc_grid.pack(fill=tk.X)

        ttk.Label(rpc_grid, text="RPC Host:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(rpc_grid, textvariable=self.rpc_host_var, width=22).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(rpc_grid, text="RPC Port:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(rpc_grid, textvariable=self.rpc_port_var, width=22).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(rpc_grid, text="RPC Secret Token:").grid(
            row=2, column=0, sticky=tk.W, pady=4
        )
        self.secret_entry = ttk.Entry(
            rpc_grid, textvariable=self.rpc_secret_var, width=22, show="*"
        )
        self.secret_entry.grid(row=2, column=1, sticky=tk.E, pady=4, padx=5)

        session_lf = ttk.Labelframe(tab, text="Session Persistence", padding=10)
        session_lf.pack(fill=tk.X)

        s_grid = ttk.Frame(session_lf)
        s_grid.pack(fill=tk.X)

        ttk.Label(s_grid, text="Session Save Interval (seconds):").grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(s_grid, textvariable=self.session_interval_var, width=10).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

    def _build_bittorrent_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="BitTorrent")

        bt_lf = ttk.Labelframe(tab, text="Swarm & Discovery", padding=10)
        bt_lf.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            bt_lf,
            text="Auto-sync best public trackers on startup",
            variable=self.autosync_trackers_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            bt_lf,
            text="Enable DHT (Distributed Hash Table)",
            variable=self.enable_dht_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            bt_lf,
            text="Enable Peer Exchange (PEX)",
            variable=self.enable_pex_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=2)

        peer_grid = ttk.Frame(bt_lf)
        peer_grid.pack(fill=tk.X, pady=4)

        ttk.Label(peer_grid, text="Max Peers per Torrent:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(peer_grid, textvariable=self.bt_max_peers_var, width=8).grid(
            row=0, column=1, sticky=tk.E, pady=2, padx=5
        )

        ttk.Label(peer_grid, text="Seeding Ratio Limit:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(peer_grid, textvariable=self.seed_ratio_var, width=8).grid(
            row=1, column=1, sticky=tk.E, pady=2, padx=5
        )

        # Trackers text
        tr_lf = ttk.Labelframe(tab, text="Public Trackers List", padding=10)
        tr_lf.pack(fill=tk.BOTH, expand=True)

        top_row = ttk.Frame(tr_lf)
        top_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(
            top_row,
            text="Fetch Best Public Trackers Now",
            command=self._fetch_trackers,
            bootstyle="info-outline",
        ).pack(side=tk.LEFT)

        self.trackers_box = tk.Text(tr_lf, height=5, wrap=tk.NONE)
        self.trackers_box.pack(fill=tk.BOTH, expand=True)
        self.trackers_box.insert("1.0", "\n".join(TrackerService.get_trackers()))

    def _build_scheduler_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Bandwidth Scheduler")

        sched_lf = ttk.Labelframe(tab, text="Automated Throttling Profile", padding=10)
        sched_lf.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            sched_lf,
            text="Enable Bandwidth Scheduling",
            variable=self.enable_scheduler_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W, pady=(0, 8))

        grid = ttk.Frame(sched_lf)
        grid.pack(fill=tk.X)

        ttk.Label(grid, text="Day Window Start (Hour 0-23):").grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid, textvariable=self.sched_start_hour_var, width=8).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(grid, text="Day Window End (Hour 0-23):").grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid, textvariable=self.sched_end_hour_var, width=8).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(grid, text="Daytime Download Limit (e.g. 1M):").grid(
            row=2, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid, textvariable=self.sched_dl_limit_var, width=8).grid(
            row=2, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(grid, text="Daytime Upload Limit (e.g. 256K):").grid(
            row=3, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid, textvariable=self.sched_ul_limit_var, width=8).grid(
            row=3, column=1, sticky=tk.E, pady=4, padx=5
        )

    def _fetch_trackers(self) -> None:
        def _bg():
            trackers = TrackerService.fetch_latest_trackers_sync()
            self.trackers_box.delete("1.0", tk.END)
            self.trackers_box.insert("1.0", "\n".join(trackers))

        threading_thread = contextlib.suppress(Exception)
        with threading_thread:
            TrackerService.fetch_latest_trackers_async(
                on_complete=lambda tr: self.trackers_box.insert(tk.END, "")
            )

    def _on_theme_changed(self, event=None) -> None:
        theme = self.theme_var.get().strip()
        with contextlib.suppress(Exception):
            ttk.Style().theme_use(theme)

    def _browse_dir(self, var: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=var.get(), parent=self)
        if selected:
            var.set(selected)

    def _save_and_apply(self) -> None:
        """Save all settings to configuration and apply runtime changes."""
        try:
            download_dir = self.download_dir_var.get().strip()
            logs_dir = self.logs_dir_var.get().strip()
            theme = self.theme_var.get().strip()

            max_concurrent = int(self.max_concurrent_var.get().strip() or "5")
            split = int(self.split_var.get().strip() or "8")
            max_conn_server = int(self.max_conn_server_var.get().strip() or "8")
            min_split_size = self.min_split_size_var.get().strip() or "20M"
            file_alloc = self.file_alloc_var.get().strip() or "none"
            disk_cache = self.disk_cache_var.get().strip() or "32M"
            max_dl_limit = self.max_download_limit_var.get().strip() or "0"
            max_ul_limit = self.max_upload_limit_var.get().strip() or "0"

            rpc_host = self.rpc_host_var.get().strip()
            rpc_port = int(self.rpc_port_var.get().strip() or "6800")
            rpc_secret = self.rpc_secret_var.get().strip()
            session_interval = int(self.session_interval_var.get().strip() or "30")

            # BitTorrent
            bt_max_peers = int(self.bt_max_peers_var.get().strip() or "55")
            seed_ratio = self.seed_ratio_var.get().strip() or "1.0"

            # Scheduler rule
            sched_enabled = self.enable_scheduler_var.get()
            sched_start = int(self.sched_start_hour_var.get().strip() or "9")
            sched_end = int(self.sched_end_hour_var.get().strip() or "18")
            sched_dl = self.sched_dl_limit_var.get().strip() or "1M"
            sched_ul = self.sched_ul_limit_var.get().strip() or "256K"

            settings_payload: dict[str, Any] = {
                "download_dir": download_dir,
                "logs_dir": logs_dir,
                "theme": theme,
                "notify_on_complete": self.notify_on_complete_var.get(),
                "minimize_to_tray": self.minimize_to_tray_var.get(),
                "autostart_daemon": self.autostart_daemon_var.get(),
                "aria2": {
                    "host": rpc_host,
                    "port": rpc_port,
                    "secret": rpc_secret,
                    "save_session_interval": session_interval,
                },
                "aria2.options": {
                    "dir": download_dir,
                    "max_concurrent_downloads": max_concurrent,
                    "split": split,
                    "max_connection_per_server": max_conn_server,
                    "min_split_size": min_split_size,
                    "file_allocation": file_alloc,
                    "disk_cache": disk_cache,
                    "max_overall_download_limit": max_dl_limit,
                    "max_overall_upload_limit": max_ul_limit,
                },
                "bittorrent": {
                    "autosync_trackers": self.autosync_trackers_var.get(),
                    "enable_dht": self.enable_dht_var.get(),
                    "enable_pex": self.enable_pex_var.get(),
                    "max_peers": bt_max_peers,
                    "seed_ratio": seed_ratio,
                },
                "scheduler": {
                    "enabled": sched_enabled,
                    "start_hour": sched_start,
                    "end_hour": sched_end,
                    "download_limit": sched_dl,
                    "upload_limit": sched_ul,
                },
            }

            self.app_settings.update_settings(settings_payload)
            self.app_settings.save_settings()

            # Update API scheduler
            if self.api and hasattr(self.api, "scheduler"):
                self.api.scheduler.rules.clear()
                if sched_enabled:
                    self.api.scheduler.add_rule(
                        ScheduleRule(
                            name="Custom Schedule",
                            enabled=True,
                            start_hour=sched_start,
                            start_minute=0,
                            end_hour=sched_end,
                            end_minute=0,
                            days_of_week=[0, 1, 2, 3, 4, 5, 6],
                            max_download_limit=sched_dl,
                            max_upload_limit=sched_ul,
                        )
                    )

            # Apply runtime options via aria2 API if connected
            if self.api and hasattr(self.api, "client"):
                if hasattr(self.api.client, "secret"):
                    self.api.client.secret = rpc_secret or None
                if hasattr(self.api, "remote") and hasattr(self.api.remote, "secret"):
                    self.api.remote.secret = rpc_secret or None
                try:
                    aria2_runtime_opts = {
                        "max-overall-download-limit": (
                            f"{max_dl_limit}K" if max_dl_limit != "0" else "0"
                        ),
                        "max-overall-upload-limit": (
                            f"{max_ul_limit}K" if max_ul_limit != "0" else "0"
                        ),
                        "max-concurrent-downloads": str(max_concurrent),
                        "enable-dht": "true" if self.enable_dht_var.get() else "false",
                        "enable-peer-exchange": "true" if self.enable_pex_var.get() else "false",
                    }
                    self.api.client.change_global_option(aria2_runtime_opts)
                except Exception as rpc_err:
                    logger.log(
                        f"Could not apply live aria2 options: {rpc_err}",
                        level="warning",
                    )

            if callable(self.on_saved):
                self.on_saved()

            self.destroy()

        except Exception as e:
            logger.log(f"Error saving settings: {e}", level="error")
