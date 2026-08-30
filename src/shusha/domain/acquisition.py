"""Domain model for acquisition requests and detection metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from shusha.domain.identifiers import AcquisitionId, BackendId


class SourceKind(StrEnum):
    """Source that introduced the acquisition item."""

    MANUAL = "manual"
    CLIPBOARD = "clipboard"
    BROWSER = "browser"
    DRAG_DROP = "drag_drop"
    CLI = "cli"
    TORRENT_FILE = "torrent_file"
    MAGNET = "magnet"
    METALINK = "metalink"
    LOCAL_FILE = "local_file"
    API = "api"


class DetectedKind(StrEnum):
    """Detected payload classification."""

    DIRECT_URL = "direct_url"
    MAGNET_URI = "magnet_uri"
    TORRENT_FILE = "torrent_file"
    METALINK_FILE = "metalink_file"
    MEDIA_STREAM = "media_stream"
    PLAYLIST_URL = "playlist_url"
    RAW_TEXT = "raw_text"
    UNKNOWN = "unknown"


class SelectionPolicy(StrEnum):
    """Routing policy for engine backend selection."""

    AUTOMATIC = "automatic"
    EXPLICIT = "explicit"
    RULE_BASED = "rule_based"


class AcquisitionStatus(StrEnum):
    """Lifecycle status in the acquisition pipeline and inbox."""

    DETECTED = "detected"
    INSPECTING = "inspecting"
    RESOLVED = "resolved"
    AWAITING_USER = "awaiting_user"
    ACCEPTED = "accepted"
    IGNORED = "ignored"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass(frozen=True, slots=True, kw_only=True)
class Provenance:
    """Audit and origin metadata for an acquisition request."""

    origin_url: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    source_application: str | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True, kw_only=True)
class AcquisitionRequest:
    """Unified representation of all input sources entering the system."""

    id: AcquisitionId
    source_kind: SourceKind
    raw_input: str
    detected_kind: DetectedKind = DetectedKind.UNKNOWN
    status: AcquisitionStatus = AcquisitionStatus.DETECTED
    metadata: dict[str, str] = field(default_factory=dict)
    preferred_backend: BackendId | None = None
    selection_policy: SelectionPolicy = SelectionPolicy.AUTOMATIC
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    provenance: Provenance = field(default_factory=Provenance)

    @property
    def is_resolved(self) -> bool:
        return self.status in (AcquisitionStatus.RESOLVED, AcquisitionStatus.ACCEPTED)
