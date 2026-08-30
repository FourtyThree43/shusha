"""Backend-neutral Job Lifecycle Service (E03-I04)."""

from __future__ import annotations

import logging
from dataclasses import replace

from shusha.application.event_bus import EventBus
from shusha.domain.acquisition import AcquisitionRequest, SourceKind
from shusha.domain.artifact import Artifact
from shusha.domain.download_source import DownloadSource
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.events import (
    JobCancelledEvent,
    JobCompletedEvent,
    JobCreatedEvent,
    JobFailedEvent,
    JobPausedEvent,
    JobProgressChangedEvent,
    JobRemovedEvent,
    JobResumedEvent,
    JobStartedEvent,
)
from shusha.domain.identifiers import (
    BackendId,
    CategoryId,
    JobGroupId,
    JobId,
    make_acquisition_id,
    make_job_id,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.states import DownloadState

logger = logging.getLogger(__name__)


class JobLifecycleService:
    """Orchestrates job lifecycle in a backend-neutral manner and emits events."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._jobs: dict[JobId, Job] = {}

    def get_job(self, job_id: JobId) -> Job:
        """Retrieve a managed job or raise DownloadNotFoundError."""
        if job_id not in self._jobs:
            raise DownloadNotFoundError(f"Job {job_id} not found")
        return self._jobs[job_id]

    def list_jobs(
        self,
        state: DownloadState | None = None,
        backend_id: BackendId | None = None,
        category_id: CategoryId | None = None,
    ) -> list[Job]:
        """List active jobs with optional filtering."""
        result: list[Job] = []
        for job in self._jobs.values():
            if state is not None and job.state != state:
                continue
            if backend_id is not None and job.backend_id != backend_id:
                continue
            if category_id is not None and job.category_id != category_id:
                continue
            result.append(job)
        return result

    def create_job(
        self,
        name: str,
        source_input: str,
        backend_id: BackendId,
        category_id: CategoryId | None = None,
        group_id: JobGroupId | None = None,
        options: dict[str, str] | None = None,
    ) -> Job:
        """Create a new job in QUEUED state and publish JobCreatedEvent."""
        import uuid

        job_id = make_job_id(f"job-{uuid.uuid4().hex[:8]}")
        acq_id = make_acquisition_id(f"acq-{uuid.uuid4().hex[:8]}")

        req = AcquisitionRequest(
            id=acq_id,
            source_kind=SourceKind.MANUAL,
            raw_input=source_input,
            preferred_backend=backend_id,
            metadata=options or {},
        )
        source = DownloadSource.from_str(
            source_input if "://" in source_input else f"http://{source_input}"
        )

        job = Job(
            id=job_id,
            backend_id=backend_id,
            name=name,
            state=DownloadState.QUEUED,
            group_id=group_id,
            source=source,
            request=req,
            category_id=category_id,
            metadata=options or {},
        )

        self._jobs[job_id] = job
        self.event_bus.publish(
            JobCreatedEvent(job_id=job.id, backend_id=job.backend_id, name=job.name)
        )
        return job

    def start_job(self, job_id: JobId) -> Job:
        """Transition job to ACTIVE and publish JobStartedEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.ACTIVE)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobStartedEvent(job_id=updated.id, backend_id=updated.backend_id)
        )
        return updated

    def pause_job(self, job_id: JobId) -> Job:
        """Transition job to PAUSED and publish JobPausedEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.PAUSED)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobPausedEvent(job_id=updated.id, backend_id=updated.backend_id)
        )
        return updated

    def resume_job(self, job_id: JobId) -> Job:
        """Transition job back to ACTIVE and publish JobResumedEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.ACTIVE)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobResumedEvent(job_id=updated.id, backend_id=updated.backend_id)
        )
        return updated

    def complete_job(self, job_id: JobId, artifacts: tuple[Artifact, ...] = ()) -> Job:
        """Transition job to COMPLETED, record output artifacts, and publish JobCompletedEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.COMPLETED)
        if artifacts:
            updated = replace(updated, outputs=list(artifacts))
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobCompletedEvent(
                job_id=updated.id, backend_id=updated.backend_id, artifacts=artifacts
            )
        )
        return updated

    def fail_job(self, job_id: JobId, error_message: str) -> Job:
        """Transition job to FAILED and publish JobFailedEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.FAILED)
        updated = replace(updated, error_message=error_message)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobFailedEvent(
                job_id=updated.id,
                backend_id=updated.backend_id,
                error_message=error_message,
            )
        )
        return updated

    def cancel_job(self, job_id: JobId) -> Job:
        """Transition job to REMOVED and publish JobCancelledEvent."""
        job = self.get_job(job_id)
        updated = job.transition_to(DownloadState.REMOVED)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobCancelledEvent(job_id=updated.id, backend_id=updated.backend_id)
        )
        return updated

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        """Remove job from active management and publish JobRemovedEvent."""
        job = self.get_job(job_id)
        del self._jobs[job_id]
        self.event_bus.publish(
            JobRemovedEvent(job_id=job.id, backend_id=job.backend_id)
        )

    def retry_job(self, job_id: JobId) -> Job:
        """Reset failed/cancelled job back to QUEUED and publish JobCreatedEvent."""
        job = self.get_job(job_id)
        updated = replace(job, state=DownloadState.QUEUED, error_message=None)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobCreatedEvent(
                job_id=updated.id, backend_id=updated.backend_id, name=updated.name
            )
        )
        return updated

    def update_progress(self, job_id: JobId, progress: JobProgress) -> Job:
        """Update job progress and publish JobProgressChangedEvent."""
        job = self.get_job(job_id)
        updated = replace(job, progress=progress)
        self._jobs[job_id] = updated
        self.event_bus.publish(
            JobProgressChangedEvent(
                job_id=updated.id,
                backend_id=updated.backend_id,
                completed_bytes=progress.completed_length,
                total_bytes=progress.total_length,
                download_speed=progress.download_speed,
                upload_speed=progress.upload_speed,
            )
        )
        return updated
