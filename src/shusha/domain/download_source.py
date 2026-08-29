"""
Download source / URI representation in the Shusha 2 domain.
"""

from dataclasses import dataclass
from enum import StrEnum

from shusha.domain.values import Uri


class SourceStatus(StrEnum):
    USED = "USED"
    WAITING = "WAITING"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class DownloadSource:
    """Represents a source URI and its current connection state."""

    uri: Uri
    status: SourceStatus = SourceStatus.WAITING

    @classmethod
    def from_str(cls, raw_uri: str, status_str: str = "WAITING") -> DownloadSource:
        uri = Uri.parse(raw_uri)
        try:
            status = SourceStatus(status_str.upper())
        except ValueError:
            status = SourceStatus.WAITING
        return cls(uri=uri, status=status)
