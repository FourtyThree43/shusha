"""Unit tests for Application Layer Commands, Queries, EventBus, and JobLifecycleService (Epic E03)."""

from __future__ import annotations

import pytest

from shusha.application.command_bus import (
    CommandBus,
    CreateJobCommand,
    PauseJobCommand,
    StartJobCommand,
)
from shusha.application.event_bus import EventBus
from shusha.application.queries import (
    GetCapabilitiesQuery,
    GetJobQuery,
    QueryBus,
)
from shusha.application.services.job_lifecycle import JobLifecycleService
from shusha.domain.artifact import Artifact, ArtifactKind
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.events import (
    DomainEvent,
    JobCompletedEvent,
    JobCreatedEvent,
    JobPausedEvent,
    JobProgressChangedEvent,
    JobRemovedEvent,
    JobResumedEvent,
    JobStartedEvent,
)
from shusha.domain.identifiers import (
    make_artifact_id,
    make_backend_id,
    make_job_id,
)
from shusha.domain.job import JobProgress
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize


class TestEventBus:
    """Tests for in-memory publish-subscribe EventBus (E03-I03)."""

    def test_type_specific_subscription_and_dispatch(self) -> None:
        bus = EventBus()
        received: list[JobCreatedEvent] = []

        unsub = bus.subscribe(JobCreatedEvent, lambda e: received.append(e))
        assert bus.subscriber_count(JobCreatedEvent) == 1

        ev1 = JobCreatedEvent(
            job_id=make_job_id("j1"),
            backend_id=make_backend_id("aria2"),
            name="ubuntu.iso",
        )
        ev2 = JobStartedEvent(
            job_id=make_job_id("j1"),
            backend_id=make_backend_id("aria2"),
        )

        bus.publish(ev1)
        bus.publish(ev2)

        assert len(received) == 1
        assert received[0].name == "ubuntu.iso"

        unsub()
        assert bus.subscriber_count(JobCreatedEvent) == 0

        bus.publish(ev1)
        assert len(received) == 1

    def test_subscribe_all_receives_any_domain_event(self) -> None:
        bus = EventBus()
        all_events: list[DomainEvent] = []

        bus.subscribe_all(lambda e: all_events.append(e))

        bus.publish(
            JobCreatedEvent(
                job_id=make_job_id("j1"),
                backend_id=make_backend_id("aria2"),
                name="test",
            )
        )
        bus.publish(
            JobPausedEvent(
                job_id=make_job_id("j1"),
                backend_id=make_backend_id("aria2"),
            )
        )

        assert len(all_events) == 2


class TestCommandBus:
    """Tests for application CommandBus (E03-I01)."""

    def test_command_registration_and_dispatch(self) -> None:
        bus = CommandBus()
        executed: list[str] = []

        def handle_create(cmd: CreateJobCommand) -> str:
            executed.append(cmd.name)
            return "job-created-123"

        bus.register(CreateJobCommand, handle_create)
        assert bus.has_handler(CreateJobCommand)
        assert not bus.has_handler(StartJobCommand)

        result = bus.dispatch(
            CreateJobCommand(
                name="archlinux.iso",
                source_input="https://example.com/arch.iso",
            )
        )
        assert result == "job-created-123"
        assert executed == ["archlinux.iso"]

    def test_unregistered_command_raises_key_error(self) -> None:
        bus = CommandBus()
        with pytest.raises(KeyError, match="No handler registered"):
            bus.dispatch(PauseJobCommand(job_id=make_job_id("j1")))


class TestQueryBus:
    """Tests for application QueryBus (E03-I02)."""

    def test_query_registration_and_dispatch(self) -> None:
        bus = QueryBus()

        def handle_caps(q: GetCapabilitiesQuery) -> CapabilitySet:
            return CapabilitySet.from_iterable([Capability.HTTP, Capability.TORRENT])

        bus.register(GetCapabilitiesQuery, handle_caps)
        result: CapabilitySet = bus.dispatch(GetCapabilitiesQuery())

        assert isinstance(result, CapabilitySet)
        assert result.has(Capability.HTTP)

    def test_unregistered_query_raises_key_error(self) -> None:
        bus = QueryBus()
        with pytest.raises(KeyError, match="No handler registered"):
            bus.dispatch(GetJobQuery(job_id=make_job_id("j1")))


class TestJobLifecycleService:
    """Tests for JobLifecycleService (E03-I04)."""

    def test_complete_job_lifecycle_workflow(self) -> None:
        bus = EventBus()
        events_received: list[DomainEvent] = []
        bus.subscribe_all(lambda e: events_received.append(e))

        svc = JobLifecycleService(event_bus=bus)

        # 1. Create
        job = svc.create_job(
            name="debian.iso",
            source_input="https://cdimage.debian.org/debian.iso",
            backend_id=make_backend_id("aria2"),
        )
        assert job.state == DownloadState.QUEUED
        assert isinstance(events_received[-1], JobCreatedEvent)

        # 2. Start
        job = svc.start_job(job.id)
        assert job.state == DownloadState.ACTIVE
        assert isinstance(events_received[-1], JobStartedEvent)

        # 3. Update progress
        job = svc.update_progress(
            job.id,
            JobProgress(
                total_length=ByteSize(1000),
                completed_length=ByteSize(500),
                download_speed=BitRate(100),
            ),
        )
        assert job.progress.completed_length == ByteSize(500)
        assert isinstance(events_received[-1], JobProgressChangedEvent)

        # 4. Pause
        job = svc.pause_job(job.id)
        assert job.state == DownloadState.PAUSED
        assert isinstance(events_received[-1], JobPausedEvent)

        # 5. Resume
        job = svc.resume_job(job.id)
        assert job.state == DownloadState.ACTIVE
        assert isinstance(events_received[-1], JobResumedEvent)

        # 6. Complete
        artifact = Artifact(
            id=make_artifact_id("art-1"),
            job_id=job.id,
            kind=ArtifactKind.FILE,
            name="debian.iso",
            path="/downloads/debian.iso",
            size=ByteSize(1000),
        )
        job = svc.complete_job(job.id, artifacts=(artifact,))
        assert job.state == DownloadState.COMPLETED
        assert len(job.outputs) == 1
        assert isinstance(events_received[-1], JobCompletedEvent)

        # 7. Remove
        svc.remove_job(job.id)
        assert isinstance(events_received[-1], JobRemovedEvent)
        with pytest.raises(DownloadNotFoundError):
            svc.get_job(job.id)

    def test_job_failure_and_retry(self) -> None:
        bus = EventBus()
        svc = JobLifecycleService(event_bus=bus)

        job = svc.create_job(
            name="faulty.iso",
            source_input="https://example.com/bad.iso",
            backend_id=make_backend_id("aria2"),
        )
        svc.start_job(job.id)
        failed_job = svc.fail_job(job.id, error_message="Connection timed out")
        assert failed_job.state == DownloadState.FAILED
        assert failed_job.error_message == "Connection timed out"

        retried_job = svc.retry_job(job.id)
        assert retried_job.state == DownloadState.QUEUED
        assert retried_job.error_message is None
