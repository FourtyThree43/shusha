"""Diagnostics screen and widget inspecting engines, uptime, and active jobs (Epic E12-I04)."""

from __future__ import annotations

import logging
import platform
import time
from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Static

from shusha.backends.contract import BackendDiagnostics, BackendProtocol
from shusha.backends.registry import BackendRegistry

if TYPE_CHECKING:
    from shusha.application.query_bus import QueryBus

logger = logging.getLogger(__name__)


class DiagnosticsSummaryBar(Static):
    """Global system and backend diagnostics summary."""

    def update_summary(
        self,
        total_backends: int,
        healthy_backends: int,
        total_active_jobs: int,
        start_time: float,
    ) -> None:
        """Update aggregate diagnostic metrics."""
        uptime_sec = max(0.0, time.time() - start_time)
        hrs = int(uptime_sec // 3600)
        mins = int((uptime_sec % 3600) // 60)
        secs = int(uptime_sec % 60)
        uptime_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

        health_badge = (
            "[bold green]ALL HEALTHY[/bold green]"
            if total_backends > 0 and total_backends == healthy_backends
            else f"[bold yellow]{healthy_backends}/{total_backends} HEALTHY[/bold yellow]"
            if healthy_backends > 0
            else "[bold red]DEGRADED[/bold red]"
        )

        content = (
            f"[bold]Backends:[/bold] {total_backends} registered │ "
            f"[bold]Status:[/bold] {health_badge} │ "
            f"[bold]Active Jobs:[/bold] {total_active_jobs} │ "
            f"[bold]System Uptime:[/bold] {uptime_str} │ "
            f"[bold]Platform:[/bold] {platform.system()} {platform.machine()}"
        )
        self.update(content)


class DiagnosticsView(Widget):
    """Diagnostics inspection view for registered backends and system metrics."""

    DEFAULT_CSS = """
    DiagnosticsView {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    #diag-summary {
        background: $surface-darken-1;
        padding: 0 1;
        height: 1;
        border-bottom: solid $primary-darken-3;
    }

    #diag-toolbar {
        height: 3;
        padding: 0 1;
        align: left middle;
        background: $surface;
    }

    .diag-btn {
        margin-right: 1;
        min-width: 14;
        height: 1;
    }

    #diag-table {
        height: 1fr;
    }

    #diag-details {
        height: 8;
        padding: 1;
        background: $surface-darken-2;
        border-top: solid $primary-darken-3;
        overflow-y: auto;
    }
    """

    def __init__(
        self,
        backend_registry: BackendRegistry | None = None,
        query_bus: QueryBus | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._backend_registry = backend_registry or BackendRegistry()
        self._query_bus = query_bus
        self._start_time = time.time()
        self._cached_diagnostics: dict[
            str, tuple[BackendProtocol, BackendDiagnostics]
        ] = {}

    def compose(self) -> ComposeResult:
        yield DiagnosticsSummaryBar(id="diag-summary")
        with Horizontal(id="diag-toolbar"):
            yield Button(
                "↺ Refresh (r)",
                id="btn-diag-refresh",
                classes="diag-btn",
                variant="primary",
            )
            yield Button(
                "⚡ Ping All (p)",
                id="btn-diag-ping",
                classes="diag-btn",
                variant="default",
            )

        yield DataTable(id="diag-table", cursor_type="row", zebra_stripes=True)
        yield Static(
            "Select a backend row above to inspect detailed capabilities and options.",
            id="diag-details",
        )

    def on_mount(self) -> None:
        """Configure table columns and perform initial diagnostics query."""
        table = self.query_one("#diag-table", DataTable)
        table.add_column("Backend ID", key="id")
        table.add_column("Engine Name", key="name")
        table.add_column("Version", key="version")
        table.add_column("Health", key="health")
        table.add_column("Ping", key="ping")
        table.add_column("Active Jobs", key="active_jobs")
        table.add_column("Capabilities", key="capabilities")

        self.refresh_diagnostics()

    def refresh_diagnostics(self) -> None:
        """Query diagnostics from all registered backends and update table."""
        backends = self._backend_registry.list_backends()
        total_active = 0
        healthy_count = 0
        self._cached_diagnostics.clear()

        try:
            table = self.query_one("#diag-table", DataTable)
        except Exception:
            return

        table.clear()

        for backend in backends:
            bid = str(backend.identity.id)
            try:
                ping_ok = backend.ping()
            except Exception:
                ping_ok = False

            try:
                diag = backend.get_diagnostics()
            except Exception as e:
                diag = BackendDiagnostics(healthy=False, details={"error": str(e)})

            self._cached_diagnostics[bid] = (backend, diag)

            if diag.healthy and ping_ok:
                healthy_count += 1
                health_badge = "[bold green]HEALTHY[/bold green]"
            else:
                health_badge = "[bold red]DEGRADED[/bold red]"

            ping_str = "[green]ONLINE[/green]" if ping_ok else "[red]OFFLINE[/red]"
            total_active += diag.active_jobs

            caps = [
                str(c.value) if hasattr(c, "value") else str(c)
                for c in backend.capabilities
            ]
            cap_summary = ", ".join(caps[:3]) + (
                f" (+{len(caps) - 3})" if len(caps) > 3 else ""
            )

            table.add_row(
                bid,
                backend.identity.name,
                backend.identity.version,
                health_badge,
                ping_str,
                str(diag.active_jobs),
                cap_summary,
                key=bid,
            )

        try:
            summary = self.query_one("#diag-summary", DiagnosticsSummaryBar)
            summary.update_summary(
                total_backends=len(backends),
                healthy_backends=healthy_count,
                total_active_jobs=total_active,
                start_time=self._start_time,
            )
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle toolbar actions."""
        if event.button.id in ("btn-diag-refresh", "btn-diag-ping"):
            self.refresh_diagnostics()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Display extended backend details when a table row is clicked/selected."""
        val = getattr(event.row_key, "value", None)
        row_key = str(val) if val is not None else str(event.row_key)
        self._display_backend_detail(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Display extended backend details when navigation moves cursor."""
        if event.row_key:
            val = getattr(event.row_key, "value", None)
            row_key = str(val) if val is not None else str(event.row_key)
            self._display_backend_detail(row_key)

    def _display_backend_detail(self, backend_id: str) -> None:
        """Format and show comprehensive details in bottom pane."""
        if backend_id not in self._cached_diagnostics:
            return

        backend, diag = self._cached_diagnostics[backend_id]
        caps = [
            str(c.value) if hasattr(c, "value") else str(c)
            for c in backend.capabilities
        ]
        opts = [o.name for o in backend.get_supported_options()]

        detail_lines = [
            f"[bold cyan]{backend.identity.name}[/bold cyan] ({backend.identity.id}) — v{backend.identity.version} by {backend.identity.vendor or 'Unknown'}",
            f"[bold]Description:[/bold] {backend.identity.description or 'No description provided.'}",
            f"[bold]Capabilities ({len(caps)}):[/bold] [green]{', '.join(caps)}[/green]",
            f"[bold]Options ({len(opts)}):[/bold] {', '.join(opts[:8])}{' ...' if len(opts) > 8 else ''}",
        ]

        if diag.details:
            details_str = " │ ".join(
                f"[bold]{k}:[/bold] {v}" for k, v in diag.details.items()
            )
            detail_lines.append(f"[bold]Metrics:[/bold] {details_str}")

        try:
            details_widget = self.query_one("#diag-details", Static)
            details_widget.update("\n".join(detail_lines))
        except Exception:
            pass


class DiagnosticsScreen(Screen[None]):
    """Full screen for backend and system diagnostics."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("r", "refresh_data", "Refresh"),
    ]

    def __init__(
        self,
        backend_registry: BackendRegistry | None = None,
        query_bus: QueryBus | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._backend_registry = backend_registry
        self._query_bus = query_bus

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DiagnosticsView(
            backend_registry=self._backend_registry,
            query_bus=self._query_bus,
            id="diagnostics-view",
        )

    def action_refresh_data(self) -> None:
        """Refresh diagnostics view."""
        view = self.query_one("#diagnostics-view", DiagnosticsView)
        view.refresh_diagnostics()
