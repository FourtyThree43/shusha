"""
Download file model representing individual files within a multi-file or torrent download.
"""

from dataclasses import dataclass

from shusha.domain.download_source import DownloadSource
from shusha.domain.values import ByteSize, Percentage


@dataclass(frozen=True, slots=True)
class DownloadFile:
    """Represents a file inside a download."""

    index: int
    path: str
    length: ByteSize
    completed_length: ByteSize
    selected: bool
    uris: list[DownloadSource]

    @property
    def progress(self) -> Percentage:
        return Percentage.from_progress(self.completed_length, self.length)

    @property
    def is_completed(self) -> bool:
        return (
            self.length.bytes > 0 and self.completed_length.bytes >= self.length.bytes
        )
