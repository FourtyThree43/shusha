"""
Download Status & Detailed Inspector Window.
Displays live progress meters, BitTorrent peers, connected servers/mirrors, and per-task bandwidth limits.
"""

from __future__ import annotations

import time
import tkinter as tk
from typing import TYPE_CHECKING, Any

import ttkbootstrap as ttk
from PIL import Image

from shusha.models.logger import LoggerService
from shusha.models.utilities import format_speed

if TYPE_CHECKING:
    from shusha.controller.api import ShushaAPI as Api
    from shusha.models.structs_downloads import Download

if not hasattr(Image, "CUBIC"):
    Image.CUBIC = getattr(Image, "BICUBIC", getattr(Image.Resampling, "BICUBIC", 3))  # ty: ignore[unresolved-attribute]

logger = LoggerService(__name__)


class DownloadMeter(ttk.Meter):
    """Circular progress meter for live download progress."""

    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.paused = ttk.BooleanVar(self, False)

    @property
    def used_var(self):
        if hasattr(self, "amount_used_var"):
            return self.amount_used_var
        return getattr(self, "amountusedvar", None)

    @property
    def total_var(self):
        if hasattr(self, "amount_total_var"):
            return self.amount_total_var
        return getattr(self, "amounttotalvar", None)

    def start(self):
        self.paused.set(False)
        u_var = self.used_var
        t_var = self.total_var
        if u_var and t_var:
            while u_var.get() <= t_var.get():
                if self.paused.get():
                    break
                if u_var.get() == t_var.get():
                    self.configure(subtext="Download complete")
                    break
                self.step()
                time.sleep(0.25)
                self.master.update_idletasks()

    def pause(self):
        self.paused.set(True)

    def reset(self):
        u_var = self.used_var
        if u_var:
            u_var.set(0)


