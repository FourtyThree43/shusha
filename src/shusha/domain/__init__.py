"""
Shusha 2 Domain Layer.
Pure, decoupled business abstractions with zero external dependencies.
"""

from shusha.domain.category import Category, CategoryRule
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
    CategoryId,
    ConnectionId,
    DownloadId,
    Gid,
    HistoryId,
    PeerId,
    ProfileId,
    SessionId,
    TaskId,
    make_category_id,
    make_download_id,
    make_gid,
)
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
    "BitRate",
    "Bitfield",
    "ByteSize",
    "Category",
    "CategoryChangedEvent",
    "CategoryId",
    "CategoryRule",
    "CategoryRuleConflictError",
    "Checksum",
    "ConnectionId",
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
    "MetalinkFile",
    "MetalinkResource",
    "Peer",
    "PeerId",
    "Percentage",
    "Port",
    "ProfileId",
    "ScheduleWindow",
    "Server",
    "SessionId",
    "SourceStatus",
    "TaskId",
    "TorrentMeta",
    "Tracker",
    "Uri",
    "ValueObjectValidationError",
    "can_transition",
    "make_category_id",
    "make_download_id",
    "make_gid",
    "validate_transition",
]
