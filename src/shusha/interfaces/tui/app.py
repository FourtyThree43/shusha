"""Shusha Textual TUI Application Shell (Epic E12 Modern UI/UX)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, TabbedContent, TabPane

from shusha.acquisition.inbox import AcquisitionInbox
from shusha.application.command_bus import CommandBus
from shusha.application.commands import CreateJobCommand
from shusha.application.event_bus import EventBus
from shusha.application.query_bus import QueryBus
from shusha.backends.fake import FakeBackend
from shusha.backends.registry import BackendRegistry
from shusha.domain.events import DomainEvent
from shusha.domain.identifiers import make_backend_id
from shusha.domain.job import Job
from shusha.interfaces.tui.screens.add_modal import AddDownloadModal
from shusha.interfaces.tui.screens.diagnostics import (
    DiagnosticsScreen,
    DiagnosticsView,
)
from shusha.interfaces.tui.screens.doctor import DoctorScreen, DoctorView
from shusha.interfaces.tui.screens.inbox_screen import InboxView
from shusha.interfaces.tui.screens.job_monitor import (
    JobMonitorScreen,
    JobMonitorView,
)
from shusha.interfaces.tui.screens.media_grabber_screen import MediaGrabberView

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ShushaTUIApp(App[None]):
    """Textual TUI application displaying backend-neutral state with zero-flicker live updates."""

    TITLE = "Shusha 2"
    SUB_TITLE = "Universal Download Acquisition & Orchestration Platform"

    CSS = """
    Screen {
        background: $background;
        color: $text;
    }

    TabbedContent {
        height: 1fr;
    }

    ContentTab {
        min-width: 14;
        text-style: bold;
    }

    TabPane {
        padding: 0;
        margin: 0;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("1", "switch_tab('tab-jobs')", "Jobs"),
        Binding("2", "switch_tab('tab-inbox')", "Inbox"),
        Binding("3", "switch_tab('tab-media')", "Media"),
        Binding("4", "switch_tab('tab-diagnostics')", "Diagnostics"),
        Binding("5", "switch_tab('tab-doctor')", "Doctor"),
        Binding("a", "add_download", "Add Download"),
        Binding("r", "refresh_active_view", "Refresh"),
        Binding("p", "pause_selected_job", "Pause"),
        Binding("s", "resume_selected_job", "Resume"),
        Binding("x", "remove_selected_job", "Remove"),
    ]

    SCREENS: ClassVar[dict[str, type[Screen[Any]]]] = {
        "job_monitor": JobMonitorScreen,
        "diagnostics": DiagnosticsScreen,
        "doctor": DoctorScreen,
    }

    def __init__(
        self,
        event_bus: EventBus | None = None,
        command_bus: CommandBus | None = None,
        query_bus: QueryBus | None = None,
        backend_registry: BackendRegistry | None = None,
        acquisition_inbox: AcquisitionInbox | None = None,
        initial_jobs: Sequence[Job] | None = None,
        driver_class: type[Any] | None = None,
        css_path: str | None = None,
        watch_css: bool = False,
    ) -> None:
        super().__init__(
            driver_class=driver_class, css_path=css_path, watch_css=watch_css
        )
        self.event_bus = event_bus or EventBus()
        self.command_bus = command_bus or CommandBus()
        self.query_bus = query_bus or QueryBus()
        self.backend_registry = backend_registry or BackendRegistry()
        self.acquisition_inbox = acquisition_inbox or AcquisitionInbox()
        self._initial_jobs = initial_jobs or []
        self._unsubscribe_bus: Callable[[], None] | None = None

        if not self.backend_registry.list_backends():
            self.backend_registry.register(FakeBackend(), default=True)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-jobs", id="app-tabs"):
            with TabPane("⚡ Transfers (1)", id="tab-jobs"):
                yield JobMonitorView(
                    command_bus=self.command_bus,
                    query_bus=self.query_bus,
                    event_bus=self.event_bus,
                    backend_registry=self.backend_registry,
                    initial_jobs=self._initial_jobs,
                    id="view-job-monitor",
                )
            with TabPane("📥 Inbox (2)", id="tab-inbox"):
                yield InboxView(
                    inbox=self.acquisition_inbox,
                    id="view-inbox",
                )
            with TabPane("🎬 Media Grabber (3)", id="tab-media"):
                yield MediaGrabberView(
                    command_bus=self.command_bus,
                    id="view-media-grabber",
                )
            with TabPane("🔍 Diagnostics (4)", id="tab-diagnostics"):
                yield DiagnosticsView(
                    backend_registry=self.backend_registry,
                    id="view-diagnostics",
                )
            with TabPane("🩺 Doctor (5)", id="tab-doctor"):
                yield DoctorView(id="view-doctor")
        yield Footer()

    def on_mount(self) -> None:
        """Subscribe to global event stream for zero-flicker reactive updates."""
        self._unsubscribe_bus = self.event_bus.subscribe_all(self._on_bus_event)

    def on_unmount(self) -> None:
        if self._unsubscribe_bus:
            self._unsubscribe_bus()

    def _on_bus_event(self, event: DomainEvent) -> None:
        """Forward domain events to active views."""
        try:
            job_view = self.query_one("#view-job-monitor", JobMonitorView)
            job_view.on_domain_event(event)
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch the visible active tab."""
        tabs = self.query_one("#app-tabs", TabbedContent)
        tabs.active = tab_id

    def action_add_download(self) -> None:
        """Open the Add Download modal dialog."""

        def on_modal_result(result: dict[str, str] | None) -> None:
            if result and result.get("url"):
                url = result["url"]
                backend_str = result.get("backend", "auto")
                backend_id = make_backend_id(
                    backend_str if backend_str != "auto" else "aria2"
                )
                cmd = CreateJobCommand(
                    name=url.split("/")[-1] or "download.bin",
                    source_input=url,
                    backend_id=backend_id,
                )
                self.command_bus.dispatch(cmd)

        self.push_screen(AddDownloadModal(), callback=on_modal_result)

    def action_refresh_active_view(self) -> None:
        """Refresh current visible tab."""
        tabs = self.query_one("#app-tabs", TabbedContent)
        if tabs.active == "tab-jobs":
            self.query_one("#view-job-monitor", JobMonitorView).refresh_jobs()
        elif tabs.active == "tab-inbox":
            self.query_one("#view-inbox", InboxView).refresh_items()
        elif tabs.active == "tab-doctor":
            self.query_one("#view-doctor", DoctorView).refresh_diagnostics()

    def action_pause_selected_job(self) -> None:
        self.query_one("#view-job-monitor", JobMonitorView).pause_selected()

    def action_resume_selected_job(self) -> None:
        self.query_one("#view-job-monitor", JobMonitorView).resume_selected()

    def action_remove_selected_job(self) -> None:
        self.query_one("#view-job-monitor", JobMonitorView).remove_selected()


def run_tui() -> None:
    """Entry point for standalone shusha-tui invocation."""
    app = ShushaTUIApp()
    app.run()
