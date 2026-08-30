"""Live Job Monitor screen and widget for Textual TUI (Epic E12-I02)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import replace
from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Input, Static

from shusha.domain.events import (
    DomainEvent,
    JobCancelledEvent,
    JobCompletedEvent,
    JobCreatedEvent,
    JobFailedEvent,
    JobPausedEvent,
    JobProgressChangedEvent,
    JobRemovedEvent,
    JobResumedEvent,
    JobStartedEvent,
    JobStateChangedEvent,
)
from shusha.domain.identifiers import JobId, make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState

if TYPE_CHECKING:
    from shusha.application.command_bus import CommandBus
    from shusha.application.event_bus import EventBus
    from shusha.application.query_bus import QueryBus
    from shusha.backends.registry import BackendRegistry

logger = logging.getLogger(__name__)


def _format_state_badge(state: DownloadState) -> str:
    """Format job download state with semantic Rich markup."""
    match state:
        case DownloadState.ACTIVE:
            return "[bold green]ACTIVE[/bold green]"
        case DownloadState.QUEUED:
            return "[bold blue]QUEUED[/bold blue]"
        case DownloadState.PAUSED:
            return "[bold yellow]PAUSED[/bold yellow]"
        case DownloadState.COMPLETED:
            return "[bold cyan]COMPLETED[/bold cyan]"
        case DownloadState.FAILED:
            return "[bold red]FAILED[/bold red]"
        case DownloadState.REMOVED:
            return "[dim red]REMOVED[/dim red]"
        case _:
            return f"[white]{state.value.upper()}[/white]"


def _format_job_row(job: Job) -> tuple[str, str, str, str, str, str, str, str]:
    """Format Job data into column cells."""
    # 1. ID
    job_id_str = str(job.id)
    short_id = job_id_str[:12] if len(job_id_str) > 12 else job_id_str

    # 2. Name
    name = job.name or "Untitled Download"
    if len(name) > 36:
        name = name[:33] + "..."

    # 3. Backend
    backend = str(job.backend_id)

    # 4. State
    state_str = _format_state_badge(job.state)

    # 5. Progress
    pct_val = job.progress.percentage.value
    pct_str = f"{pct_val:5.1f}%"
    if job.state == DownloadState.COMPLETED:
        progress_str = f"[cyan]{pct_str}[/cyan]"
    elif job.state == DownloadState.ACTIVE:
        progress_str = f"[green]{pct_str}[/green]"
    elif job.state == DownloadState.FAILED:
        progress_str = f"[red]{pct_str}[/red]"
    else:
        progress_str = f"[yellow]{pct_str}[/yellow]"

    # 6. Downloaded / Total
    comp_size = job.progress.completed_length.human_readable()
    tot_size = (
        job.progress.total_length.human_readable()
        if job.progress.total_length
        else "Unknown"
    )
    size_str = f"{comp_size} / {tot_size}"

    # 7. Speed
    if (
        job.state == DownloadState.ACTIVE
        and job.progress.download_speed.bytes_per_sec > 0
    ):
        speed_str = (
            f"[bold green]{job.progress.download_speed.human_readable()}[/bold green]"
        )
    else:
        speed_str = "--"

    # 8. ETA
    if (
        job.state == DownloadState.ACTIVE
        and job.progress.eta
        and job.progress.eta.seconds > 0
    ):
        eta_str = job.progress.eta.human_readable()
    elif job.state == DownloadState.COMPLETED:
        eta_str = "Done"
    else:
        eta_str = "--"

    return (
        short_id,
        name,
        backend,
        state_str,
        progress_str,
        size_str,
        speed_str,
        eta_str,
    )


class JobSummaryBar(Static):
    """Real-time summary statistics bar for all tracked jobs."""

    def update_metrics(self, jobs: Sequence[Job]) -> None:
        """Update the aggregate statistics display."""
        total = len(jobs)
        active = sum(1 for j in jobs if j.state == DownloadState.ACTIVE)
        queued = sum(1 for j in jobs if j.state == DownloadState.QUEUED)
        paused = sum(1 for j in jobs if j.state == DownloadState.PAUSED)
        completed = sum(1 for j in jobs if j.state == DownloadState.COMPLETED)
        failed = sum(1 for j in jobs if j.state == DownloadState.FAILED)

        total_down_bps = sum(
            j.progress.download_speed.bytes_per_sec
            for j in jobs
            if j.state == DownloadState.ACTIVE
        )
        total_up_bps = sum(
            j.progress.upload_speed.bytes_per_sec
            for j in jobs
            if j.state == DownloadState.ACTIVE
        )

        down_speed_str = (
            f"{total_down_bps / 1_048_576:.1f} MB/s"
            if total_down_bps >= 1_048_576
            else f"{total_down_bps / 1024:.1f} KB/s"
        )
        up_speed_str = (
            f"{total_up_bps / 1_048_576:.1f} MB/s"
            if total_up_bps >= 1_048_576
            else f"{total_up_bps / 1024:.1f} KB/s"
        )

        content = (
            f"[bold]Jobs:[/bold] {total} total │ "
            f"[green]● {active} active[/green] │ "
            f"[blue]▶ {queued} queued[/blue] │ "
            f"[yellow]⏸ {paused} paused[/yellow] │ "
            f"[cyan]✔ {completed} done[/cyan] │ "
            f"[red]✖ {failed} failed[/red]   │   "
            f"[bold cyan]▼ DL:[/bold cyan] {down_speed_str} │ "
            f"[bold magenta]▲ UL:[/bold magenta] {up_speed_str}"
        )
        self.update(content)


class JobMonitorView(Widget):
    """Main live jobs monitor widget containing toolbar, filter, and table."""

    DEFAULT_CSS = """
    JobMonitorView {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    #summary-bar {
        background: $surface-darken-1;
        color: $text;
        padding: 0 1;
        height: 1;
        border-bottom: solid $primary-darken-3;
    }

    #toolbar {
        height: 3;
        padding: 0 1;
        align: left middle;
        background: $surface;
    }

    #filter-input {
        width: 30;
        margin-right: 1;
    }

    .filter-btn {
        margin-right: 1;
        min-width: 8;
        height: 1;
    }

    #job-table {
        height: 1fr;
        border: none;
    }

    #action-bar {
        height: 3;
        padding: 0 1;
        align: right middle;
        background: $surface-darken-1;
    }

    .action-btn {
        margin-left: 1;
        min-width: 10;
        height: 1;
    }
    """

    def __init__(
        self,
        command_bus: CommandBus | None = None,
        query_bus: QueryBus | None = None,
        event_bus: EventBus | None = None,
        backend_registry: BackendRegistry | None = None,
        initial_jobs: Sequence[Job] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._event_bus = event_bus
        self._backend_registry = backend_registry
        self._jobs: dict[JobId, Job] = {}
        self._state_filter: DownloadState | None = None
        self._text_filter: str = ""

        if initial_jobs:
            for j in initial_jobs:
                self._jobs[j.id] = j

    def compose(self) -> ComposeResult:
        yield JobSummaryBar(id="summary-bar")
        with Horizontal(id="toolbar"):
            yield Input(placeholder="Filter by name/ID...", id="filter-input")
            yield Button(
                "All", id="btn-filter-all", classes="filter-btn", variant="primary"
            )
            yield Button("Active", id="btn-filter-active", classes="filter-btn")
            yield Button("Queued", id="btn-filter-queued", classes="filter-btn")
            yield Button("Paused", id="btn-filter-paused", classes="filter-btn")
            yield Button("Done", id="btn-filter-done", classes="filter-btn")
            yield Button("Failed", id="btn-filter-failed", classes="filter-btn")

        yield DataTable(id="job-table", cursor_type="row", zebra_stripes=True)

        with Horizontal(id="action-bar"):
            yield Button(
                "⏸ Pause",
                id="btn-action-pause",
                classes="action-btn",
                variant="warning",
            )
            yield Button(
                "▶ Resume",
                id="btn-action-resume",
                classes="action-btn",
                variant="success",
            )
            yield Button(
                "✖ Remove",
                id="btn-action-remove",
                classes="action-btn",
                variant="error",
            )
            yield Button(
                "↺ Retry",
                id="btn-action-retry",
                classes="action-btn",
                variant="default",
            )

    def on_mount(self) -> None:
        """Initialize data table columns and populate initial rows."""
        table = self.query_one("#job-table", DataTable)
        table.add_column("ID", key="id")
        table.add_column("Name", key="name")
        table.add_column("Backend", key="backend")
        table.add_column("State", key="state")
        table.add_column("Progress", key="progress")
        table.add_column("Size", key="size")
        table.add_column("Speed", key="speed")
        table.add_column("ETA", key="eta")

        self._refresh_all_rows()
        self._update_summary()

    def _matches_filter(self, job: Job) -> bool:
        """Check if job satisfies current state and text filters."""
        if self._state_filter is not None and job.state != self._state_filter:
            return False
        if self._text_filter:
            tf = self._text_filter.lower()
            if tf not in str(job.id).lower() and tf not in job.name.lower():
                return False
        return True

    def _refresh_all_rows(self) -> None:
        """Clear and rebuild rows (used only on filter changes)."""
        try:
            table = self.query_one("#job-table", DataTable)
        except Exception:
            return

        table.clear()
        for job in self._jobs.values():
            if self._matches_filter(job):
                row_cells = _format_job_row(job)
                table.add_row(*row_cells, key=str(job.id))

    def _update_summary(self) -> None:
        """Refresh aggregate metrics bar."""
        try:
            summary = self.query_one("#summary-bar", JobSummaryBar)
            summary.update_metrics(list(self._jobs.values()))
        except Exception:
            pass

    def update_job(self, job: Job) -> None:
        """Incrementally update or insert a job row without table flicker."""
        self._jobs[job.id] = job
        row_key = str(job.id)

        try:
            table = self.query_one("#job-table", DataTable)
        except Exception:
            return

        matches = self._matches_filter(job)
        row_keys_set = {
            str(k.value) if hasattr(k, "value") else str(k) for k in table.rows
        }
        has_row = row_key in row_keys_set

        if matches:
            cells = _format_job_row(job)
            if has_row:
                # Update row cells in-place for flicker-free rendering
                table.update_cell(row_key, "id", cells[0])
                table.update_cell(row_key, "name", cells[1])
                table.update_cell(row_key, "backend", cells[2])
                table.update_cell(row_key, "state", cells[3])
                table.update_cell(row_key, "progress", cells[4])
                table.update_cell(row_key, "size", cells[5])
                table.update_cell(row_key, "speed", cells[6])
                table.update_cell(row_key, "eta", cells[7])
            else:
                table.add_row(*cells, key=row_key)
        else:
            if has_row:
                table.remove_row(row_key)

        self._update_summary()

    def remove_job(self, job_id: JobId | str) -> None:
        """Remove a job from state and view."""
        jid = make_job_id(str(job_id))
        if jid in self._jobs:
            del self._jobs[jid]

        row_key = str(job_id)
        try:
            table = self.query_one("#job-table", DataTable)
            row_keys_set = {
                str(k.value) if hasattr(k, "value") else str(k) for k in table.rows
            }
            if row_key in row_keys_set:
                table.remove_row(row_key)
        except Exception:
            pass

        self._update_summary()

    def handle_domain_event(self, event: DomainEvent) -> None:
        """Handle incoming domain event from EventBus."""
        match event:
            case JobCreatedEvent(job_id=jid, backend_id=bid, name=name):
                if jid not in self._jobs:
                    job = Job(
                        id=jid, backend_id=bid, name=name, state=DownloadState.QUEUED
                    )
                    self.update_job(job)
            case JobStartedEvent(job_id=jid):
                if jid in self._jobs:
                    self.update_job(self._jobs[jid].transition_to(DownloadState.ACTIVE))
            case JobStateChangedEvent(job_id=jid, new_state=ns):
                if jid in self._jobs:
                    self.update_job(self._jobs[jid].transition_to(ns))
            case JobProgressChangedEvent(
                job_id=jid,
                completed_bytes=cb,
                total_bytes=tb,
                download_speed=ds,
                upload_speed=us,
            ):
                if jid in self._jobs:
                    cur = self._jobs[jid]
                    new_prog = replace(
                        cur.progress,
                        completed_length=cb,
                        total_length=tb,
                        download_speed=ds,
                        upload_speed=us,
                    )
                    self.update_job(replace(cur, progress=new_prog))
            case JobPausedEvent(job_id=jid):
                if jid in self._jobs:
                    self.update_job(self._jobs[jid].transition_to(DownloadState.PAUSED))
            case JobResumedEvent(job_id=jid):
                if jid in self._jobs:
                    self.update_job(self._jobs[jid].transition_to(DownloadState.ACTIVE))
            case JobCompletedEvent(job_id=jid):
                if jid in self._jobs:
                    self.update_job(
                        self._jobs[jid].transition_to(DownloadState.COMPLETED)
                    )
            case JobFailedEvent(job_id=jid, error_message=msg):
                if jid in self._jobs:
                    cur = self._jobs[jid]
                    self.update_job(
                        replace(
                            cur.transition_to(DownloadState.FAILED), error_message=msg
                        )
                    )
            case JobCancelledEvent(job_id=jid):
                if jid in self._jobs:
                    self.update_job(
                        self._jobs[jid].transition_to(DownloadState.REMOVED)
                    )
            case JobRemovedEvent(job_id=jid):
                self.remove_job(jid)
            case _:
                pass

    def get_selected_job_id(self) -> JobId | None:
        """Get JobId of currently selected row in DataTable."""
        try:
            table = self.query_one("#job-table", DataTable)
            if table.cursor_row is not None and table.row_count > 0:
                row_key = list(table.rows.keys())[table.cursor_row]
                key_str = (
                    str(row_key.value) if hasattr(row_key, "value") else str(row_key)
                )
                return make_job_id(key_str)
        except Exception:
            pass
        return None

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter search input change."""
        if event.input.id == "filter-input":
            self._text_filter = event.value
            self._refresh_all_rows()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle toolbar filter buttons and action buttons."""
        btn_id = event.button.id
        if not btn_id:
            return

        # 1. State filters
        if btn_id.startswith("btn-filter-"):
            self._handle_filter_button(btn_id)
            return

        # 2. Job actions
        selected_id = self.get_selected_job_id()
        if not selected_id:
            return

        if btn_id == "btn-action-pause":
            self.action_pause_job(selected_id)
        elif btn_id == "btn-action-resume":
            self.action_resume_job(selected_id)
        elif btn_id == "btn-action-remove":
            self.action_remove_job(selected_id)
        elif btn_id == "btn-action-retry":
            self.action_retry_job(selected_id)

    def _handle_filter_button(self, btn_id: str) -> None:
        """Set state filter from clicked filter button."""
        match btn_id:
            case "btn-filter-all":
                self._state_filter = None
            case "btn-filter-active":
                self._state_filter = DownloadState.ACTIVE
            case "btn-filter-queued":
                self._state_filter = DownloadState.QUEUED
            case "btn-filter-paused":
                self._state_filter = DownloadState.PAUSED
            case "btn-filter-done":
                self._state_filter = DownloadState.COMPLETED
            case "btn-filter-failed":
                self._state_filter = DownloadState.FAILED

        self._refresh_all_rows()

    def action_pause_job(self, job_id: JobId) -> None:
        """Dispatch PauseJobCommand or update through backend."""
        if self._command_bus:
            from shusha.application.commands import PauseJobCommand

            try:
                self._command_bus.dispatch(PauseJobCommand(job_id=job_id))
            except Exception as e:
                logger.warning("Failed to dispatch PauseJobCommand: %s", e)
        elif self._backend_registry:
            job = self._jobs.get(job_id)
            if job:
                backend = self._backend_registry.get(job.backend_id)
                if backend:
                    backend.pause_job(job_id)
                    self.update_job(job.transition_to(DownloadState.PAUSED))

    def action_resume_job(self, job_id: JobId) -> None:
        """Dispatch ResumeJobCommand or update through backend."""
        if self._command_bus:
            from shusha.application.commands import ResumeJobCommand

            try:
                self._command_bus.dispatch(ResumeJobCommand(job_id=job_id))
            except Exception as e:
                logger.warning("Failed to dispatch ResumeJobCommand: %s", e)
        elif self._backend_registry:
            job = self._jobs.get(job_id)
            if job:
                backend = self._backend_registry.get(job.backend_id)
                if backend:
                    backend.resume_job(job_id)
                    self.update_job(job.transition_to(DownloadState.ACTIVE))

    def action_remove_job(self, job_id: JobId) -> None:
        """Dispatch RemoveJobCommand or update through backend."""
        if self._command_bus:
            from shusha.application.commands import RemoveJobCommand

            try:
                self._command_bus.dispatch(RemoveJobCommand(job_id=job_id))
            except Exception as e:
                logger.warning("Failed to dispatch RemoveJobCommand: %s", e)
        elif self._backend_registry:
            job = self._jobs.get(job_id)
            if job:
                backend = self._backend_registry.get(job.backend_id)
                if backend:
                    backend.remove_job(job_id)
                    self.remove_job(job_id)

    def action_retry_job(self, job_id: JobId) -> None:
        """Dispatch RetryJobCommand or restart job."""
        if self._command_bus:
            from shusha.application.commands import RetryJobCommand

            try:
                self._command_bus.dispatch(RetryJobCommand(job_id=job_id))
            except Exception as e:
                logger.warning("Failed to dispatch RetryJobCommand: %s", e)
        elif self._backend_registry:
            job = self._jobs.get(job_id)
            if job:
                backend = self._backend_registry.get(job.backend_id)
                if backend:
                    active = backend.submit_job(job.transition_to(DownloadState.ACTIVE))
                    self.update_job(active)

    def on_domain_event(self, event: DomainEvent) -> None:
        """Alias to handle_domain_event."""
        self.handle_domain_event(event)

    def refresh_jobs(self) -> None:
        """Force refresh of all rows."""
        self._refresh_all_rows()

    def pause_selected(self) -> None:
        """Pause the currently selected job in table."""
        jid = self.get_selected_job_id()
        if jid:
            self.action_pause_job(jid)

    def resume_selected(self) -> None:
        """Resume the currently selected job in table."""
        jid = self.get_selected_job_id()
        if jid:
            self.action_resume_job(jid)

    def remove_selected(self) -> None:
        """Remove the currently selected job in table."""
        jid = self.get_selected_job_id()
        if jid:
            self.action_remove_job(jid)


class JobMonitorScreen(Screen[None]):
    """Full screen for the live jobs monitor."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("space", "pause_resume", "Pause/Resume"),
        Binding("x", "remove_job", "Remove"),
        Binding("r", "retry_job", "Retry"),
    ]

    def __init__(
        self,
        command_bus: CommandBus | None = None,
        query_bus: QueryBus | None = None,
        event_bus: EventBus | None = None,
        backend_registry: BackendRegistry | None = None,
        initial_jobs: Sequence[Job] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._event_bus = event_bus
        self._backend_registry = backend_registry
        self._initial_jobs = initial_jobs

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield JobMonitorView(
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            event_bus=self._event_bus,
            backend_registry=self._backend_registry,
            initial_jobs=self._initial_jobs,
            id="job-monitor-view",
        )

    def action_pause_resume(self) -> None:
        """Toggle pause/resume on selected job."""
        view = self.query_one("#job-monitor-view", JobMonitorView)
        jid = view.get_selected_job_id()
        if jid and jid in view._jobs:
            job = view._jobs[jid]
            if job.state == DownloadState.ACTIVE:
                view.action_pause_job(jid)
            elif job.state == DownloadState.PAUSED:
                view.action_resume_job(jid)

    def action_remove_job(self) -> None:
        """Remove selected job."""
        view = self.query_one("#job-monitor-view", JobMonitorView)
        jid = view.get_selected_job_id()
        if jid:
            view.action_remove_job(jid)

    def action_retry_job(self) -> None:
        """Retry selected job."""
        view = self.query_one("#job-monitor-view", JobMonitorView)
        jid = view.get_selected_job_id()
        if jid:
            view.action_retry_job(jid)
