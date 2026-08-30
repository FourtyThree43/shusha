"""Backend contract and protocol definitions (E05-I01)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from shusha.backends.options import BackendOptionSpec
from shusha.domain.capability import CapabilitySet
from shusha.domain.identifiers import BackendId, JobId
from shusha.domain.job import Job


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendIdentity:
    """Identity and metadata of a download backend engine."""

    id: BackendId
    name: str
    version: str = "1.0.0"
    description: str = ""
    vendor: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class BackendDiagnostics:
    """Health check and diagnostic snapshot for a backend."""

    healthy: bool = True
    uptime_seconds: float = 0.0
    active_jobs: int = 0
    details: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class BackendProtocol(Protocol):
    """Authoritative shared contract for all download backends."""

    @property
    def identity(self) -> BackendIdentity:
        """Return the identity descriptor of the backend."""
        ...

    @property
    def capabilities(self) -> CapabilitySet:
        """Return the immutable capability set supported by this backend."""
        ...

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize connections, sub-processes, or configuration."""
        ...

    def shutdown(self) -> None:
        """Gracefully terminate background processes and free resources."""
        ...

    def ping(self) -> bool:
        """Perform a liveness check and return True if healthy."""
        ...

    def submit_job(self, job: Job) -> Job:
        """Enqueue and start execution of a Job on the backend engine."""
        ...

    def pause_job(self, job_id: JobId) -> Job:
        """Pause an active job."""
        ...

    def resume_job(self, job_id: JobId) -> Job:
        """Resume a paused job."""
        ...

    def cancel_job(self, job_id: JobId) -> Job:
        """Stop/cancel a job."""
        ...

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        """Remove a job from engine management and optionally delete files."""
        ...

    def get_job_status(self, job_id: JobId) -> Job:
        """Retrieve the latest live state and progress of a Job."""
        ...

    def get_diagnostics(self) -> BackendDiagnostics:
        """Return diagnostic and operational health metrics."""
        ...

    def get_supported_options(self) -> list[BackendOptionSpec]:
        """Return list of supported backend-specific option specifications."""
        ...