class DownloadWindow(ttk.Toplevel):
    """Multi-tab detailed live status and inspector dialog for an aria2 download."""

    def __init__(self, api: Api | None = None, **kwargs: Any):
        super().__init__(
            title="Download Inspector - Shusha",
            size=(780, 520),
            position=(50, 50),
            resizable=(True, True),
            **kwargs,
        )
        self.config(padx=12, pady=12)
        self.api = api
        self.download_gid: str | None = None
        self._is_alive = True

        # Notebook container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tab 1: General
        self.general_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.general_tab, text="General")
        self._build_general_tab()

        # Tab 2: Peers (BitTorrent)
        self.peers_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.peers_tab, text="Peers (BitTorrent)")
        self._build_peers_tab()

        # Tab 3: Servers (HTTP/FTP Mirrors)
        self.servers_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.servers_tab, text="Servers & Mirrors")
        self._build_servers_tab()

        # Tab 4: Speed Limits
        self.limits_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.limits_tab, text="Task Limits")
        self._build_limits_tab()

        # Bottom Action Bar
        self.controls = ttk.Frame(self, padding=(0, 5))
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)

        self.start_btn = ttk.Button(
            self.controls, text="Start", command=self.start, bootstyle="info", width=10
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.pause_btn = ttk.Button(
            self.controls,
            text="Pause",
            command=self.pause,
            bootstyle="warning",
            width=10,
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.resume_btn = ttk.Button(
            self.controls,
            text="Resume",
            command=self.un_pause,
            bootstyle="success",
            width=10,
        )
        self.resume_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.resume_btn.state(["disabled"])

        self.close_btn = ttk.Button(
            self.controls,
            text="Close",
            command=self._on_close,
            bootstyle="secondary",
            width=10,
        )
        self.close_btn.pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(1000, self.update_stats_periodically)

    def _build_general_tab(self):
        status_lf = ttk.Labelframe(self.general_tab, text="Live Transfer Status")
        status_lf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.stats_f = ttk.Frame(status_lf)
        self.stats_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        meter_f = ttk.Frame(status_lf)
        meter_f.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=15, pady=10)
        self.meter = DownloadMeter(
            meter_f,
            meter_size=190,
            padding=5,
            amount_total=100,
            meter_type="semi",
            text_right="%",
            subtext="downloaded",
            interactive=False,
            stripe_thickness=6,
            bootstyle="info",
        )
        self.meter.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _build_peers_tab(self):
        ttk.Label(
            self.peers_tab,
            text="Active BitTorrent Peer Swarm",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        cols = ("ip", "port", "download_speed", "upload_speed", "seeder", "client")
        self.peers_tree = ttk.Treeview(
            self.peers_tab, columns=cols, show="headings", selectmode="browse"
        )
        self.peers_tree.heading("ip", text="IP Address")
        self.peers_tree.heading("port", text="Port")
        self.peers_tree.heading("download_speed", text="Down Speed")
        self.peers_tree.heading("upload_speed", text="Up Speed")
        self.peers_tree.heading("seeder", text="Seeder?")
        self.peers_tree.heading("client", text="Peer Client")

        self.peers_tree.column("ip", width=140)
        self.peers_tree.column("port", width=70, anchor=tk.CENTER)
        self.peers_tree.column("download_speed", width=110, anchor=tk.E)
        self.peers_tree.column("upload_speed", width=110, anchor=tk.E)
        self.peers_tree.column("seeder", width=80, anchor=tk.CENTER)
        self.peers_tree.column("client", width=150)

        sb = ttk.Scrollbar(
            self.peers_tab, orient=tk.VERTICAL, command=self.peers_tree.yview
        )
        self.peers_tree.configure(yscrollcommand=sb.set)
        self.peers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_servers_tab(self):
        ttk.Label(
            self.servers_tab,
            text="Connected Download Servers & Multi-Source Mirrors",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        cols = ("uri", "speed", "conns")
        self.servers_tree = ttk.Treeview(
            self.servers_tab, columns=cols, show="headings", selectmode="browse"
        )
        self.servers_tree.heading("uri", text="Server / Mirror URI")
        self.servers_tree.heading("speed", text="Download Speed")
        self.servers_tree.heading("conns", text="Active Connections")

        self.servers_tree.column("uri", width=420)
        self.servers_tree.column("speed", width=130, anchor=tk.E)
        self.servers_tree.column("conns", width=130, anchor=tk.CENTER)

        sb = ttk.Scrollbar(
            self.servers_tab, orient=tk.VERTICAL, command=self.servers_tree.yview
        )
        self.servers_tree.configure(yscrollcommand=sb.set)
        self.servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_limits_tab(self):
        frame = ttk.Labelframe(
            self.limits_tab, text="Bandwidth Throttling (0 = Unlimited)"
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(frame, text="Max Download Limit (KB/s):").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=12
        )
        self.limit_dl_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.limit_dl_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=10, pady=12
        )

        ttk.Label(frame, text="Max Upload Limit (KB/s):").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=12
        )
        self.limit_ul_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.limit_ul_var, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=10, pady=12
        )

        apply_btn = ttk.Button(
            frame,
            text="Apply Speed Limits",
            bootstyle="primary",
            command=self._apply_limits,
        )
        apply_btn.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=15)

    def _apply_limits(self):
        if not self.api or not self.download_gid:
            return
        dl_val = self.limit_dl_var.get().strip() or "0"
        ul_val = self.limit_ul_var.get().strip() or "0"

        dl_str = f"{dl_val}K" if dl_val != "0" else "0"
        ul_str = f"{ul_val}K" if ul_val != "0" else "0"

        success = self.api.change_download_speed_limits(
            self.download_gid, max_download=dl_str, max_upload=ul_str
        )
        if success:
            logger.log(
                f"Applied speed limits for {self.download_gid}: DL={dl_str}, UL={ul_str}"
            )

    def update_stats_frame(self, download: Download):
        if not download:
            return
        self.download_gid = download.gid

        for widget in self.stats_f.winfo_children():
            widget.destroy()

        u_var = self.meter.used_var
        if u_var:
            u_var.set(int(download.progress))

        first_uri = "N/A"
        if download.files and len(download.files) > 0 and download.files[0].uris:
            first_uri = download.files[0].uris[0].get("uri", "N/A")

        dl_info = {
            "File": download.name,
            "Source URI": first_uri,
            "Status": download.status.capitalize(),
            "Downloaded": download.completed_length_string(),
            "Total Size": download.total_length_string(),
            "Transfer Rate": download.download_speed_string(),
            "ETA": download.eta_string(),
            "Connections": str(download.connections),
            "GID": str(download.gid),
        }

        for key, value in dl_info.items():
            row_frame = ttk.Frame(self.stats_f)
            row_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
            ttk.Label(
                row_frame, text=f"{key}:", font=("Helvetica", 9, "bold"), width=14
            ).pack(side=tk.LEFT)
            ttk.Label(
                row_frame, text=str(value), wraplength=350, font=("Helvetica", 9)
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._refresh_peers()
        self._refresh_servers()

    def _refresh_peers(self):
        if not self.api or not self.download_gid:
            return
        for item in self.peers_tree.get_children():
            self.peers_tree.delete(item)

        peers = self.api.get_peers(self.download_gid)
        for p in peers:
            ip = p.get("ip", "Unknown")
            port = str(p.get("port", ""))
            dspeed = format_speed(int(p.get("downloadSpeed", 0) or 0))
            uspeed = format_speed(int(p.get("uploadSpeed", 0) or 0))
            seeder = "Yes" if p.get("seeder") == "true" else "No"
            client = p.get("peerId", "")
            self.peers_tree.insert(
                "", "end", values=(ip, port, dspeed, uspeed, seeder, client)
            )

    def _refresh_servers(self):
        if not self.api or not self.download_gid:
            return
        for item in self.servers_tree.get_children():
            self.servers_tree.delete(item)

        servers_data = self.api.get_servers(self.download_gid)
        for s in servers_data:
            servers_list = s.get("servers", [])
            for srv in servers_list:
                uri = srv.get("uri", "")
                speed = format_speed(int(srv.get("downloadSpeed", 0) or 0))
                conns = str(srv.get("currentConnection", 1))
                self.servers_tree.insert("", "end", values=(uri, speed, conns))

    def update_stats_periodically(self):
        if not self._is_alive:
            return

        if self.download_gid and self.api:
            st_struct = self.api.get_download(self.download_gid)
            if st_struct:
                self.update_stats_frame(st_struct)
                if st_struct.is_active:
                    self.pause_btn.state(["!disabled"])
                    self.resume_btn.state(["disabled"])
                    self.start_btn.state(["disabled"])
                elif st_struct.is_paused:
                    self.pause_btn.state(["disabled"])
                    self.resume_btn.state(["!disabled"])
                    self.start_btn.state(["disabled"])
                elif st_struct.has_failed:
                    self.pause_btn.state(["disabled"])
                    self.resume_btn.state(["disabled"])
                    self.start_btn.state(["!disabled"])
                    self.meter.configure(subtext="Failed")

        if self._is_alive:
            self.after(1500, self.update_stats_periodically)

    def start(self):
        if self.download_gid and self.api:
            self.api.resume(self.download_gid)

    def pause(self):
        if self.download_gid and self.api:
            self.api.pause(self.download_gid)

    def un_pause(self):
        if self.download_gid and self.api:
            self.api.resume(self.download_gid)

    def cancel(self):
        if self.download_gid and self.api:
            self.api.remove(self.download_gid)
        self._on_close()

    def _on_close(self):
        self._is_alive = False
        self.destroy()
