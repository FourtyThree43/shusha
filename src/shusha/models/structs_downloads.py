"""
This module defines the BitTorrent, File, and Download classes.
They hold structured information about torrents, files, and downloads in aria2c.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shusha.models.logger import LoggerService
from shusha.models.utilities import (
    bool_or_value,
    format_eta,
    format_size,
    format_speed,
)

if TYPE_CHECKING:
    from shusha.controller.api import ShushaAPI as Api
    from shusha.models.structs_options import Options

logger = LoggerService(__name__)


@dataclass(slots=True)
class BitTorrent:
    """Information retrieved from a torrent structure."""

    _struct: dict[str, Any] = field(default_factory=dict)

    def __init__(self, struct: dict[str, Any] | None = None) -> None:
        self._struct = struct or {}

    def __str__(self) -> str:
        return str((self.info or {}).get("name", ""))

    @property
    def announce_list(self) -> list[list[str]] | None:
        return self._struct.get("announceList")

    @property
    def comment(self) -> str | None:
        return self._struct.get("comment")

    @property
    def creation_date(self) -> datetime:
        ts = self._struct.get("creationDate", 0)
        return datetime.fromtimestamp(int(ts or 0), tz=timezone.utc)

    @property
    def mode(self) -> str | None:
        return self._struct.get("mode")

    @property
    def info(self) -> dict[str, Any] | None:
        return self._struct.get("info")


@dataclass(slots=True)
class File:
    """Information about a download's file."""

    _struct: dict[str, Any] = field(default_factory=dict)

    def __init__(self, struct: dict[str, Any] | None = None) -> None:
        self._struct = struct or {}

    def __str__(self) -> str:
        return str(self.path)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, File):
            return self.path == other.path
        return NotImplemented

    @property
    def index(self) -> int:
        return int(self._struct.get("index", 1) or 1)

    @property
    def path(self) -> Path:
        return Path(self._struct.get("path", "") or "")

    @property
    def is_metadata(self) -> bool:
        return str(self.path).startswith("[METADATA]")

    @property
    def length(self) -> int:
        return int(self._struct.get("length", 0) or 0)

    def length_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_size(self.length)
        return f"{self.length} B"

    @property
    def completed_length(self) -> int:
        return int(self._struct.get("completedLength", 0) or 0)

    def completed_length_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_size(self.completed_length)
        return f"{self.completed_length} B"

    @property
    def selected(self) -> bool:
        return bool_or_value(self._struct.get("selected", True))

    @property
    def uris(self) -> list[dict[str, Any]]:
        return self._struct.get("uris", [])


