"""Shusha Domain Layer.

Pure, decoupled business abstractions with zero external dependencies.
"""

from shusha.domain.acquisition import (
    AcquisitionRequest,
    AcquisitionStatus,
    DetectedKind,
    Provenance,
    SelectionPolicy,
    SourceKind,
)
from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.category import Category, CategoryRule
from shusha.domain.credentials import (
    CredentialKind,
    CredentialReference,
    CredentialScope,
)
from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource, SourceStatus
from shusha.domain.errors import (
    CategoryRuleConflictError,
    DomainError,
    DownloadNotFoundError,
    InvalidIdentifierError,
    InvalidStateTransitionError,
    ValueObjectValidationError,
)
from shusha.domain.events import (
    CategoryChangedEvent,
    DomainEvent,
    DownloadCompletedEvent,
    DownloadCreatedEvent,
    DownloadFailedEvent,
    DownloadProgressEvent,
    DownloadRemovedEvent,
    DownloadStateChangedEvent,
)
from shusha.domain.identifiers import (
    AcquisitionId,
    ArtifactId,
    BackendId,
    CategoryId,
    ConnectionId,
    CredentialId,
    DownloadId,
    Gid,
    HistoryId,
    JobGroupId,
    JobId,
    PeerId,
    ProfileId,
    SessionId,
    TaskId,
    make_acquisition_id,
    make_artifact_id,
    make_backend_id,
    make_category_id,
    make_credential_id,
    make_download_id,
    make_gid,
    make_job_group_id,
    make_job_id,
)
from shusha.domain.job import Job, JobProgress, JobTimestamps
from shusha.domain.job_group import JobGroup, JobGroupKind
from shusha.domain.metalink import MetalinkFile, MetalinkResource
from shusha.domain.peer import Peer
from shusha.domain.queue import DownloadQueue
from shusha.domain.scheduler import ScheduleWindow
from shusha.domain.server import Server
from shusha.domain.states import DownloadState, can_transition, validate_transition
from shusha.domain.statistics import GlobalStatistics
from shusha.domain.torrent import TorrentMeta, Tracker
from shusha.domain.values import (
    Bitfield,
    BitRate,
    ByteSize,
    Checksum,
    Duration,
    Percentage,
    Port,
    Uri,
)

__all__ = [
    "AcquisitionId",
    "AcquisitionRequest",
    "AcquisitionStatus",
    "Artifact",
    "ArtifactId",
    "ArtifactKind",
    "ArtifactStatus",
    "BackendId",
    "BitRate",
    "Bitfield",
    "ByteSize",
    "Capability",
    "CapabilitySet",
    "Category",
    "CategoryChangedEvent",
    "CategoryId",
    "CategoryRule",
    "CategoryRuleConflictError",
    "Checksum",
    "ConnectionId",
    "CredentialId",
    "CredentialKind",
    "CredentialReference",
    "CredentialScope",
    "DetectedKind",
    "DomainError",
    "DomainEvent",
    "Download",
    "DownloadCompletedEvent",
    "DownloadCreatedEvent",
    "DownloadFailedEvent",
    "DownloadFile",
    "DownloadId",
    "DownloadNotFoundError",
    "DownloadProgressEvent",
    "DownloadQueue",
    "DownloadRemovedEvent",
    "DownloadSource",
    "DownloadState",
    "DownloadStateChangedEvent",
    "Duration",
    "Gid",
    "GlobalStatistics",
    "HistoryId",
    "InvalidIdentifierError",
    "InvalidStateTransitionError",
    "Job",
    "JobGroup",
    "JobGroupId",
    "JobGroupKind",
    "JobId",
    "JobProgress",
    "JobTimestamps",
    "MetalinkFile",
    "MetalinkResource",
    "Peer",
    "PeerId",
    "Percentage",
    "Port",
    "ProfileId",
    "Provenance",
    "ScheduleWindow",
    "SelectionPolicy",
    "Server",
    "SessionId",
    "SourceKind",
    "SourceStatus",
    "TaskId",
    "TorrentMeta",
    "Tracker",
    "Uri",
    "ValueObjectValidationError",
    "can_transition",
    "make_acquisition_id",
    "make_artifact_id",
    "make_backend_id",
    "make_category_id",
    "make_credential_id",
    "make_download_id",
    "make_gid",
    "make_job_group_id",
    "make_job_id",
    "validate_transition",
]
