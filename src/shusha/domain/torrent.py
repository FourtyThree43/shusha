"""
BitTorrent domain models for Shusha 2.
"""

from dataclasses import dataclass
from datetime import datetime

from shusha.domain.download_file import DownloadFile
from shusha.domain.values import ByteSize


@dataclass(frozen=True, slots=True)
class Tracker:
    """BitTorrent tracker tier and announce URL."""

    url: str
    tier: int = 0


@dataclass(frozen=True, slots=True)
class TorrentMeta:
    """Parsed BitTorrent metadata."""

    info_hash: str
    name: str
    piece_length: ByteSize
    num_pieces: int
    total_length: ByteSize
    files: list[DownloadFile]
    trackers: list[Tracker]
    comment: str | None = None
    creation_date: datetime | None = None
    created_by: str | None = None
