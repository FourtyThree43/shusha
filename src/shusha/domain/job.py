"""Backend-neutral core Job aggregate entity."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from shusha.domain.acquisition import AcquisitionRequest
from shusha.domain.artifact import Artifact
from shusha.domain.capability import CapabilitySet
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import BackendId, CategoryId, JobGroupId, JobId
from shusha.domain.states import DownloadState, validate_transition
from shusha.domain.values import BitRate, ByteSize, Duration, Percentage


@dataclass(frozen=True, slots=True, kw_only=True)
class JobTimestamps:
    """Audit and lifecycle timestamps for a Job."""

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class JobProgress:
    """Progress and bandwidth measurement for a Job."""

    total_length: ByteSize | None = None
    completed_length: ByteSize = field(default_factory=lambda: ByteSize(0))
    download_speed: BitRate = field(default_factory=lambda: BitRate(0))
    upload_speed: BitRate = field(default_factory=lambda: BitRate(0))
    eta: Duration | None = None

    @property
    def percentage(self) -> Percentage:
        """Calculate progress percentage."""
        return Percentage.from_progress(self.completed_length, self.total_length)


@dataclass(frozen=True, slots=True, kw_only=True)
class Job:
    """Core backend-neutral execution aggregate entity."""

    id: JobId
    backend_id: BackendId
    name: str
    state: DownloadState = DownloadState.QUEUED
    group_id: JobGroupId | None = None
    source: DownloadSource | None = None
    request: AcquisitionRequest | None = None
    progress: JobProgress = field(default_factory=JobProgress)
    timestamps: JobTimestamps = field(default_factory=JobTimestamps)
    outputs: list[Artifact] = field(default_factory=list)
    capabilities: CapabilitySet = field(default_factory=CapabilitySet)
    category_id: CategoryId | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    backend_data: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None

    @property
    def is_active(self) -> bool:
        return self.state == DownloadState.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.state == DownloadState.COMPLETED

    @property
    def is_paused(self) -> bool:
        return self.state == DownloadState.PAUSED

    @property
    def is_failed(self) -> bool:
        return self.state == DownloadState.FAILED

    def transition_to(self, new_state: DownloadState) -> Job:
        """Enforce domain invariants and state transition rules."""
        validate_transition(self.state, new_state)
        new_timestamps = self.timestamps

        if new_state == DownloadState.ACTIVE and not self.timestamps.started_at:
            new_timestamps = replace(self.timestamps, started_at=datetime.now(UTC))
        elif new_state in (
            DownloadState.COMPLETED,
            DownloadState.FAILED,
            DownloadState.REMOVED,
        ):
            new_timestamps = replace(self.timestamps, finished_at=datetime.now(UTC))

        return replace(self, state=new_state, timestamps=new_timestamps)
