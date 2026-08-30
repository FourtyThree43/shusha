"""Domain and application events for Shusha."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from shusha.domain.artifact import Artifact
from shusha.domain.capability import CapabilitySet
from shusha.domain.identifiers import (
    AcquisitionId,
    BackendId,
    CategoryId,
    DownloadId,
    Gid,
    JobId,
)
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base domain event with UTC timestamp."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# --- Job Events ---


@dataclass(frozen=True, slots=True, kw_only=True)
class JobCreatedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId
    name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class JobStartedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId


@dataclass(frozen=True, slots=True, kw_only=True)
class JobStateChangedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId
    previous_state: DownloadState
    new_state: DownloadState


@dataclass(frozen=True, slots=True, kw_only=True)
class JobProgressChangedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId
    completed_bytes: ByteSize
    total_bytes: ByteSize | None
    download_speed: BitRate
    upload_speed: BitRate


@dataclass(frozen=True, slots=True, kw_only=True)
class JobPausedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId


@dataclass(frozen=True, slots=True, kw_only=True)
class JobResumedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId


@dataclass(frozen=True, slots=True, kw_only=True)
class JobFailedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId
    error_message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class JobCompletedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True, kw_only=True)
class JobCancelledEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId


@dataclass(frozen=True, slots=True, kw_only=True)
class JobRemovedEvent(DomainEvent):
    job_id: JobId
    backend_id: BackendId


# --- Backend Events ---


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendConnectedEvent(DomainEvent):
    backend_id: BackendId
    version: str = ""
    capabilities: CapabilitySet = field(default_factory=CapabilitySet)


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendDisconnectedEvent(DomainEvent):
    backend_id: BackendId
    reason: str = ""


# --- Acquisition Events ---


@dataclass(frozen=True, slots=True, kw_only=True)
class AcquisitionDetectedEvent(DomainEvent):
    acquisition_id: AcquisitionId
    source_kind: str
    raw_input: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AcquisitionResolvedEvent(DomainEvent):
    acquisition_id: AcquisitionId
    detected_kind: str
    preferred_backend: BackendId | None = None


# --- Plugin Events ---


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginLoadedEvent(DomainEvent):
    plugin_id: str
    version: str
    capabilities: CapabilitySet = field(default_factory=CapabilitySet)


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginFailedEvent(DomainEvent):
    plugin_id: str
    error_message: str


# --- Scheduler Events ---


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerTriggeredEvent(DomainEvent):
    schedule_id: str
    job_id: JobId | None = None


# --- Legacy Download Events for Compatibility ---


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadCreatedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadStateChangedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    previous_state: DownloadState
    new_state: DownloadState


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadProgressEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    completed_bytes: ByteSize
    total_bytes: ByteSize | None
    download_speed: BitRate
    upload_speed: BitRate


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadCompletedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    total_bytes: ByteSize
    dest_path: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadFailedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    error_code: int
    error_message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadRemovedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid


@dataclass(frozen=True, slots=True, kw_only=True)
class CategoryChangedEvent(DomainEvent):
    download_id: DownloadId
    gid: Gid
    new_category_id: CategoryId | None
