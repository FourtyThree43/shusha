"""
BitTorrent Creation Dialog for Shusha 2.
Generates standard .torrent files using pure Python hashing and bencoding.
"""

import hashlib
import time
import tkinter as tk
from collections.abc import Mapping
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, ClassVar

import ttkbootstrap as tb

from shusha.presentation.components.base import BaseDialog, BaseFrame


def bencode(val: Any) -> bytes:
    """Encode Python objects into standard BitTorrent bencoded bytes."""
    if isinstance(val, int):
        return f"i{val}e".encode("ascii")
    if isinstance(val, str):
        b = val.encode("utf-8")
        return f"{len(b)}:".encode("ascii") + b
    if isinstance(val, bytes):
        return f"{len(val)}:".encode("ascii") + val
    if isinstance(val, list):
        encoded_items = b"".join(bencode(item) for item in val)
        return b"l" + encoded_items + b"e"
    if isinstance(val, (dict, Mapping)):
        # Keys must be sorted strings
        sorted_keys = sorted(str(k) for k in val)
        encoded_dict = b""
        for k in sorted_keys:
            encoded_dict += bencode(k) + bencode(val[k])
        return b"d" + encoded_dict + b"e"
    raise TypeError(f"Cannot bencode object of type {type(val)}")


def generate_torrent_file(
    source_path: Path,
    piece_size: int,
    trackers: list[str],
    comment: str = "",
    created_by: str = "Shusha/2.0",
    is_private: bool = False,
) -> bytes:
    """Generate .torrent bencoded file bytes for single file or directory."""
    pieces = bytearray()

    if source_path.is_file():
        total_length = source_path.stat().st_size
        with open(source_path, "rb") as f:
            while chunk := f.read(piece_size):
                pieces.extend(hashlib.sha1(chunk).digest())

        info_dict: dict[str, Any] = {
            "name": source_path.name,
            "piece length": piece_size,
            "pieces": bytes(pieces),
            "length": total_length,
        }
    elif source_path.is_dir():
        file_entries: list[dict[str, Any]] = []
        # Walk directory
        all_files = sorted(
            [p for p in source_path.rglob("*") if p.is_file()],
            key=lambda p: str(p.relative_to(source_path)),
        )

        current_piece = bytearray()
        for f_path in all_files:
            rel_parts = list(f_path.relative_to(source_path).parts)
            f_size = f_path.stat().st_size
            file_entries.append({"length": f_size, "path": rel_parts})

            with open(f_path, "rb") as f:
                while True:
                    needed = piece_size - len(current_piece)
                    chunk = f.read(needed)
                    if not chunk:
                        break
                    current_piece.extend(chunk)
                    if len(current_piece) == piece_size:
                        pieces.extend(hashlib.sha1(current_piece).digest())
                        current_piece.clear()

        if current_piece:
            pieces.extend(hashlib.sha1(current_piece).digest())

        info_dict = {
            "name": source_path.name,
            "piece length": piece_size,
            "pieces": bytes(pieces),
            "files": file_entries,
        }
    else:
        raise FileNotFoundError(f"Invalid source path: {source_path}")

    if is_private:
        info_dict["private"] = 1

    torrent_data: dict[str, Any] = {
        "info": info_dict,
        "creation date": int(time.time()),
        "created by": created_by,
    }

    if trackers:
        torrent_data["announce"] = trackers[0]
        if len(trackers) > 1:
            torrent_data["announce-list"] = [[t] for t in trackers]

    if comment:
        torrent_data["comment"] = comment

    return bencode(torrent_data)


