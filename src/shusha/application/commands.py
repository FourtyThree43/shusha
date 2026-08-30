"""Frontend-independent application commands and CommandBus (E03-I01)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from shusha.domain.identifiers import BackendId, CategoryId, JobGroupId, JobId
from shusha.domain.job_group import JobGroupKind

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Command:
    """Base marker for all application commands."""


# --- Job Execution Commands ---


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateJobCommand(Command):
    name: str
    source_input: str
    backend_id: BackendId | None = None
    destination_dir: str | None = None
    options: dict[str, str] = field(default_factory=dict)
    category_id: CategoryId | None = None
    group_id: JobGroupId | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class StartJobCommand(Command):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class PauseJobCommand(Command):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class ResumeJobCommand(Command):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelJobCommand(Command):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class RemoveJobCommand(Command):
    job_id: JobId
    delete_files: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class RetryJobCommand(Command):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateJobGroupCommand(Command):
    name: str
    kind: JobGroupKind = JobGroupKind.BATCH
    job_ids: tuple[JobId, ...] = field(default_factory=tuple)


# --- Command Bus ---

C = TypeVar("C", bound=Command)
R = TypeVar("R")


class CommandBus:
    """Dispatches application commands to their registered handler."""

    def __init__(self) -> None:
        self._handlers: dict[type[Command], Callable[[Any], Any]] = {}

    def register(self, command_type: type[C], handler: Callable[[C], R]) -> None:
        """Register a handler for a specific command type."""
        if command_type in self._handlers:
            logger.warning("Overriding existing command handler for %s", command_type)
        self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> Any:
        """Dispatch command to its registered handler and return result."""
        handler = self._handlers.get(type(command))
        if not handler:
            raise KeyError(
                f"No handler registered for command: {type(command).__name__}"
            )
        return handler(command)

    def has_handler(self, command_type: type[Command]) -> bool:
        """Check if a handler is registered for a command type."""
        return command_type in self._handlers
