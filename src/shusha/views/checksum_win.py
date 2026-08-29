"""File Checksum & Integrity Verifier Dialog for Shusha-DM."""

from __future__ import annotations

import hashlib
import threading
import tkinter as tk
import zlib
from pathlib import Path
from tkinter import filedialog
from typing import Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


class ChecksumWindow(ttk.Toplevel):
    """Modal dialog for computing and comparing cryptographic hashes of downloaded files."""

    def __init__(
        self,
        master: Any = None,
        initial_file: str | Path | None = None,
        compute_on_open: bool = True,
    ) -> None:
        super().__init__(
            title="File Hash & Integrity Verifier - Shusha",
            master=master,
            size=(640, 480),
            resizable=(True, True),
        )
        self.minsize(560, 400)
        self.config(padx=12, pady=12)

        self.file_path_var = tk.StringVar(value=str(initial_file or ""))
        self.expected_hash_var = tk.StringVar(value="")
        self.status_msg_var = tk.StringVar(
            value="Select a file and click Compute Hashes"
        )

        self.hash_vars = {
            "MD5": tk.StringVar(value=""),
            "SHA-1": tk.StringVar(value=""),
            "SHA-256": tk.StringVar(value=""),
            "SHA-512": tk.StringVar(value=""),
            "CRC32": tk.StringVar(value=""),
        }

        self._build_ui()
        if compute_on_open and initial_file and Path(initial_file).is_file():
            self._start_hashing()

    def _build_ui(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # File selection
        file_lf = ttk.Labelframe(container, text="Target File", padding=10)
        file_lf.pack(fill=tk.X, pady=(0, 10))

        f_row = ttk.Frame(file_lf)
        f_row.pack(fill=tk.X)
        ttk.Entry(f_row, textvariable=self.file_path_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(
            f_row,
            text="Browse...",
            command=self._browse_file,
            bootstyle="secondary-outline",
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            f_row, text="Compute", command=self._start_hashing, bootstyle="primary"
        ).pack(side=tk.LEFT, padx=2)

        # Calculated Hashes
        hash_lf = ttk.Labelframe(container, text="Computed Hashes", padding=10)
        hash_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        grid = ttk.Frame(hash_lf)
        grid.pack(fill=tk.BOTH, expand=True)

        for idx, (algo, var) in enumerate(self.hash_vars.items()):
            ttk.Label(
                grid, text=f"{algo}:", width=10, font=("TkDefaultFont", 9, "bold")
            ).grid(row=idx, column=0, sticky=tk.W, pady=3)
            ttk.Entry(grid, textvariable=var, state="readonly").grid(
                row=idx, column=1, sticky=tk.EW, pady=3, padx=5
            )
            ttk.Button(
                grid,
                text="Copy",
                command=lambda v=var: self._copy_val(v),
                bootstyle="secondary-outline",
                width=6,
            ).grid(row=idx, column=2, sticky=tk.E, pady=3)

        grid.columnconfigure(1, weight=1)

        # Verification Compare
        ver_lf = ttk.Labelframe(container, text="Verification Check", padding=10)
        ver_lf.pack(fill=tk.X, pady=(0, 10))

        v_row = ttk.Frame(ver_lf)
        v_row.pack(fill=tk.X)
        ttk.Label(v_row, text="Expected Hash:").pack(side=tk.LEFT, padx=(0, 5))
        e_entry = ttk.Entry(v_row, textvariable=self.expected_hash_var)
        e_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        e_entry.bind("<KeyRelease>", self._check_match)
        ttk.Button(
            v_row, text="Verify", command=self._check_match, bootstyle="info-outline"
        ).pack(side=tk.RIGHT)

        self.status_label = ttk.Label(
            container,
            textvariable=self.status_msg_var,
            font=("TkDefaultFont", 9, "italic"),
        )
        self.status_label.pack(side=tk.LEFT, pady=5)

        ttk.Button(
            container,
            text="Close",
            command=self.destroy,
            bootstyle="secondary",
            width=10,
        ).pack(side=tk.RIGHT, pady=5)

    def _browse_file(self) -> None:
        selected = filedialog.askopenfilename(title="Select File to Hash", parent=self)
        if selected:
            self.file_path_var.set(selected)
            self._start_hashing()

    def _copy_val(self, var: tk.StringVar) -> None:
        val = var.get().strip()
        if val:
            self.clipboard_clear()
            self.clipboard_append(val)

    def _start_hashing(self) -> None:
        path_str = self.file_path_var.get().strip()
        if not path_str or not Path(path_str).is_file():
            self.status_msg_var.set("Selected path is not a valid file.")
            return

        self.status_msg_var.set("Computing hashes in background...")
        threading.Thread(
            target=self._compute_bg, args=(Path(path_str),), daemon=True
        ).start()

    def compute_hashes_sync(self, target: Path) -> dict[str, str]:
        """Compute all cryptographic hashes synchronously and populate UI variables."""
        md5_h = hashlib.md5()
        sha1_h = hashlib.sha1()
        sha256_h = hashlib.sha256()
        sha512_h = hashlib.sha512()
        crc = 0

        with open(target, "rb") as f:
            while chunk := f.read(64 * 1024):
                md5_h.update(chunk)
                sha1_h.update(chunk)
                sha256_h.update(chunk)
                sha512_h.update(chunk)
                crc = zlib.crc32(chunk, crc)

        res = {
            "MD5": md5_h.hexdigest(),
            "SHA-1": sha1_h.hexdigest(),
            "SHA-256": sha256_h.hexdigest(),
            "SHA-512": sha512_h.hexdigest(),
            "CRC32": f"{crc & 0xFFFFFFFF:08X}",
        }
        for algo, val in res.items():
            if algo in self.hash_vars:
                self.hash_vars[algo].set(val)
        self.status_msg_var.set("Hash computation complete.")
        self._check_match()
        return res

    def _compute_bg(self, target: Path) -> None:
        try:
            self.compute_hashes_sync(target)
        except Exception as e:
            logger.log(f"Error computing checksum: {e}", level="error")
            self.status_msg_var.set(f"Hash calculation error: {e}")

    def _check_match(self, event: Any = None) -> None:
        expected = self.expected_hash_var.get().strip().lower()
        if not expected:
            return

        for algo, var in self.hash_vars.items():
            calculated = var.get().strip().lower()
            if calculated and calculated == expected:
                self.status_msg_var.set(f" MATCH! Verified against {algo} hash.")
                self.status_label.config(bootstyle="success")
                return

        self.status_msg_var.set(" MISMATCH: Does not match any computed hash.")
        self.status_label.config(bootstyle="danger")
