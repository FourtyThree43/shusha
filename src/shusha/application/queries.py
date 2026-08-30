"""Frontend-independent application queries and QueryBus (E03-I02)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from shusha.domain.identifiers import BackendId, CategoryId, JobGroupId, JobId
from shusha.domain.states import DownloadState

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Query:
    """Base marker for all application queries."""


# --- Domain Queries ---


@dataclass(frozen=True, slots=True, kw_only=True)
class GetJobQuery(Query):
    job_id: JobId


@dataclass(frozen=True, slots=True, kw_only=True)
class ListJobsQuery(Query):
    state: DownloadState | None = None
    category_id: CategoryId | None = None
    backend_id: BackendId | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class GetJobGroupQuery(Query):
    group_id: JobGroupId


@dataclass(frozen=True, slots=True, kw_only=True)
class GetCapabilitiesQuery(Query):
    backend_id: BackendId | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GetGlobalStatisticsQuery(Query):
    backend_id: BackendId | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GetDiagnosticsQuery(Query):
    include_backends: bool = True
    include_plugins: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolveAcquisitionQuery(Query):
    raw_input: str
    preferred_backend: BackendId | None = None


# --- Query Bus ---

Q = TypeVar("Q", bound=Query)
R = TypeVar("R")


class QueryBus:
    """Dispatches application queries to their registered handler."""

    def __init__(self) -> None:
        self._handlers: dict[type[Query], Callable[[Any], Any]] = {}

    def register(self, query_type: type[Q], handler: Callable[[Q], R]) -> None:
        """Register a handler for a specific query type."""
        if query_type in self._handlers:
            logger.warning("Overriding existing query handler for %s", query_type)
        self._handlers[query_type] = handler

    def dispatch(self, query: Query) -> Any:
        """Dispatch query to its registered handler and return result."""
        handler = self._handlers.get(type(query))
        if not handler:
            raise KeyError(f"No handler registered for query: {type(query).__name__}")
        return handler(query)

    def has_handler(self, query_type: type[Query]) -> bool:
        """Check if a handler is registered for a query type."""
        return query_type in self._handlers