class Download:
    """Structured representation of an aria2 download task."""

    def __init__(self, api: Api | None, struct: dict[str, Any] | None) -> None:
        self.api = api
        self._struct: dict[str, Any] = struct or {}
        self._files: list[File] = []
        self._root_files_paths: list[Path] = []
        self._bittorrent: BitTorrent | None = None
        self._name: str = ""
        self._options: Options | None = None
        self._followed_by: list[Download] | None = None
        self._following: Download | None = None
        self._belongs_to: Download | None = None

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Download):
            return self.gid == other.gid
        return NotImplemented

    def update(self) -> None:
        """Update internal values of the download from the remote client."""
        if self.api and self.gid:
            try:
                self._struct = self.api.client.tell_status(self.gid) or {}
            except Exception as e:
                logger.log(f"Failed to update download {self.gid}: {e}", level="debug")

        self._files = []
        self._name = ""
        self._bittorrent = None
        self._followed_by = None
        self._following = None
        self._belongs_to = None
        self._options = None

    @property
    def live(self) -> Download:
        self.update()
        return self

    @property
    def name(self) -> str:
        """Return the name of the download safely without indexing crashes."""
        if not self._name:
            if (
                self.bittorrent
                and self.bittorrent.info
                and self.bittorrent.info.get("name")
            ):
                self._name = str(self.bittorrent.info["name"])
            elif self.files and len(self.files) > 0:
                first_file = self.files[0]
                if first_file.is_metadata:
                    self._name = str(first_file.path)
                elif first_file.path and str(first_file.path) not in ("", "."):
                    try:
                        file_path = str(first_file.path.absolute())
                        dir_path = str(self.dir.absolute())
                        if file_path.startswith(dir_path):
                            start_pos = len(dir_path) + 1
                            parts = Path(file_path[start_pos:]).parts
                            self._name = parts[0] if parts else first_file.path.name
                        else:
                            self._name = first_file.path.name
                    except Exception:
                        self._name = first_file.path.name
                elif first_file.uris and len(first_file.uris) > 0:
                    first_uri = first_file.uris[0].get("uri", "")
                    self._name = (
                        first_uri.split("/")[-1] if "/" in first_uri else first_uri
                    )

            if not self._name:
                followed = self._struct.get("followedBy")
                if followed and isinstance(followed, list) and len(followed) > 0:
                    self._name = str(followed[0])
                else:
                    self._name = str(self.gid or "Download")

        return self._name

    @property
    def control_file_path(self) -> Path:
        return self.dir / f"{self.name}.aria2"

    @property
    def root_files_paths(self) -> list[Path]:
        if not self._root_files_paths:
            paths: list[Path] = []
            for file in self.files:
                if file.is_metadata:
                    continue
                try:
                    relative_path = file.path.relative_to(self.dir)
                    path = self.dir / relative_path.parts[0]
                    if path not in paths:
                        paths.append(path)
                except Exception:
                    if file.path not in paths:
                        paths.append(file.path)
            self._root_files_paths = paths
        return self._root_files_paths

    @property
    def options(self) -> Options | None:
        if self._options is None and self.api:
            self.update_options()
        return self._options

    @options.setter
    def options(self, value: Options) -> None:
        self._options = value

    def update_options(self) -> None:
        if self.api:
            try:
                opts_list = self.api.get_options(downloads=[self])
                if opts_list:
                    self._options = opts_list[0]
            except Exception as e:
                logger.log(
                    f"Failed to fetch options for {self.gid}: {e}", level="debug"
                )

    @property
    def gid(self) -> str:
        return str(self._struct.get("gid", "") or "")

    @property
    def status(self) -> str:
        return str(self._struct.get("status", "unknown") or "unknown")

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_waiting(self) -> bool:
        return self.status == "waiting"

    @property
    def is_paused(self) -> bool:
        return self.status == "paused"

    @property
    def is_complete(self) -> bool:
        return self.status == "complete"

    @property
    def is_removed(self) -> bool:
        return self.status == "removed"

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    @property
    def has_failed(self) -> bool:
        return self.is_error

    @property
    def total_length(self) -> int:
        return int(self._struct.get("totalLength", 0) or 0)

    def total_length_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_size(self.total_length)
        return f"{self.total_length} B"

    @property
    def completed_length(self) -> int:
        return int(self._struct.get("completedLength", 0) or 0)

    def completed_length_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_size(self.completed_length)
        return f"{self.completed_length} B"

    @property
    def upload_length(self) -> int:
        return int(self._struct.get("uploadLength", 0) or 0)

    def upload_length_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_size(self.upload_length)
        return f"{self.upload_length} B"

    @property
    def download_speed(self) -> int:
        return int(self._struct.get("downloadSpeed", 0) or 0)

    def download_speed_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_speed(self.download_speed)
        return f"{self.download_speed} B/s"

    @property
    def upload_speed(self) -> int:
        return int(self._struct.get("uploadSpeed", 0) or 0)

    def upload_speed_string(self, human_readable: bool = True) -> str:
        if human_readable:
            return format_speed(self.upload_speed)
        return f"{self.upload_speed} B/s"

    @property
    def info_hash(self) -> str | None:
        return self._struct.get("infoHash")

    @property
    def num_seeders(self) -> int:
        return int(self._struct.get("numSeeders", 0) or 0)

    @property
    def seeder(self) -> bool:
        return bool_or_value(self._struct.get("seeder", False))

    @property
    def connections(self) -> int:
        return int(self._struct.get("connections", 0) or 0)

    @property
    def error_code(self) -> str | None:
        return self._struct.get("errorCode")

    @property
    def error_message(self) -> str | None:
        return self._struct.get("errorMessage")

    @property
    def followed_by_ids(self) -> list[str]:
        return self._struct.get("followedBy", [])

    @property
    def following_id(self) -> str | None:
        return self._struct.get("following")

    @property
    def belongs_to_id(self) -> str | None:
        return self._struct.get("belongsTo")

    @property
    def dir(self) -> Path:
        return Path(self._struct.get("dir", ".") or ".")

    @property
    def files(self) -> list[File]:
        if not self._files:
            raw_files = self._struct.get("files", [])
            self._files = [File(f) for f in raw_files]
        return self._files

    @property
    def bittorrent(self) -> BitTorrent | None:
        if self._bittorrent is None and "bittorrent" in self._struct:
            self._bittorrent = BitTorrent(self._struct["bittorrent"])
        return self._bittorrent

    @property
    def bitfield(self) -> str:
        """Hex-encoded bitfield of completed pieces."""
        return str(self._struct.get("bitfield", "") or "")

    @property
    def num_pieces(self) -> int:
        """Total number of pieces in the download."""
        return int(self._struct.get("numPieces", 0) or 0)

    @property
    def piece_length(self) -> int:
        """Byte length of each piece."""
        return int(self._struct.get("pieceLength", 0) or 0)

    @property
    def pieces_bool_array(self) -> list[bool]:
        """Decode the hex bitfield into an array of boolean flags for each piece."""
        hex_str = self.bitfield
        if not hex_str:
            if self.is_complete and self.num_pieces > 0:
                return [True] * self.num_pieces
            return [False] * max(0, self.num_pieces)

        bits: list[bool] = []
        for char in hex_str:
            try:
                val = int(char, 16)
                for shift in (3, 2, 1, 0):
                    bits.append(bool((val >> shift) & 1))
            except ValueError:
                continue

        if self.num_pieces > 0:
            return bits[: self.num_pieces]
        return bits

    @property
    def num_completed_pieces(self) -> int:
        """Number of verified/completed pieces."""
        arr = self.pieces_bool_array
        return sum(1 for b in arr if b)

    @property
    def verified_length(self) -> int:
        return int(self._struct.get("verifiedLength", 0) or 0)

    @property
    def verify_integrity_pending(self) -> bool:
        return bool_or_value(self._struct.get("verifyIntegrityPending", False))

    @property
    def progress(self) -> float:
        if self.total_length > 0:
            return round((self.completed_length / self.total_length) * 100, 2)
        return 0.0

    def progress_string(self) -> str:
        return f"{self.progress:.2f}%"

    @property
    def eta(self) -> timedelta:
        if self.download_speed > 0 and self.total_length > self.completed_length:
            seconds = (self.total_length - self.completed_length) / self.download_speed
            return timedelta(seconds=int(seconds))
        return timedelta()

    def eta_string(self) -> str:
        return format_eta(self.eta)

    def move_up(self, pos: int = 1) -> int:
        return self.api.move_up(self, pos) if self.api else -1

    def move_down(self, pos: int = 1) -> int:
        return self.api.move_down(self, pos) if self.api else -1

    def move_to_top(self) -> int:
        return self.api.move_to_top(self) if self.api else -1

    def move_to_bottom(self) -> int:
        return self.api.move_to_bottom(self) if self.api else -1

    def remove(self, force: bool = False, files: bool = False) -> bool:
        if self.api:
            return bool(self.api.remove(self.gid, force=force))
        return False

    def pause(self, force: bool = False) -> bool:
        if self.api:
            return bool(self.api.pause(self.gid, force=force))
        return False

    def resume(self) -> bool:
        if self.api:
            return bool(self.api.resume(self.gid))
        return False

    def purge(self) -> bool:
        if self.api:
            return self.api.client.remove_download_result(self.gid) == "OK"
        return False

    def move_files(self, to_directory: str | Path, force: bool = False) -> bool:
        if self.api:
            return bool(self.api.move_files([self], to_directory, force)[0])
        return False

    def copy_files(self, to_directory: str | Path, force: bool = False) -> bool:
        if self.api:
            return bool(self.api.copy_files([self], to_directory, force)[0])
        return False
