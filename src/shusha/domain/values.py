"""
Immutable Value Objects for the Shusha 2 Domain.
Pure domain logic: no GUI, RPC, or database dependencies.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

from shusha.domain.errors import ValueObjectValidationError


@dataclass(frozen=True, slots=True, order=True)
class ByteSize:
    """Represents an exact number of bytes with formatting and unit parsing."""

    bytes: int

    def __post_init__(self) -> None:
        if self.bytes < 0:
            raise ValueObjectValidationError(
                f"ByteSize cannot be negative: {self.bytes}"
            )

    @classmethod
    def from_str(cls, val: str) -> Self:
        """Parse unit strings like '10M', '1.5 GiB', '500 KB', '1024'."""
        clean = val.strip().upper()
        if not clean:
            return cls(0)

        match = re.match(r"^([0-9.]+)\s*([A-Z]*)$", clean)
        if not match:
            raise ValueObjectValidationError(f"Invalid byte size string: '{val}'")

        number_str, unit = match.groups()
        try:
            num = float(number_str)
        except ValueError as err:
            raise ValueObjectValidationError(
                f"Invalid numeric value in byte size: '{val}'"
            ) from err

        multipliers: dict[str, int] = {
            "": 1,
            "B": 1,
            "K": 1024,
            "KB": 1000,
            "KIB": 1024,
            "M": 1024 * 1024,
            "MB": 1000 * 1000,
            "MIB": 1024 * 1024,
            "G": 1024 * 1024 * 1024,
            "GB": 1000 * 1000 * 1000,
            "GIB": 1024 * 1024 * 1024,
            "T": 1024 * 1024 * 1024 * 1024,
            "TB": 1000 * 1000 * 1000 * 1000,
            "TIB": 1024 * 1024 * 1024 * 1024,
        }

        mult = multipliers.get(unit, 1)
        return cls(int(num * mult))

    def human_readable(self, binary: bool = True) -> str:
        """Format as human-readable string (e.g. '15.4 MiB' or '16.1 MB')."""
        if self.bytes == 0:
            return "0 B"

        base = 1024.0 if binary else 1000.0
        units = (
            ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
            if binary
            else ["B", "KB", "MB", "GB", "TB", "PB"]
        )

        exponent = min(int(math.log(self.bytes, base)), len(units) - 1)
        val = self.bytes / (base**exponent)
        return f"{val:.2f} {units[exponent]}"

    def __add__(self, other: ByteSize | int) -> ByteSize:
        other_bytes = other.bytes if isinstance(other, ByteSize) else other
        return ByteSize(self.bytes + other_bytes)

    def __sub__(self, other: ByteSize | int) -> ByteSize:
        other_bytes = other.bytes if isinstance(other, ByteSize) else other
        return ByteSize(max(0, self.bytes - other_bytes))


@dataclass(frozen=True, slots=True, order=True)
class BitRate:
    """Represents throughput / data transfer speed in bytes per second."""

    bytes_per_sec: int

    def __post_init__(self) -> None:
        if self.bytes_per_sec < 0:
            raise ValueObjectValidationError(
                f"BitRate cannot be negative: {self.bytes_per_sec}"
            )

    @classmethod
    def from_str(cls, val: str) -> Self:
        clean = val.strip().upper().replace("/S", "").replace("/SEC", "")
        size = ByteSize.from_str(clean)
        return cls(size.bytes)

    def human_readable(self) -> str:
        """Format as speed string (e.g. '2.45 MiB/s')."""
        size_str = ByteSize(self.bytes_per_sec).human_readable(binary=True)
        return f"{size_str}/s"


@dataclass(frozen=True, slots=True, order=True)
class Duration:
    """Represents a duration in seconds (e.g. for ETA or runtime)."""

    seconds: int

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueObjectValidationError(
                f"Duration cannot be negative: {self.seconds}"
            )

    @classmethod
    def calculate_eta(
        cls, completed_bytes: ByteSize, total_bytes: ByteSize | None, speed: BitRate
    ) -> Duration | None:
        """Calculate estimated time of arrival."""
        if (
            total_bytes is None
            or total_bytes.bytes <= completed_bytes.bytes
            or speed.bytes_per_sec <= 0
        ):
            return None
        remaining = total_bytes.bytes - completed_bytes.bytes
        sec = int(remaining / speed.bytes_per_sec)
        return cls(sec)

    def human_readable(self) -> str:
        """Format as HH:MM:SS or DDd HH:MM:SS."""
        d = self.seconds // 86400
        h = (self.seconds % 86400) // 3600
        m = (self.seconds % 3600) // 60
        s = self.seconds % 60
        if d > 0:
            return f"{d}d {h:02d}:{m:02d}:{s:02d}"
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


@dataclass(frozen=True, slots=True, order=True)
class Percentage:
    """Represents a ratio/percentage between 0.0% and 100.0%."""

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            # Clamp or validate
            object.__setattr__(self, "value", max(0.0, min(100.0, self.value)))

    @classmethod
    def from_progress(
        cls, completed: ByteSize | int, total: ByteSize | int | None
    ) -> Percentage:
        c = completed.bytes if isinstance(completed, ByteSize) else completed
        t = total.bytes if isinstance(total, ByteSize) else (total or 0)
        if t <= 0:
            return cls(0.0)
        ratio = min(1.0, max(0.0, c / t)) * 100.0
        return cls(round(ratio, 2))

    def human_readable(self) -> str:
        return f"{self.value:.1f}%"


@dataclass(frozen=True, slots=True)
class Port:
    """Network port number between 1 and 65535."""

    number: int

    def __post_init__(self) -> None:
        if not (1 <= self.number <= 65535):
            raise ValueObjectValidationError(
                f"Invalid network port: {self.number} (must be 1-65535)"
            )


@dataclass(frozen=True, slots=True)
class Uri:
    """Validated Uniform Resource Identifier (HTTP, HTTPS, FTP, SFTP, Magnet)."""

    raw_uri: str
    scheme: str
    host: str | None
    path: str

    @classmethod
    def parse(cls, raw: str) -> Self:
        clean = raw.strip()
        if not clean:
            raise ValueObjectValidationError("URI string cannot be empty.")

        if clean.startswith("magnet:?"):
            return cls(raw_uri=clean, scheme="magnet", host=None, path="")

        parsed = urlparse(clean)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https", "ftp", "sftp", "magnet"):
            raise ValueObjectValidationError(
                f"Unsupported URI scheme: '{scheme}' in '{clean}'"
            )

        return cls(raw_uri=clean, scheme=scheme, host=parsed.hostname, path=parsed.path)


@dataclass(frozen=True, slots=True)
class Checksum:
    """Cryptographic checksum with hash algorithm and hex digest."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        algo = self.algorithm.strip().lower()
        clean_digest = self.digest.strip().lower()
        object.__setattr__(self, "algorithm", algo)
        object.__setattr__(self, "digest", clean_digest)

        if not re.match(r"^[0-9a-fA-F]+$", clean_digest):
            raise ValueObjectValidationError(
                f"Invalid hexadecimal checksum digest: '{self.digest}'"
            )


@dataclass(frozen=True, slots=True)
class Bitfield:
    """Bitfield representing completed pieces in a BitTorrent / multi-part download."""

    hex_string: str

    @property
    def total_pieces(self) -> int:
        return len(self.hex_string) * 4

    @property
    def completed_pieces(self) -> int:
        count = 0
        for char in self.hex_string:
            val = int(char, 16)
            count += bin(val).count("1")
        return count

    @property
    def completion_percentage(self) -> Percentage:
        total = self.total_pieces
        if total == 0:
            return Percentage(0.0)
        return Percentage.from_progress(self.completed_pieces, total)

    def is_piece_complete(self, piece_index: int) -> bool:
        """Check if a specific piece index is marked completed in the bitfield."""
        char_index = piece_index // 4
        if char_index >= len(self.hex_string):
            return False
        bit_offset = 3 - (piece_index % 4)
        val = int(self.hex_string[char_index], 16)
        return bool((val >> bit_offset) & 1)
