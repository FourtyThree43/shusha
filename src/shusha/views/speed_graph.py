"""Transfer Speed Graph Canvas widget.

This widget plots a real-time historical graph of download and upload speeds over the
last 60 seconds (inspired by Motrix and Persepolis bandwidth charts).
"""

from __future__ import annotations

import collections
import tkinter as tk
from typing import Any

import ttkbootstrap as ttk


class SpeedGraphWidget(ttk.Frame):
    """Real-time speed graph plotting download (green) and upload (blue) rates."""

    def __init__(
        self,
        master: Any,
        max_points: int = 60,
        height: int = 120,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self.max_points = max_points
        self.graph_height = height

        self.colors = ttk.Style().colors

        # History ring buffers: store speed in bytes/sec
        self.down_history: collections.deque[int] = collections.deque(
            [0] * max_points, maxlen=max_points
        )
        self.up_history: collections.deque[int] = collections.deque(
            [0] * max_points, maxlen=max_points
        )

        # Header Legend
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=tk.X, pady=(0, 2))

        self.down_label = ttk.Label(
            self.header_frame,
            text="▼ DL: 0 B/s",
            font=("TkDefaultFont", 8, "bold"),
            foreground=self.colors.success,
        )
        self.down_label.pack(side=tk.LEFT, padx=4)

        self.up_label = ttk.Label(
            self.header_frame,
            text="▲ UL: 0 B/s",
            font=("TkDefaultFont", 8, "bold"),
            foreground=self.colors.info,
        )
        self.up_label.pack(side=tk.LEFT, padx=8)

        self.peak_label = ttk.Label(
            self.header_frame,
            text="Peak: 0 B/s",
            font=("TkDefaultFont", 8),
            foreground=self.colors.secondary,
        )
        self.peak_label.pack(side=tk.RIGHT, padx=4)

        # Canvas
        self.canvas = tk.Canvas(
            self,
            height=self.graph_height,
            bg=self.colors.bg,
            highlightthickness=1,
            highlightbackground=self.colors.border,
        )
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def add_data_point(self, down_speed_bytes: int, up_speed_bytes: int) -> None:
        """Append a new data point and refresh the graph."""
        self.down_history.append(down_speed_bytes)
        self.up_history.append(up_speed_bytes)

        # Format labels
        self.down_label.config(text=f"▼ DL: {self._format_speed(down_speed_bytes)}")
        self.up_label.config(text=f"▲ UL: {self._format_speed(up_speed_bytes)}")

        max_speed = max(max(self.down_history), max(self.up_history), 1)
        self.peak_label.config(text=f"Peak: {self._format_speed(max_speed)}")

        self.redraw()

    @staticmethod
    def _format_speed(speed: int) -> str:
        if speed >= 1048576:
            return f"{speed / 1048576:.1f} MB/s"
        elif speed >= 1024:
            return f"{speed / 1024:.1f} KB/s"
        return f"{speed} B/s"

    def redraw(self) -> None:
        """Redraw sparkline paths on canvas."""
        self.canvas.delete("all")
        w = max(50, self.canvas.winfo_width())
        h = max(30, self.canvas.winfo_height())

        max_speed = max(max(self.down_history), max(self.up_history), 1024)

        # Draw grid lines
        grid_color = self.colors.border
        for y_pct in (0.25, 0.5, 0.75):
            y = int(h * y_pct)
            self.canvas.create_line(0, y, w, y, fill=grid_color, dash=(2, 4))

        # Helper to compute points
        step_x = w / (self.max_points - 1)

        def make_points(history: collections.deque[int]) -> list[float]:
            pts: list[float] = []
            for idx, val in enumerate(history):
                x = idx * step_x
                y = h - 2 - (val / max_speed) * (h - 8)
                pts.extend([x, y])
            return pts

        # Plot upload line (blue)
        up_pts = make_points(self.up_history)
        if len(up_pts) >= 4:
            self.canvas.create_line(
                up_pts,
                fill=self.colors.info,
                width=2,
                smooth=True,
            )

        # Plot download line (green)
        down_pts = make_points(self.down_history)
        if len(down_pts) >= 4:
            self.canvas.create_line(
                down_pts,
                fill=self.colors.success,
                width=2,
                smooth=True,
            )