class CreateTorrentDialog(BaseDialog):
    """Modal dialog for creating and exporting new .torrent files."""

    PIECE_SIZES: ClassVar[list[tuple[str, int]]] = [
        ("32 KiB", 32 * 1024),
        ("64 KiB", 64 * 1024),
        ("128 KiB", 128 * 1024),
        ("256 KiB", 256 * 1024),
        ("512 KiB", 512 * 1024),
        ("1 MiB", 1024 * 1024),
        ("2 MiB", 2 * 1024 * 1024),
        ("4 MiB", 4 * 1024 * 1024),
        ("8 MiB", 8 * 1024 * 1024),
        ("16 MiB", 16 * 1024 * 1024),
    ]

    def __init__(self, parent: tk.Tk | tk.Toplevel) -> None:
        super().__init__(
            parent=parent,
            title="Create .torrent File — Shusha",
            min_width=600,
            min_height=480,
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_frame = BaseFrame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        # Source
        lbl_src = tb.Label(main_frame, text="Select Source File or Folder:")
        lbl_src.pack(anchor="w", pady=(0, 2))

        src_frame = BaseFrame(main_frame)
        src_frame.pack(fill="x", pady=(0, 8))

        self.txt_source = tb.Entry(src_frame)
        self.txt_source.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_file = tb.Button(
            src_frame,
            text="File...",
            bootstyle="secondary",
            command=self._on_browse_file,
        )
        btn_file.pack(side="left", padx=2)

        btn_dir = tb.Button(
            src_frame,
            text="Folder...",
            bootstyle="secondary",
            command=self._on_browse_dir,
        )
        btn_dir.pack(side="left")

        # Trackers
        lbl_trackers = tb.Label(main_frame, text="Trackers (one URL per line):")
        lbl_trackers.pack(anchor="w", pady=(4, 2))

        self.txt_trackers = tk.Text(main_frame, height=5, font=("TkFixedFont", 9))
        self.txt_trackers.pack(fill="x", pady=(0, 8))
        self.txt_trackers.insert("1.0", "udp://tracker.opentrackr.org:1337/announce\n")

        # Piece size & Private
        opt_frame = BaseFrame(main_frame)
        opt_frame.pack(fill="x", pady=(0, 8))
        opt_frame.columnconfigure(1, weight=1)

        lbl_piece = tb.Label(opt_frame, text="Piece Size:")
        lbl_piece.grid(row=0, column=0, sticky="w", pady=2)

        self.cmb_piece = tb.Combobox(
            opt_frame,
            values=[label for label, _ in self.PIECE_SIZES],
            state="readonly",
        )
        self.cmb_piece.set("1 MiB")
        self.cmb_piece.grid(row=0, column=1, sticky="w", padx=4, pady=2)

        self.var_private = tk.BooleanVar(value=False)
        chk_priv = tb.Checkbutton(
            opt_frame,
            text="Private Torrent (disable DHT / PEX)",
            variable=self.var_private,
            bootstyle="round-toggle",
        )
        chk_priv.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        # Comment
        lbl_comm = tb.Label(opt_frame, text="Comment:")
        lbl_comm.grid(row=2, column=0, sticky="w", pady=2)
        self.txt_comment = tb.Entry(opt_frame)
        self.txt_comment.grid(row=2, column=1, sticky="ew", padx=4, pady=2)

        # Buttons
        btn_box = BaseFrame(main_frame)
        btn_box.pack(fill="x", pady=(8, 0))

        btn_create = tb.Button(
            btn_box,
            text="Create Torrent...",
            bootstyle="primary",
            command=self._on_create,
        )
        btn_create.pack(side="right", padx=(4, 0))

        btn_cancel = tb.Button(
            btn_box, text="Cancel", bootstyle="secondary-outline", command=self.destroy
        )
        btn_cancel.pack(side="right")

    def _on_browse_file(self) -> None:
        p = filedialog.askopenfilename(title="Select Source File", parent=self)
        if p:
            self.txt_source.delete(0, "end")
            self.txt_source.insert(0, p)

    def _on_browse_dir(self) -> None:
        p = filedialog.askdirectory(title="Select Source Folder", parent=self)
        if p:
            self.txt_source.delete(0, "end")
            self.txt_source.insert(0, p)

    def _on_create(self) -> None:
        src_str = self.txt_source.get().strip()
        if not src_str:
            messagebox.showwarning(
                "Missing Source", "Please select a source file or folder", parent=self
            )
            return

        source_path = Path(src_str)
        if not source_path.exists():
            messagebox.showerror(
                "Not Found", f"Source path does not exist: {source_path}", parent=self
            )
            return

        # Output .torrent save path
        out_path = filedialog.asksaveasfilename(
            title="Save .torrent File",
            defaultextension=".torrent",
            filetypes=[("Torrent Files", "*.torrent")],
            initialfile=f"{source_path.name}.torrent",
            parent=self,
        )
        if not out_path:
            return

        # Find piece size bytes
        piece_size_bytes = 1024 * 1024
        for label, sz in self.PIECE_SIZES:
            if label == self.cmb_piece.get():
                piece_size_bytes = sz
                break

        trackers = [
            t.strip()
            for t in self.txt_trackers.get("1.0", "end").splitlines()
            if t.strip()
        ]

        try:
            torrent_bytes = generate_torrent_file(
                source_path=source_path,
                piece_size=piece_size_bytes,
                trackers=trackers,
                comment=self.txt_comment.get().strip(),
                is_private=self.var_private.get(),
            )
            Path(out_path).write_bytes(torrent_bytes)
            messagebox.showinfo(
                "Torrent Created", f"Successfully created:\n{out_path}", parent=self
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error Creating Torrent", str(e), parent=self)
