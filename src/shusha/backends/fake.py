"""Deterministic in-memory Fake Backend for tests and decoupled frontends (Epic E06)."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from shusha.backends.contract import (
    BackendDiagnostics,
    BackendIdentity,
    BackendProtocol,
)
from shusha.backends.errors import (
    BackendConnectionError,
    BackendExecutionError,
    BackendJobNotFoundError,
)
from shusha.backends.options import (
    BackendOptionSpec,
    OptionMutability,
    OptionScope,
    OptionType,
)
from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.events import (
    DomainEvent,
    JobCompletedEvent,
    JobFailedEvent,
    JobPausedEvent,
    JobProgressChangedEvent,
    JobResumedEvent,
    JobStartedEvent,
)
from shusha.domain.identifiers import (
    JobId,
    make_artifact_id,
    make_backend_id,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Duration

logger = logging.getLogger(__name__)


class FakeBackend(BackendProtocol):
    """Full-featured deterministic in-memory backend simulator."""

    def __init__(
        self,
        backend_id: str = "fake",
        name: str = "Fake In-Memory Simulator",
        capabilities: CapabilitySet | None = None,
        event_callback: Any | None = None,
    ) -> None:
        self._identity = BackendIdentity(
            id=make_backend_id(backend_id),
            name=name,
            version="1.0.0",
            description="High-fidelity deterministic simulator for frontend and integration tests",
            vendor="Shusha Core",
        )
        self._capabilities = (
            capabilities
            if capabilities is not None
            else CapabilitySet.from_iterable(list(Capability))
        )
        self._jobs: dict[JobId, Job] = {}
        self._is_online = True
        self._fail_next_submission: str | None = None
        self._event_callback = event_callback
        self._initialized = False

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize simulator."""
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown simulator."""
        self._initialized = False

    def ping(self) -> bool:
        """Liveness check."""
        return self._is_online and self._initialized

    def set_online(self, online: bool) -> None:
        """Simulate backend connection loss or recovery."""
        self._is_online = online

    def set_fail_next_submission(self, error_message: str | None) -> None:
        """Configure the backend to fail the next submit_job call."""
        self._fail_next_submission = error_message

    def submit_job(self, job: Job) -> Job:
        """Submit a job and immediately transition to ACTIVE."""
        if not self.ping():
            raise BackendConnectionError(
                "FakeBackend is offline or uninitialized", backend_id=self.identity.id
            )

        if self._fail_next_submission:
            err = self._fail_next_submission
            self._fail_next_submission = None
            raise BackendExecutionError(err, backend_id=self.identity.id)

        active_job = job.transition_to(DownloadState.ACTIVE)
        self._jobs[active_job.id] = active_job
        self._emit(JobStartedEvent(job_id=active_job.id, backend_id=self.identity.id))
        return active_job

    def pause_job(self, job_id: JobId) -> Job:
        """Pause a job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.PAUSED)
        self._jobs[job_id] = updated
        self._emit(JobPausedEvent(job_id=job_id, backend_id=self.identity.id))
        return updated

    def resume_job(self, job_id: JobId) -> Job:
        """Resume a paused job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.ACTIVE)
        self._jobs[job_id] = updated
        self._emit(JobResumedEvent(job_id=job_id, backend_id=self.identity.id))
        return updated

    def cancel_job(self, job_id: JobId) -> Job:
        """Cancel a job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.REMOVED)
        self._jobs[job_id] = updated
        return updated

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        """Remove a job."""
        if job_id not in self._jobs:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
        del self._jobs[job_id]

    def get_job_status(self, job_id: JobId) -> Job:
        """Retrieve the current job status."""
        if not self.ping():
            raise BackendConnectionError(
                "FakeBackend is offline", backend_id=self.identity.id
            )
        if job_id not in self._jobs:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
        return self._jobs[job_id]

    def get_diagnostics(self) -> BackendDiagnostics:
        """Return diagnostic health snapshot."""
        return BackendDiagnostics(
            healthy=self.ping(),
            uptime_seconds=3600.0 if self._initialized else 0.0,
            active_jobs=sum(1 for j in self._jobs.values() if j.is_active),
            details={"mode": "in-memory-simulation", "job_count": str(len(self._jobs))},
        )

    def get_supported_options(self) -> list[BackendOptionSpec]:
        """Return fake option specifications."""
        return [
            BackendOptionSpec(
                name="simulated-speed-limit",
                option_type=OptionType.INT,
                default_value=0,
                scope=OptionScope.BOTH,
                mutability=OptionMutability.DYNAMIC,
                description="Simulated download bandwidth cap in bytes/sec",
            ),
            BackendOptionSpec(
                name="auto-verify-checksum",
                option_type=OptionType.BOOL,
                default_value=True,
                scope=OptionScope.JOB,
                description="Automatically verify output file checksums upon completion",
            ),
        ]

    # --- Deterministic Simulation Methods ---

    def simulate_progress(
        self,
        job_id: JobId,
        completed_bytes: int,
        total_bytes: int | None = None,
        speed_bps: int = 1_000_000,
    ) -> Job:
        """Advance progress and calculate speed/ETA."""
        job = self.get_job_status(job_id)
        tot_size = (
            ByteSize(total_bytes)
            if total_bytes is not None
            else job.progress.total_length
        )
        comp_size = ByteSize(completed_bytes)
        speed = BitRate(speed_bps)
        eta = Duration.calculate_eta(comp_size, tot_size, speed)

        prog = JobProgress(
            total_length=tot_size,
            completed_length=comp_size,
            download_speed=speed,
            eta=eta,
        )
        updated = replace(job, progress=prog)
        self._jobs[job_id] = updated
        self._emit(
            JobProgressChangedEvent(
                job_id=job_id,
                backend_id=self.identity.id,
                completed_bytes=comp_size,
                total_bytes=tot_size,
                download_speed=speed,
                upload_speed=BitRate(0),
            )
        )
        return updated

    def simulate_complete(
        self,
        job_id: JobId,
        artifacts: list[Artifact] | None = None,
    ) -> Job:
        """Transition job to COMPLETED with output artifacts."""
        job = self.get_job_status(job_id)
        if artifacts is None:
            default_art = Artifact(
                id=make_artifact_id(f"art-{job_id}"),
                job_id=job_id,
                kind=ArtifactKind.FILE,
                name=job.name,
                path=f"/downloads/{job.name}",
                size=job.progress.total_length or job.progress.completed_length,
                status=ArtifactStatus.VERIFIED,
            )
            artifacts = [default_art]

        updated = job.transition_to(DownloadState.COMPLETED)
        updated = replace(
            updated,
            outputs=artifacts,
            progress=replace(
                updated.progress,
                completed_length=updated.progress.total_length
                or updated.progress.completed_length,
                download_speed=BitRate(0),
                eta=None,
            ),
        )
        self._jobs[job_id] = updated
        self._emit(
            JobCompletedEvent(
                job_id=job_id,
                backend_id=self.identity.id,
                artifacts=tuple(artifacts),
            )
        )
        return updated

    def simulate_failure(self, job_id: JobId, error_message: str) -> Job:
        """Transition job to FAILED."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.FAILED)
        updated = replace(updated, error_message=error_message)
        self._jobs[job_id] = updated
        self._emit(
            JobFailedEvent(
                job_id=job_id,
                backend_id=self.identity.id,
                error_message=error_message,
            )
        )
        return updated

    def _emit(self, event: DomainEvent) -> None:
        if self._event_callback:
            try:
                self._event_callback(event)
            except Exception as e:
                logger.warning("Error in fake backend event callback: %s", e)
