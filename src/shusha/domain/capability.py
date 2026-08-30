"""Typed Capability domain model and vocabulary."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum


class Capability(StrEnum):
    """Machine-readable backend and engine capability vocabulary."""

    BASIC_DOWNLOAD = "basic_download"
    PAUSE_RESUME = "pause_resume"
    CANCEL = "cancel"
    RETRY = "retry"
    QUEUE = "queue"
    SCHEDULING = "scheduling"
    MULTIPLE_SOURCES = "multiple_sources"
    SEGMENTATION = "segmentation"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SFTP = "sftp"
    TORRENT = "torrent"
    MAGNET = "magnet"
    METALINK = "metalink"
    TORRENT_FILES = "torrent_files"
    TORRENT_PEERS = "torrent_peers"
    TORRENT_TRACKERS = "torrent_trackers"
    SERVER_STATUS = "server_status"
    PIECE_STATUS = "piece_status"
    CHECKSUM = "checksum"
    COOKIES = "cookies"
    AUTHENTICATION = "authentication"
    PROXY = "proxy"
    RATE_LIMIT = "rate_limit"
    FILE_SELECTION = "file_selection"
    INPUT_FILE = "input_file"
    SESSION_SAVE = "session_save"
    REMOTE_RPC = "remote_rpc"
    MEDIA_EXTRACTION = "media_extraction"
    FORMAT_SELECTION = "format_selection"
    PLAYLIST = "playlist"
    SUBTITLES = "subtitles"
    METADATA = "metadata"
    POST_PROCESSING = "post_processing"


@dataclass(frozen=True, slots=True)
class CapabilitySet:
    """Immutable set of capabilities queryable by application and frontends."""

    capabilities: frozenset[Capability] = field(default_factory=frozenset)

    @classmethod
    def from_iterable(cls, items: Iterable[Capability | str]) -> CapabilitySet:
        """Construct a CapabilitySet from an iterable of strings or enums."""
        normalized: set[Capability] = set()
        for item in items:
            if isinstance(item, Capability):
                normalized.add(item)
            elif isinstance(item, str):
                normalized.add(Capability(item.lower()))
        return cls(capabilities=frozenset(normalized))

    def has(self, capability: Capability | str) -> bool:
        """Check if a single capability is supported."""
        if isinstance(capability, str):
            try:
                cap = Capability(capability.lower())
            except ValueError:
                return False
        else:
            cap = capability
        return cap in self.capabilities

    def supports_all(self, required: Iterable[Capability | str]) -> bool:
        """Check if all specified capabilities are supported."""
        return all(self.has(c) for c in required)

    def supports_any(self, candidates: Iterable[Capability | str]) -> bool:
        """Check if at least one of the specified capabilities is supported."""
        return any(self.has(c) for c in candidates)

    def to_list(self) -> list[str]:
        """Serialize capabilities as a sorted list of strings."""
        return sorted(c.value for c in self.capabilities)

    def __contains__(self, item: Capability | str) -> bool:
        return self.has(item)

    def __len__(self) -> int:
        return len(self.capabilities)

    def __iter__(self):
        return iter(self.capabilities)
