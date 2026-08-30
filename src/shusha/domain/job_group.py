"""Domain model for grouped jobs, batches, and playlists."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from shusha.domain.identifiers import JobGroupId, JobId
from shusha.domain.values import ByteSize, Percentage


class JobGroupKind(StrEnum):
    """Classification of job grouping."""

    BATCH = "batch"
    PLAYLIST = "playlist"
    COLLECTION = "collection"
    SEGMENTED = "segmented"


@dataclass(frozen=True, slots=True, kw_only=True)
class JobGroup:
    """Represents a collection of related jobs orchestrated as a unit."""

    id: JobGroupId
    name: str
    kind: JobGroupKind = JobGroupKind.BATCH
    job_ids: tuple[JobId, ...] = field(default_factory=tuple)
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_length: ByteSize | None = None
    completed_length: ByteSize = field(default_factory=lambda: ByteSize(0))
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def is_finished(self) -> bool:
        """Return true if all constituent jobs have finished."""
        if self.total_jobs == 0:
            return True
        return (self.completed_jobs + self.failed_jobs) >= self.total_jobs

    @property
    def progress(self) -> Percentage:
        """Calculate overall byte-level or count-level progress."""
        if self.total_length and self.total_length.bytes > 0:
            return Percentage.from_progress(self.completed_length, self.total_length)
        if self.total_jobs > 0:
            return Percentage(round((self.completed_jobs / self.total_jobs) * 100.0, 2))
        return Percentage(0.0)
