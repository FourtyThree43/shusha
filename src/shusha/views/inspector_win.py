"""Comprehensive Tabbed Inspector Window for Shusha-DM.

Provides in-depth telemetry and control over individual downloads:
- Overview (hashes, speeds, ETA, path)
- Live Speed Graph
- Real-time Piece Map
- Selective Torrent Files list
- Connected BitTorrent Peers
- Active Mirror Servers
- BitTorrent Trackers manager
- Live Download Options
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import ttkbootstrap as ttk
from ttkbootstrap import Tableview

from shusha.controller.api import ShushaAPI
from shusha.models.structs_downloads import Download
from shusha.models.tracker_service import TrackerService
from shusha.models.utilities import open_path_in_file_manager
from shusha.views.piece_map import PieceMapWidget
from shusha.views.speed_graph import SpeedGraphWidget


class DownloadInspectorWindow(ttk.Toplevel):
    """Modern tabbed inspector window displaying download status and analytics."""

    def __init__(
        self,
        master: Any,
        api: ShushaAPI,
        download: Download,
    ) -> None:
        super().__init__(master=master)
        self.api = api
        self.download = download

        self.title(f"Task Inspector: {download.name or download.gid}")
        self.geometry("780x560")
        self.minsize(640, 450)

        self._build_ui()
        self._poll_telemetry()

    def _build_ui(self) -> None:
        # Header banner
        header_frame = ttk.Frame(self, padding=(12, 10, 12, 6))
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text=self.download.name or "Download Task",
            font=("TkDefaultFont", 11, "bold"),
            anchor="w",
        )
        title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)

        # Quick action buttons
        ttk.Button(
            header_frame,
            text="Open Folder",
            command=self._open_folder,
            bootstyle="outline-primary",
        ).pack(side=tk.RIGHT, padx=4)

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=tk.YES, padx=10, pady=6)

        # Tab 1: Overview
        self.tab_overview = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_overview, text="Overview")
        self._build_overview_tab()

        # Tab 2: Speed Graph
        self.tab_graph = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_graph, text="Speed Graph")
        self.speed_widget = SpeedGraphWidget(self.tab_graph, height=220)
        self.speed_widget.pack(fill=tk.BOTH, expand=tk.YES)

        # Tab 3: Piece Map
        self.tab_pieces = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_pieces, text="Piece Map")
        self.piece_widget = PieceMapWidget(self.tab_pieces, download=self.download)
        self.piece_widget.pack(fill=tk.BOTH, expand=tk.YES)

        # Tab 4: Files (for multi-file torrents/metalinks)
        self.tab_files = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_files, text="Files")
        self._build_files_tab()

        # Tab 5: Peers
        self.tab_peers = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_peers, text="Peers")
        self._build_peers_tab()

        # Tab 6: Servers
        self.tab_servers = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_servers, text="Servers")
        self._build_servers_tab()

        # Tab 7: Trackers
        self.tab_trackers = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_trackers, text="Trackers")
        self._build_trackers_tab()

        # Tab 8: Options
        self.tab_options = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_options, text="Options")
        self._build_options_tab()

    def _build_overview_tab(self) -> None:
        props = [
            ("GID", self.download.gid),
            ("Status", self.download.status),
            ("Progress", self.download.progress_string()),
            ("Size", f"{self.download.completed_length_string()} / {self.download.total_length_string()}"),
            ("Download Speed", self.download.download_speed_string()),
            ("Upload Speed", self.download.upload_speed_string()),
            ("ETA", self.download.eta_string()),
            ("Save Directory", str(self.download.dir)),
            ("Connections", str(self.download.connections)),
            ("Error Info", str(self.download.error_message or "None")),
        ]

        for _idx, (lbl, val) in enumerate(props):
            row = ttk.Frame(self.tab_overview)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"{lbl}:", width=16, font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(row, text=val, font=("TkDefaultFont", 9)).pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)

    def _build_files_tab(self) -> None:
        cols = ["Index", "Filename", "Size", "Completed", "Selected"]
        self.files_table = Tableview(
            master=self.tab_files,
            coldata=cols,
            rowdata=[],
            paginated=True,
            searchable=True,
            bootstyle="primary",
        )
        self.files_table.pack(fill=tk.BOTH, expand=tk.YES)
        self._refresh_files_data()

    def _refresh_files_data(self) -> None:
        rows: list[list[str]] = []
        for f in self.download.files:
            rows.append([
                str(f.index),
                f.path.name if f.path else f"File #{f.index}",
                f.length_string(),
                f.completed_length_string(),
                "Yes" if f.selected else "No",
            ])
        self.files_table.delete_rows()
        self.files_table.insert_rows("end", rows)
        self.files_table.load_table_data()

    def _build_peers_tab(self) -> None:
        cols = ["IP:Port", "Client / Peer ID", "DL Speed", "UL Speed", "Progress", "Seeder"]
        self.peers_table = Tableview(
            master=self.tab_peers,
            coldata=cols,
            rowdata=[],
            paginated=True,
            searchable=True,
            bootstyle="info",
        )
        self.peers_table.pack(fill=tk.BOTH, expand=tk.YES)

    def _build_servers_tab(self) -> None:
        cols = ["Index", "Mirror URI", "Current Speed", "Active Conns"]
        self.servers_table = Tableview(
            master=self.tab_servers,
            coldata=cols,
            rowdata=[],
            paginated=True,
            searchable=True,
            bootstyle="secondary",
        )
        self.servers_table.pack(fill=tk.BOTH, expand=tk.YES)

    def _build_trackers_tab(self) -> None:
        top_bar = ttk.Frame(self.tab_trackers)
        top_bar.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(
            top_bar,
            text="Add Best Public Trackers",
            command=self._append_public_trackers,
            bootstyle="success-outline",
        ).pack(side=tk.LEFT, padx=4)

        ttk.Label(self.tab_trackers, text="Trackers List:").pack(anchor="w")
        self.trackers_box = tk.Text(self.tab_trackers, height=8, wrap=tk.NONE)
        self.trackers_box.pack(fill=tk.BOTH, expand=tk.YES, pady=4)

        # Prepopulate with fallback trackers
        self.trackers_box.insert("1.0", "\n".join(TrackerService.get_trackers()))

    def _append_public_trackers(self) -> None:
        best_trackers = TrackerService.get_trackers()
        current_text = self.trackers_box.get("1.0", tk.END).strip()
        current_set = set(current_text.splitlines()) if current_text else set()
        new_trackers = [t for t in best_trackers if t not in current_set]

        if new_trackers:
            self.trackers_box.insert(tk.END, ("\n" if current_text else "") + "\n".join(new_trackers))
            csv_val = ",".join(list(current_set) + new_trackers)
            if self.download.gid:
                self.api.client.change_option(self.download.gid, {"bt-tracker": csv_val})

    def _build_options_tab(self) -> None:
        row1 = ttk.Frame(self.tab_options)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Max Download Limit:", width=20).pack(side=tk.LEFT)
        self.dl_limit_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self.dl_limit_var, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Label(row1, text="(e.g. 500K, 2M, 0 for unlimited)").pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(self.tab_options)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="Max Upload Limit:", width=20).pack(side=tk.LEFT)
        self.ul_limit_var = tk.StringVar(value="0")
        ttk.Entry(row2, textvariable=self.ul_limit_var, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Label(row2, text="(e.g. 100K, 1M, 0)").pack(side=tk.LEFT, padx=4)

        btn_row = ttk.Frame(self.tab_options)
        btn_row.pack(fill=tk.X, pady=10)
        ttk.Button(
            btn_row,
            text="Apply Options",
            command=self._apply_options,
            bootstyle="success",
        ).pack(side=tk.LEFT)

    def _apply_options(self) -> None:
        if self.download.gid:
            self.api.change_download_speed_limits(
                self.download.gid,
                max_download=self.dl_limit_var.get().strip() or "0",
                max_upload=self.ul_limit_var.get().strip() or "0",
            )

    def _open_folder(self) -> None:
        if self.download.dir:
            open_path_in_file_manager(self.download.dir)

    def _poll_telemetry(self) -> None:
        """Periodic background telemetry polling for graph and tables."""
        if not self.winfo_exists():
            return

        try:
            if self.download.gid:
                # Update speed graph
                self.speed_widget.add_data_point(
                    self.download.download_speed, self.download.upload_speed
                )
                self.piece_widget.update_download(self.download)

                # Peers
                peers = self.api.get_peers(self.download.gid)
                peer_rows = [
                    [
                        f"{p.get('ip', '')}:{p.get('port', '')}",
                        p.get("peerId", "Unknown"),
                        f"{int(p.get('downloadSpeed', 0))/1024:.1f} KB/s",
                        f"{int(p.get('uploadSpeed', 0))/1024:.1f} KB/s",
                        f"{p.get('bitfield', '')[:10]}...",
                        "Yes" if p.get("seeder") == "true" else "No",
                    ]
                    for p in peers
                ]
                self.peers_table.delete_rows()
                self.peers_table.insert_rows("end", peer_rows)
                self.peers_table.load_table_data()

                # Servers
                servers_data = self.api.get_servers(self.download.gid)
                server_rows: list[list[str]] = []
                for s in servers_data:
                    for s_item in s.get("servers", []):
                        server_rows.append([
                            str(s.get("index", "1")),
                            s_item.get("uri", ""),
                            f"{int(s_item.get('downloadSpeed', 0))/1024:.1f} KB/s",
                            str(s_item.get("currentConnection", 1)),
                        ])
                self.servers_table.delete_rows()
                self.servers_table.insert_rows("end", server_rows)
                self.servers_table.load_table_data()

        except Exception:
            pass
        finally:
            self.after(2000, self._poll_telemetry)
