"""
Domain events for the Shusha 2 application.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from shusha.domain.identifiers import CategoryId, DownloadId, Gid
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base domain event with UTC timestamp."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


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
    category_id: CategoryId
    action: str  # 'CREATED', 'UPDATED', 'DELETED'
