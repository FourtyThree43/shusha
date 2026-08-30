"""Unit tests for FakeBackend simulation features (Epic E06)."""

from __future__ import annotations

import pytest

from shusha.backends import (
    BackendConnectionError,
    BackendExecutionError,
    FakeBackend,
)
from shusha.domain.artifact import ArtifactKind
from shusha.domain.events import (
    DomainEvent,
    JobCompletedEvent,
    JobFailedEvent,
    JobProgressChangedEvent,
)
from shusha.domain.identifiers import make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState
from shusha.domain.values import ByteSize, Percentage


class TestFakeBackendSimulation:
    """Tests for FakeBackend deterministic simulation capabilities (E06-I01)."""

    def test_progress_speed_and_eta_simulation(self) -> None:
        events: list[DomainEvent] = []
        backend = FakeBackend(event_callback=lambda e: events.append(e))
        backend.initialize()

        job = Job(
            id=make_job_id("j-sim-1"),
            backend_id=backend.identity.id,
            name="large_dataset.bin",
        )
        backend.submit_job(job)

        # Simulate 50% progress at 5 MB/s
        updated = backend.simulate_progress(
            job_id=job.id,
            completed_bytes=50_000_000,
            total_bytes=100_000_000,
            speed_bps=5_000_000,
        )

        assert updated.progress.completed_length == ByteSize(50_000_000)
        assert updated.progress.total_length == ByteSize(100_000_000)
        assert updated.progress.percentage == Percentage(50.0)
        assert updated.progress.eta is not None
        assert updated.progress.eta.seconds == 10  # 50MB remaining / 5MB/s = 10s
        assert any(isinstance(e, JobProgressChangedEvent) for e in events)

    def test_completion_simulation_produces_artifacts(self) -> None:
        events: list[DomainEvent] = []
        backend = FakeBackend(event_callback=lambda e: events.append(e))
        backend.initialize()

        job = Job(
            id=make_job_id("j-sim-2"), backend_id=backend.identity.id, name="movie.mkv"
        )
        backend.submit_job(job)

        completed_job = backend.simulate_complete(job.id)
        assert completed_job.state == DownloadState.COMPLETED
        assert len(completed_job.outputs) == 1
        assert completed_job.outputs[0].kind == ArtifactKind.FILE
        assert completed_job.outputs[0].is_verified
        assert any(isinstance(e, JobCompletedEvent) for e in events)

    def test_failure_simulation(self) -> None:
        events: list[DomainEvent] = []
        backend = FakeBackend(event_callback=lambda e: events.append(e))
        backend.initialize()

        job = Job(
            id=make_job_id("j-sim-3"),
            backend_id=backend.identity.id,
            name="unstable.iso",
        )
        backend.submit_job(job)

        failed_job = backend.simulate_failure(job.id, error_message="Disk full")
        assert failed_job.state == DownloadState.FAILED
        assert failed_job.error_message == "Disk full"
        assert any(isinstance(e, JobFailedEvent) for e in events)

    def test_offline_disconnect_simulation(self) -> None:
        backend = FakeBackend()
        backend.initialize()

        job = Job(
            id=make_job_id("j-sim-4"), backend_id=backend.identity.id, name="test.bin"
        )
        backend.submit_job(job)

        backend.set_online(False)
        assert backend.ping() is False
        with pytest.raises(BackendConnectionError):
            backend.get_job_status(job.id)

    def test_submission_failure_injection(self) -> None:
        backend = FakeBackend()
        backend.initialize()
        backend.set_fail_next_submission("Simulated internal error")

        job = Job(
            id=make_job_id("j-sim-5"), backend_id=backend.identity.id, name="fail.bin"
        )
        with pytest.raises(BackendExecutionError, match="Simulated internal error"):
            backend.submit_job(job)
