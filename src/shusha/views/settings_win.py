# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT

import contextlib
import tkinter as tk
from tkinter import filedialog
from typing import Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService
from shusha.models.settings import AppSettings
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


class SettingsWindow(ttk.Toplevel):
    """
    Graphical Settings Window for configuring application directories,
    download connection limits, speed throttles, themes, and aria2 RPC options.
    """

    def __init__(self, master=None, api=None, on_saved=None):
        super().__init__(
            title="Settings - Shusha",
            master=master,
            size=(560, 520),
            resizable=(False, False),
        )

        self.api = api
        self.on_saved = on_saved
        self.app_settings = AppSettings()

        # Load existing configuration
        user_config = self.app_settings.config_dict.get("USER", {})
        aria2_config = user_config.get("aria2", {})
        aria2_options = user_config.get("aria2.options", {})

        # Form Variables
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

        self.max_concurrent_var = tk.StringVar(
            value=str(aria2_options.get("max_concurrent_downloads", 5))
        )
        self.split_var = tk.StringVar(value=str(aria2_options.get("split", 8)))
        self.max_conn_server_var = tk.StringVar(
            value=str(aria2_options.get("max_connection_per_server", 5))
        )
        self.max_download_limit_var = tk.StringVar(
            value=str(aria2_options.get("max_overall_download_limit", "0"))
        )
        self.max_upload_limit_var = tk.StringVar(
            value=str(aria2_options.get("max_overall_upload_limit", "0"))
        )

        self.rpc_host_var = tk.StringVar(
            value=str(aria2_config.get("host", "localhost"))
        )
        self.rpc_port_var = tk.StringVar(value=str(aria2_config.get("port", 6800)))
        self.rpc_secret_var = tk.StringVar(value=str(aria2_config.get("secret", "")))

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 1. General Tab
        general_tab = ttk.Frame(notebook, padding=12)
        notebook.add(general_tab, text="General")

        # Download Directory
        dl_lf = ttk.Labelframe(general_tab, text="Storage & Logs", padding=10)
        dl_lf.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dl_lf, text="Download Directory:").pack(anchor=tk.W, pady=(0, 2))
        dl_row = ttk.Frame(dl_lf)
        dl_row.pack(fill=tk.X, pady=(0, 8))
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

        # Appearance & Notifications
        pref_lf = ttk.Labelframe(general_tab, text="Preferences", padding=10)
        pref_lf.pack(fill=tk.X)

        ttk.Label(pref_lf, text="Application Theme:").pack(anchor=tk.W, pady=(0, 2))
        theme_combo = ttk.Combobox(
            pref_lf,
            textvariable=self.theme_var,
            values=AVAILABLE_THEMES,
            state="readonly",
        )
        theme_combo.pack(fill=tk.X, pady=(0, 8))

        ttk.Checkbutton(
            pref_lf,
            text="Show desktop notifications on completion",
            variable=self.notify_on_complete_var,
            bootstyle="round-toggle",
        ).pack(anchor=tk.W)

        # 2. Connection & Speed Tab
        conn_tab = ttk.Frame(notebook, padding=12)
        notebook.add(conn_tab, text="Downloads & Speed")

        limits_lf = ttk.Labelframe(conn_tab, text="Connection Limits", padding=10)
        limits_lf.pack(fill=tk.X, pady=(0, 10))

        grid_f = ttk.Frame(limits_lf)
        grid_f.pack(fill=tk.X)

        ttk.Label(grid_f, text="Max Concurrent Downloads:").grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid_f, textvariable=self.max_concurrent_var, width=10).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(grid_f, text="Split Connections per Download:").grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid_f, textvariable=self.split_var, width=10).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(grid_f, text="Max Connections per Server:").grid(
            row=2, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(grid_f, textvariable=self.max_conn_server_var, width=10).grid(
            row=2, column=1, sticky=tk.E, pady=4, padx=5
        )

        speed_lf = ttk.Labelframe(
            conn_tab, text="Bandwidth Limits (0 = Unlimited)", padding=10
        )
        speed_lf.pack(fill=tk.X)

        speed_grid = ttk.Frame(speed_lf)
        speed_grid.pack(fill=tk.X)

        ttk.Label(speed_grid, text="Max Download Speed (KiB/s):").grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(speed_grid, textvariable=self.max_download_limit_var, width=10).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(speed_grid, text="Max Upload Speed (KiB/s):").grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(speed_grid, textvariable=self.max_upload_limit_var, width=10).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

        # 3. Aria2 RPC Tab
        rpc_tab = ttk.Frame(notebook, padding=12)
        notebook.add(rpc_tab, text="Aria2 RPC")

        rpc_lf = ttk.Labelframe(rpc_tab, text="Daemon Connection Settings", padding=10)
        rpc_lf.pack(fill=tk.X)

        rpc_grid = ttk.Frame(rpc_lf)
        rpc_grid.pack(fill=tk.X)

        ttk.Label(rpc_grid, text="RPC Host:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(rpc_grid, textvariable=self.rpc_host_var, width=20).grid(
            row=0, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(rpc_grid, text="RPC Port:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(rpc_grid, textvariable=self.rpc_port_var, width=20).grid(
            row=1, column=1, sticky=tk.E, pady=4, padx=5
        )

        ttk.Label(rpc_grid, text="RPC Secret Token:").grid(
            row=2, column=0, sticky=tk.W, pady=4
        )
        ttk.Entry(rpc_grid, textvariable=self.rpc_secret_var, width=20, show="*").grid(
            row=2, column=1, sticky=tk.E, pady=4, padx=5
        )

        # Bottom Buttons
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
            width=12,
        ).pack(side=tk.RIGHT)

    def _browse_dir(self, var: tk.StringVar):
        selected = filedialog.askdirectory(initialdir=var.get(), parent=self)
        if selected:
            var.set(selected)

    def _save_and_apply(self):
        """Save settings to disk and apply options to active aria2 instance."""
        try:
            download_dir = self.download_dir_var.get().strip()
            logs_dir = self.logs_dir_var.get().strip()
            theme = self.theme_var.get().strip()

            max_concurrent = int(self.max_concurrent_var.get().strip() or "5")
            split = int(self.split_var.get().strip() or "8")
            max_conn_server = int(self.max_conn_server_var.get().strip() or "5")
            max_dl_limit = self.max_download_limit_var.get().strip() or "0"
            max_ul_limit = self.max_upload_limit_var.get().strip() or "0"

            rpc_host = self.rpc_host_var.get().strip()
            rpc_port = int(self.rpc_port_var.get().strip() or "6800")
            rpc_secret = self.rpc_secret_var.get().strip()

            # Prepare update dictionary
            settings_payload: dict[str, Any] = {
                "download_dir": download_dir,
                "logs_dir": logs_dir,
                "theme": theme,
                "notify_on_complete": self.notify_on_complete_var.get(),
                "aria2": {
                    "host": rpc_host,
                    "port": rpc_port,
                    "secret": rpc_secret,
                },
                "aria2.options": {
                    "dir": download_dir,
                    "max_concurrent_downloads": max_concurrent,
                    "split": split,
                    "max_connection_per_server": max_conn_server,
                    "max_overall_download_limit": max_dl_limit,
                    "max_overall_upload_limit": max_ul_limit,
                },
            }

            self.app_settings.update_settings(settings_payload)
            self.app_settings.save_settings()

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
                    }
                    self.api.client.change_global_option(aria2_runtime_opts)
                except Exception as rpc_err:
                    logger.log(
                        f"Could not apply live aria2 options: {rpc_err}",
                        level="warning",
                    )

            # Apply theme dynamically
            with contextlib.suppress(Exception):
                ttk.Style().theme_use(theme)

            if callable(self.on_saved):
                self.on_saved()

            self.destroy()

        except Exception as e:
            logger.log(f"Error saving settings: {e}", level="error")


if __name__ == "__main__":
    root = ttk.Window(themename="bootstrap-dark")
    root.withdraw()
    win = SettingsWindow(root)
    win.mainloop()
