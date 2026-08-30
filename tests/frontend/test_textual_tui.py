"""Unit and smoke tests for Shusha Textual TUI & Diagnostics (Epic E12).

Validates that the Textual TUI initializes cleanly against FakeBackend and EventBus
without requiring physical terminal display devices.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from textual.widgets import DataTable, TabbedContent

from shusha.application.command_bus import CommandBus
from shusha.application.event_bus import EventBus
from shusha.application.query_bus import QueryBus
from shusha.backends.fake import FakeBackend
from shusha.backends.registry import BackendRegistry
from shusha.domain.events import (
    JobCompletedEvent,
    JobCreatedEvent,
    JobPausedEvent,
    JobProgressChangedEvent,
    JobRemovedEvent,
    JobResumedEvent,
    JobStartedEvent,
)
from shusha.domain.identifiers import make_job_id
from shusha.domain.job import Job, JobProgress
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Duration
from shusha.interfaces.tui import (
    DiagnosticsScreen,
    DiagnosticsView,
    DoctorScreen,
    DoctorView,
    JobMonitorScreen,
    JobMonitorView,
    ShushaTUIApp,
)
from shusha.interfaces.tui.screens.doctor import (
    DoctorStatus,
    run_system_doctor_checks,
)
from shusha.tui import ShushaTUIApp as ShushaTUIAppAlias


def test_tui_imports_and_alias() -> None:
    """Validate package exports and backwards-compatible aliases."""
    assert ShushaTUIApp is ShushaTUIAppAlias
    assert JobMonitorScreen is not None
    assert DiagnosticsScreen is not None
    assert DoctorScreen is not None


def test_doctor_checks_execution(tmp_path: Path) -> None:
    """Validate system doctor diagnostics logic returns structured results."""
    results = run_system_doctor_checks(custom_download_dir=tmp_path)
    assert len(results) >= 5

    categories = {r.category for r in results}
    assert "Binaries & Engines" in categories
    assert "Storage & Permissions" in categories
    assert "Network & Proxy" in categories
    assert "Runtime & Platform" in categories

    # Storage check on tmp_path must pass
    storage_checks = [r for r in results if r.name == "Downloads Directory"]
    assert len(storage_checks) == 1
    assert storage_checks[0].status == DoctorStatus.PASS


def test_doctor_checks_proxy_handling(tmp_path: Path) -> None:
    """Validate doctor handles valid and invalid proxy configurations."""
    # Test valid proxy
    with patch.dict("os.environ", {"HTTP_PROXY": "http://127.0.0.1:8080"}):
        results = run_system_doctor_checks(custom_download_dir=tmp_path)
        proxy_check = next(r for r in results if r.name == "Proxy Configuration")
        assert proxy_check.status == DoctorStatus.PASS

    # Test invalid proxy format
    with patch.dict("os.environ", {"HTTP_PROXY": "invalid://"}):
        results = run_system_doctor_checks(custom_download_dir=tmp_path)
        proxy_check = next(r for r in results if r.name == "Proxy Configuration")
        assert proxy_check.status in (DoctorStatus.WARN, DoctorStatus.FAIL)


def test_tui_app_initialization_with_fake_backend() -> None:
    """Validate ShushaTUIApp boots against FakeBackend and initializes subsystems."""

    async def _run() -> None:
        event_bus = EventBus()
        command_bus = CommandBus()
        query_bus = QueryBus()
        registry = BackendRegistry()
        fake = FakeBackend()
        fake.initialize()
        registry.register(fake, default=True)

        job1 = Job(
            id=make_job_id("job-001"),
            backend_id=fake.identity.id,
            name="ubuntu-24.04.iso",
            state=DownloadState.ACTIVE,
            progress=JobProgress(
                completed_length=ByteSize(500_000_000),
                total_length=ByteSize(1_000_000_000),
                download_speed=BitRate(5_000_000),
                eta=Duration(100),
            ),
        )

        app = ShushaTUIApp(
            event_bus=event_bus,
            command_bus=command_bus,
            query_bus=query_bus,
            backend_registry=registry,
            initial_jobs=[job1],
        )

        async with app.run_test() as pilot:
            assert pilot.app.is_running

            # Verify TabbedContent has initialized with all 3 tabs
            tabs = pilot.app.query_one(TabbedContent)
            assert tabs.active == "tab-jobs"

            # Verify JobMonitorView is mounted
            job_view = pilot.app.query_one("#view-job-monitor", JobMonitorView)
            assert job_view is not None
            assert len(job_view._jobs) == 1

            # Verify DataTable has the initial job
            table = job_view.query_one("#job-table", DataTable)
            assert table.row_count == 1

            # Switch to Diagnostics tab
            app.action_switch_tab("tab-diagnostics")
            await pilot.pause()
            assert tabs.active == "tab-diagnostics"

            # Verify DiagnosticsView
            diag_view = pilot.app.query_one("#view-diagnostics", DiagnosticsView)
            assert diag_view is not None
            diag_table = diag_view.query_one("#diag-table", DataTable)
            assert diag_table.row_count >= 1

            # Switch to Doctor tab
            app.action_switch_tab("tab-doctor")
            await pilot.pause()
            assert tabs.active == "tab-doctor"

            # Verify DoctorView
            doc_view = pilot.app.query_one("#view-doctor", DoctorView)
            assert doc_view is not None
            doc_table = doc_view.query_one("#doctor-table", DataTable)
            assert doc_table.row_count >= 5

    asyncio.run(_run())


def test_tui_live_job_events_incremental_updates() -> None:
    """Validate that domain events update JobMonitorView incrementally without table destruction."""

    async def _run() -> None:
        event_bus = EventBus()
        registry = BackendRegistry()
        fake = FakeBackend()
        fake.initialize()
        registry.register(fake, default=True)

        app = ShushaTUIApp(
            event_bus=event_bus,
            backend_registry=registry,
        )

        async with app.run_test() as pilot:
            job_view = pilot.app.query_one("#view-job-monitor", JobMonitorView)
            table = job_view.query_one("#job-table", DataTable)
            assert table.row_count == 0

            # 1. Publish JobCreatedEvent
            jid = make_job_id("test-dl-1")
            event_bus.publish(
                JobCreatedEvent(
                    job_id=jid,
                    backend_id=fake.identity.id,
                    name="archlinux.iso",
                )
            )
            await pilot.pause()
            assert table.row_count == 1
            assert jid in job_view._jobs
            assert job_view._jobs[jid].state == DownloadState.QUEUED

            # 2. Publish JobStartedEvent -> Transition to ACTIVE
            event_bus.publish(
                JobStartedEvent(
                    job_id=jid,
                    backend_id=fake.identity.id,
                )
            )
            await pilot.pause()
            assert table.row_count == 1
            assert job_view._jobs[jid].state == DownloadState.ACTIVE

            # 3. Publish JobProgressChangedEvent -> Updates progress cells in-place
            event_bus.publish(
                JobProgressChangedEvent(
                    job_id=jid,
                    backend_id=fake.identity.id,
                    completed_bytes=ByteSize(750_000_000),
                    total_bytes=ByteSize(1_000_000_000),
                    download_speed=BitRate(10_000_000),
                    upload_speed=BitRate(500_000),
                )
            )
            await pilot.pause()
            assert table.row_count == 1
            assert job_view._jobs[jid].progress.percentage.value == 75.0

            # 4. Publish JobPausedEvent
            event_bus.publish(JobPausedEvent(job_id=jid, backend_id=fake.identity.id))
            await pilot.pause()
            assert job_view._jobs[jid].state == DownloadState.PAUSED

            # 5. Publish JobResumedEvent
            event_bus.publish(JobResumedEvent(job_id=jid, backend_id=fake.identity.id))
            await pilot.pause()
            assert job_view._jobs[jid].state == DownloadState.ACTIVE

            # 6. Publish JobCompletedEvent
            event_bus.publish(
                JobCompletedEvent(job_id=jid, backend_id=fake.identity.id)
            )
            await pilot.pause()
            assert job_view._jobs[jid].state == DownloadState.COMPLETED

            # 7. Publish JobRemovedEvent -> Removes row from table
            event_bus.publish(JobRemovedEvent(job_id=jid, backend_id=fake.identity.id))
            await pilot.pause()
            assert table.row_count == 0
            assert jid not in job_view._jobs

    asyncio.run(_run())


def test_tui_job_filtering() -> None:
    """Validate state filtering on the JobMonitorView."""

    async def _run() -> None:
        registry = BackendRegistry()
        fake = FakeBackend()
        fake.initialize()
        registry.register(fake)

        job_act = Job(
            id=make_job_id("job-act"),
            backend_id=fake.identity.id,
            name="active_task.bin",
            state=DownloadState.ACTIVE,
        )
        job_pau = Job(
            id=make_job_id("job-pau"),
            backend_id=fake.identity.id,
            name="paused_task.bin",
            state=DownloadState.PAUSED,
        )
        job_don = Job(
            id=make_job_id("job-don"),
            backend_id=fake.identity.id,
            name="done_task.bin",
            state=DownloadState.COMPLETED,
        )

        app = ShushaTUIApp(
            backend_registry=registry,
            initial_jobs=[job_act, job_pau, job_don],
        )

        async with app.run_test() as pilot:
            job_view = pilot.app.query_one("#view-job-monitor", JobMonitorView)
            table = job_view.query_one("#job-table", DataTable)
            assert table.row_count == 3

            # Filter to Active only
            job_view._handle_filter_button("btn-filter-active")
            await pilot.pause()
            assert table.row_count == 1

            # Filter to Paused only
            job_view._handle_filter_button("btn-filter-paused")
            await pilot.pause()
            assert table.row_count == 1

            # Filter to Done only
            job_view._handle_filter_button("btn-filter-done")
            await pilot.pause()
            assert table.row_count == 1

            # Filter to All
            job_view._handle_filter_button("btn-filter-all")
            await pilot.pause()
            assert table.row_count == 3

    asyncio.run(_run())


def test_tui_action_dispatching() -> None:
    """Validate pause/resume/remove actions from JobMonitorView."""

    async def _run() -> None:
        command_bus = CommandBus()
        registry = BackendRegistry()
        fake = FakeBackend()
        fake.initialize()
        registry.register(fake)

        dispatched_commands: list[str] = []

        from shusha.application.commands import (
            PauseJobCommand,
            RemoveJobCommand,
            ResumeJobCommand,
            RetryJobCommand,
        )

        command_bus.register(
            PauseJobCommand, lambda c: dispatched_commands.append("pause")
        )
        command_bus.register(
            ResumeJobCommand, lambda c: dispatched_commands.append("resume")
        )
        command_bus.register(
            RemoveJobCommand, lambda c: dispatched_commands.append("remove")
        )
        command_bus.register(
            RetryJobCommand, lambda c: dispatched_commands.append("retry")
        )

        jid = make_job_id("job-act")
        job_act = Job(
            id=jid,
            backend_id=fake.identity.id,
            name="task.bin",
            state=DownloadState.ACTIVE,
        )

        app = ShushaTUIApp(
            command_bus=command_bus,
            backend_registry=registry,
            initial_jobs=[job_act],
        )

        async with app.run_test() as pilot:
            job_view = pilot.app.query_one("#view-job-monitor", JobMonitorView)

            job_view.action_pause_job(jid)
            assert "pause" in dispatched_commands

            job_view.action_resume_job(jid)
            assert "resume" in dispatched_commands

            job_view.action_retry_job(jid)
            assert "retry" in dispatched_commands

            job_view.action_remove_job(jid)
            assert "remove" in dispatched_commands

    asyncio.run(_run())


def test_tui_screens_standalone_composition() -> None:
    """Validate standalone Screen instances can compose without errors."""
    registry = BackendRegistry()
    fake = FakeBackend()
    fake.initialize()
    registry.register(fake)

    s1 = JobMonitorScreen(backend_registry=registry)
    assert s1 is not None

    s2 = DiagnosticsScreen(backend_registry=registry)
    assert s2 is not None

    s3 = DoctorScreen()
    assert s3 is not None


def test_tui_inbox_and_media_grabber_views() -> None:
    """Validate Acquisition Inbox and Media Grabber screens in Textual TUI."""

    async def _run() -> None:
        from shusha.acquisition.inbox import AcquisitionInbox
        from shusha.domain.acquisition import (
            AcquisitionRequest,
            AcquisitionStatus,
            DetectedKind,
            SourceKind,
        )
        from shusha.domain.identifiers import make_acquisition_id
        from shusha.interfaces.tui.screens import InboxView, MediaGrabberView

        inbox = AcquisitionInbox()
        inbox.add(
            AcquisitionRequest(
                id=make_acquisition_id("acq-tui-1"),
                source_kind=SourceKind.CLIPBOARD,
                raw_input="https://example.com/file.tar.gz",
                detected_kind=DetectedKind.DIRECT_URL,
                status=AcquisitionStatus.DETECTED,
            )
        )

        app = ShushaTUIApp(acquisition_inbox=inbox)

        async with app.run_test() as pilot:
            # Switch to Inbox tab
            app.action_switch_tab("tab-inbox")
            await pilot.pause()

            inbox_view = pilot.app.query_one("#view-inbox", InboxView)
            inbox_table = inbox_view.query_one("#inbox_table", DataTable)
            assert inbox_table.row_count == 1

            # Accept item
            inbox_view.accept_selected()
            item = inbox.get(make_acquisition_id("acq-tui-1"))
            assert item is not None
            assert item.status == AcquisitionStatus.ACCEPTED

            # Switch to Media Grabber tab
            app.action_switch_tab("tab-media")
            await pilot.pause()
            media_view = pilot.app.query_one("#view-media-grabber", MediaGrabberView)
            assert media_view is not None

    asyncio.run(_run())


def test_tui_add_modal_composition() -> None:
    """Validate AddDownloadModal can be composed and dismissed."""
    from shusha.interfaces.tui.screens.add_modal import AddDownloadModal

    modal = AddDownloadModal()
    assert modal is not None
