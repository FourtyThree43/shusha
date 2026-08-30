"""Acquisition Inbox and lifecycle manager (E09-I05).

Stores, tracks, deduplicates, and manages state transitions for all incoming
acquisition items through detected, inspecting, resolved, awaiting_user, accepted,
ignored, expired, and failed states.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
from datetime import UTC, datetime
from typing import Protocol

from shusha.domain.acquisition import (
    AcquisitionRequest,
    AcquisitionStatus,
    DetectedKind,
    SourceKind,
)
from shusha.domain.events import (
    AcquisitionDetectedEvent,
    AcquisitionResolvedEvent,
    DomainEvent,
)
from shusha.domain.identifiers import AcquisitionId, BackendId

logger = logging.getLogger(__name__)


class EventBusProtocol(Protocol):
    """Protocol for event notification subscribers."""

    def publish(self, event: DomainEvent) -> None: ...


# Terminal / Inactive statuses
TERMINAL_STATUSES = frozenset(
    {
        AcquisitionStatus.ACCEPTED,
        AcquisitionStatus.IGNORED,
        AcquisitionStatus.EXPIRED,
    }
)

VALID_STATUS_TRANSITIONS: dict[AcquisitionStatus, frozenset[AcquisitionStatus]] = {
    AcquisitionStatus.DETECTED: frozenset(
        {
            AcquisitionStatus.INSPECTING,
            AcquisitionStatus.RESOLVED,
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.ACCEPTED,
            AcquisitionStatus.IGNORED,
            AcquisitionStatus.EXPIRED,
            AcquisitionStatus.FAILED,
        }
    ),
    AcquisitionStatus.INSPECTING: frozenset(
        {
            AcquisitionStatus.RESOLVED,
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.ACCEPTED,
            AcquisitionStatus.FAILED,
            AcquisitionStatus.IGNORED,
            AcquisitionStatus.EXPIRED,
        }
    ),
    AcquisitionStatus.RESOLVED: frozenset(
        {
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.ACCEPTED,
            AcquisitionStatus.IGNORED,
            AcquisitionStatus.EXPIRED,
            AcquisitionStatus.FAILED,
        }
    ),
    AcquisitionStatus.AWAITING_USER: frozenset(
        {
            AcquisitionStatus.ACCEPTED,
            AcquisitionStatus.IGNORED,
            AcquisitionStatus.EXPIRED,
            AcquisitionStatus.FAILED,
        }
    ),
    AcquisitionStatus.FAILED: frozenset(
        {
            AcquisitionStatus.DETECTED,
            AcquisitionStatus.INSPECTING,
            AcquisitionStatus.RESOLVED,
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.IGNORED,
            AcquisitionStatus.EXPIRED,
        }
    ),
    AcquisitionStatus.IGNORED: frozenset(
        {
            AcquisitionStatus.DETECTED,
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.ACCEPTED,
        }
    ),
    AcquisitionStatus.EXPIRED: frozenset(
        {
            AcquisitionStatus.DETECTED,
            AcquisitionStatus.AWAITING_USER,
            AcquisitionStatus.ACCEPTED,
        }
    ),
    AcquisitionStatus.ACCEPTED: frozenset(),
}


class AcquisitionInbox:
    """Thread-safe acquisition inbox managing request lifecycles and transitions."""

    def __init__(
        self,
        event_bus: EventBusProtocol | None = None,
        deduplicate: bool = True,
    ) -> None:
        self._items: dict[AcquisitionId, AcquisitionRequest] = {}
        self._raw_input_index: dict[str, AcquisitionId] = {}
        self._lock = threading.RLock()
        self._event_bus = event_bus
        self._deduplicate = deduplicate

    def add(self, request: AcquisitionRequest) -> AcquisitionRequest:
        """Add a newly detected acquisition request to the inbox with deduplication."""
        with self._lock:
            if self._deduplicate:
                clean_input = request.raw_input.strip()
                existing_id = self._raw_input_index.get(clean_input)
                if existing_id and existing_id in self._items:
                    existing = self._items[existing_id]
                    # If existing request is still active, return it without duplicate insertion
                    if existing.status not in TERMINAL_STATUSES:
                        logger.debug(
                            "Deduplicated incoming acquisition request for %s",
                            clean_input,
                        )
                        return existing

            self._items[request.id] = request
            self._raw_input_index[request.raw_input.strip()] = request.id

        # Publish event
        if self._event_bus:
            self._event_bus.publish(
                AcquisitionDetectedEvent(
                    acquisition_id=request.id,
                    source_kind=str(request.source_kind.value),
                    raw_input=request.raw_input,
                )
            )

        return request

    def get(self, acquisition_id: AcquisitionId) -> AcquisitionRequest | None:
        """Retrieve an acquisition item by ID."""
        with self._lock:
            return self._items.get(acquisition_id)

    def list_all(
        self,
        status: AcquisitionStatus | None = None,
        source_kind: SourceKind | None = None,
    ) -> list[AcquisitionRequest]:
        """List acquisition requests matching optional status and source kind filters."""
        with self._lock:
            items = list(self._items.values())

        if status is not None:
            items = [i for i in items if i.status == status]
        if source_kind is not None:
            items = [i for i in items if i.source_kind == source_kind]

        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def list_active(self) -> list[AcquisitionRequest]:
        """List all active, non-terminal acquisition candidates."""
        with self._lock:
            items = [
                i for i in self._items.values() if i.status not in TERMINAL_STATUSES
            ]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def update_status(
        self,
        acquisition_id: AcquisitionId,
        status: AcquisitionStatus,
        preferred_backend: BackendId | None = None,
        detected_kind: DetectedKind | None = None,
        metadata_updates: dict[str, str] | None = None,
    ) -> AcquisitionRequest:
        """Transition an acquisition request to a new status with validation."""
        with self._lock:
            item = self._items.get(acquisition_id)
            if item is None:
                raise KeyError(
                    f"Acquisition request '{acquisition_id}' not found in inbox."
                )

            # Validate state transition
            allowed = VALID_STATUS_TRANSITIONS.get(item.status, frozenset())
            if status != item.status and status not in allowed:
                raise ValueError(
                    f"Invalid acquisition transition from '{item.status}' to '{status}'."
                )

            # Update metadata
            new_metadata = dict(item.metadata)
            if metadata_updates:
                new_metadata.update(metadata_updates)

            updated = dataclasses.replace(
                item,
                status=status,
                preferred_backend=preferred_backend or item.preferred_backend,
                detected_kind=detected_kind or item.detected_kind,
                metadata=new_metadata,
            )
            self._items[acquisition_id] = updated

        # Emit resolved event if status transitioned to resolved or accepted
        if self._event_bus and status in (
            AcquisitionStatus.RESOLVED,
            AcquisitionStatus.ACCEPTED,
        ):
            self._event_bus.publish(
                AcquisitionResolvedEvent(
                    acquisition_id=updated.id,
                    detected_kind=str(updated.detected_kind.value),
                    preferred_backend=updated.preferred_backend,
                )
            )

        return updated

    def accept(
        self,
        acquisition_id: AcquisitionId | str,
        backend_id: BackendId | None = None,
    ) -> AcquisitionRequest:
        """Mark an acquisition item as accepted for download execution."""
        from shusha.domain.identifiers import make_acquisition_id

        aid = make_acquisition_id(str(acquisition_id))
        return self.update_status(
            acquisition_id=aid,
            status=AcquisitionStatus.ACCEPTED,
            preferred_backend=backend_id,
        )

    def ignore(self, acquisition_id: AcquisitionId | str) -> AcquisitionRequest:
        """Dismiss or ignore an acquisition request."""
        from shusha.domain.identifiers import make_acquisition_id

        aid = make_acquisition_id(str(acquisition_id))
        return self.update_status(
            acquisition_id=aid,
            status=AcquisitionStatus.IGNORED,
        )

    def retry(self, acquisition_id: AcquisitionId) -> AcquisitionRequest:
        """Retry a failed acquisition item."""
        return self.update_status(
            acquisition_id=acquisition_id,
            status=AcquisitionStatus.DETECTED,
        )

    def expire_older_than(self, max_age_seconds: float) -> list[AcquisitionRequest]:
        """Expire unaccepted items older than max_age_seconds."""
        now = datetime.now(UTC)
        expired: list[AcquisitionRequest] = []

        with self._lock:
            for item in list(self._items.values()):
                if item.status in (
                    AcquisitionStatus.DETECTED,
                    AcquisitionStatus.INSPECTING,
                    AcquisitionStatus.RESOLVED,
                    AcquisitionStatus.AWAITING_USER,
                ):
                    age = (now - item.created_at).total_seconds()
                    if age > max_age_seconds:
                        upd = dataclasses.replace(
                            item, status=AcquisitionStatus.EXPIRED
                        )
                        self._items[item.id] = upd
                        expired.append(upd)

        return expired

    def remove(self, acquisition_id: AcquisitionId) -> bool:
        """Remove an acquisition item from the inbox."""
        with self._lock:
            item = self._items.pop(acquisition_id, None)
            if item:
                self._raw_input_index.pop(item.raw_input.strip(), None)
                return True
            return False

    def clear(self) -> None:
        """Clear all acquisition items."""
        with self._lock:
            self._items.clear()
            self._raw_input_index.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
