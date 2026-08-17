"""This module defines the Stats dataclass.

It holds information retrieved with the `get_global_stat` method of the client.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shusha.models.utilities import format_speed


@dataclass(slots=True)
class Stats:
    """Dataclass holding global aria2 statistics with defensive parsing."""

    download_speed: int = 0
    upload_speed: int = 0
    num_active: int = 0
    num_waiting: int = 0
    num_stopped: int = 0
    num_stopped_total: int = 0

    def __init__(
        self,
        struct_or_download_speed: dict[str, Any] | int = 0,
        upload_speed: int = 0,
        num_active: int = 0,
        num_waiting: int = 0,
        num_stopped: int = 0,
        num_stopped_total: int = 0,
    ) -> None:
        if isinstance(struct_or_download_speed, dict):
            struct = struct_or_download_speed
            self.download_speed = int(struct.get("downloadSpeed", 0) or 0)
            self.upload_speed = int(struct.get("uploadSpeed", 0) or 0)
            self.num_active = int(struct.get("numActive", 0) or 0)
            self.num_waiting = int(struct.get("numWaiting", 0) or 0)
            self.num_stopped = int(struct.get("numStopped", 0) or 0)
            self.num_stopped_total = int(struct.get("numStoppedTotal", 0) or 0)
        else:
            self.download_speed = int(struct_or_download_speed or 0)
            self.upload_speed = int(upload_speed or 0)
            self.num_active = int(num_active or 0)
            self.num_waiting = int(num_waiting or 0)
            self.num_stopped = int(num_stopped or 0)
            self.num_stopped_total = int(num_stopped_total or 0)

    @classmethod
    def from_dict(cls, struct: dict[str, Any] | None) -> Stats:
        """Create a Stats instance safely from a raw RPC dictionary."""
        if not struct or not isinstance(struct, dict):
            return cls()
        return cls(struct)

    def download_speed_string(self, human_readable: bool = True) -> str:
        """Return the download speed as formatted string."""
        if human_readable:
            return format_speed(self.download_speed)
        return f"{self.download_speed} B/s"

    def upload_speed_string(self, human_readable: bool = True) -> str:
        """Return the upload speed as formatted string."""
        if human_readable:
            return format_speed(self.upload_speed)
        return f"{self.upload_speed} B/s"
