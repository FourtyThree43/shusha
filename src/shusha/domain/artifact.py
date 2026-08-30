"""Domain model for execution outputs and artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from shusha.domain.identifiers import ArtifactId, JobId
from shusha.domain.values import ByteSize, Checksum


class ArtifactKind(StrEnum):
    """Classification of output artifact."""

    FILE = "file"
    DIRECTORY = "directory"
    PLAYLIST = "playlist"
    COLLECTION = "collection"
    TORRENT_PAYLOAD = "torrent_payload"
    STREAM = "stream"


class ArtifactStatus(StrEnum):
    """Integrity and availability status of an artifact."""

    PENDING = "pending"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True, kw_only=True)
class Artifact:
    """Backend-neutral execution output artifact."""

    id: ArtifactId
    job_id: JobId
    kind: ArtifactKind = ArtifactKind.FILE
    name: str
    path: Path | str
    size: ByteSize | None = None
    checksum: Checksum | None = None
    status: ArtifactStatus = ArtifactStatus.PENDING
    mime_type: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def is_verified(self) -> bool:
        return self.status == ArtifactStatus.VERIFIED

    @property
    def is_available(self) -> bool:
        """Check if local file or directory currently exists."""
        p = Path(self.path)
        return p.exists()
