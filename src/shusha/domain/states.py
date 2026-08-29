"""
Download state machine and state transition rules for Shusha 2.
"""

from enum import StrEnum

from shusha.domain.errors import InvalidStateTransitionError


class DownloadState(StrEnum):
    """Authoritative download states."""

    NEW = "NEW"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    RESUMING = "RESUMING"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REMOVING = "REMOVING"
    REMOVED = "REMOVED"
    SEEDING = "SEEDING"


# Valid state transitions graph
VALID_TRANSITIONS: dict[DownloadState, set[DownloadState]] = {
    DownloadState.NEW: {
        DownloadState.QUEUED,
        DownloadState.STARTING,
        DownloadState.PAUSED,
        DownloadState.FAILED,
        DownloadState.REMOVED,
    },
    DownloadState.QUEUED: {
        DownloadState.STARTING,
        DownloadState.ACTIVE,
        DownloadState.PAUSED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
        DownloadState.FAILED,
    },
    DownloadState.STARTING: {
        DownloadState.ACTIVE,
        DownloadState.PAUSING,
        DownloadState.PAUSED,
        DownloadState.FAILED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.ACTIVE: {
        DownloadState.PAUSING,
        DownloadState.PAUSED,
        DownloadState.COMPLETING,
        DownloadState.COMPLETED,
        DownloadState.SEEDING,
        DownloadState.FAILED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.PAUSING: {
        DownloadState.PAUSED,
        DownloadState.FAILED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.PAUSED: {
        DownloadState.RESUMING,
        DownloadState.QUEUED,
        DownloadState.ACTIVE,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
        DownloadState.FAILED,
    },
    DownloadState.RESUMING: {
        DownloadState.ACTIVE,
        DownloadState.PAUSED,
        DownloadState.FAILED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.COMPLETING: {
        DownloadState.COMPLETED,
        DownloadState.SEEDING,
        DownloadState.FAILED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.COMPLETED: {
        DownloadState.SEEDING,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.SEEDING: {
        DownloadState.PAUSING,
        DownloadState.PAUSED,
        DownloadState.COMPLETED,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
        DownloadState.FAILED,
    },
    DownloadState.FAILED: {
        DownloadState.QUEUED,
        DownloadState.STARTING,
        DownloadState.REMOVING,
        DownloadState.REMOVED,
    },
    DownloadState.REMOVING: {
        DownloadState.REMOVED,
    },
    DownloadState.REMOVED: set(),
}


def can_transition(current: DownloadState, target: DownloadState) -> bool:
    """Check whether a transition between two states is valid."""
    if current == target:
        return True
    return target in VALID_TRANSITIONS.get(current, set())


def validate_transition(current: DownloadState, target: DownloadState) -> None:
    """Validate transition and raise InvalidStateTransitionError if illegal."""
    if not can_transition(current, target):
        raise InvalidStateTransitionError(current.value, target.value)
