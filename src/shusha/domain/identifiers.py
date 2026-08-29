"""
Strongly typed domain identifiers for Shusha 2.
"""

from typing import NewType

Gid = NewType("Gid", str)
DownloadId = NewType("DownloadId", str)
CategoryId = NewType("CategoryId", str)
ProfileId = NewType("ProfileId", str)
HistoryId = NewType("HistoryId", str)
TaskId = NewType("TaskId", str)
SessionId = NewType("SessionId", str)
ConnectionId = NewType("ConnectionId", str)
PeerId = NewType("PeerId", str)


def make_gid(val: str) -> Gid:
    """Create and validate an aria2 16-character hex GID."""
    clean = val.strip()
    if not clean:
        raise ValueError("GID cannot be empty.")
    return Gid(clean)


def make_download_id(val: str) -> DownloadId:
    """Create a domain download identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("DownloadId cannot be empty.")
    return DownloadId(clean)


def make_category_id(val: str) -> CategoryId:
    """Create a category identifier."""
    clean = val.strip().lower()
    if not clean:
        raise ValueError("CategoryId cannot be empty.")
    return CategoryId(clean)
