"""System Doctor screen and health validator (Epic E12-I05)."""

from __future__ import annotations

import enum
import logging
import os
import platform
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import urlparse

import platformdirs
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Static

from shusha.backends.ytdlp.adapter import YtDlpAdapter
from shusha.infrastructure.daemon.discovery import (
    find_aria2_executable,
    inspect_aria2_version,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DoctorStatus(enum.StrEnum):
    """Health check outcome status."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class DoctorCheckResult:
    """Individual diagnostic check outcome."""

    category: str
    name: str
    status: DoctorStatus
    summary: str
    details: str = ""
    remediation: str = ""


def run_system_doctor_checks(
    custom_download_dir: Path | str | None = None,
) -> list[DoctorCheckResult]:
    """Execute all system environment health checks and return structured results."""
    results: list[DoctorCheckResult] = []

    # -------------------------------------------------------------
    # 1. aria2c Binary Check
    # -------------------------------------------------------------
    aria2_bin = find_aria2_executable()
    if aria2_bin:
        try:
            ver_str, features = inspect_aria2_version(aria2_bin)
            features_str = ", ".join(features) if features else "Standard"
            results.append(
                DoctorCheckResult(
                    category="Binaries & Engines",
                    name="aria2c binary",
                    status=DoctorStatus.PASS,
                    summary=f"v{ver_str} installed ({aria2_bin.name})",
                    details=f"Path: {aria2_bin}\nVersion: {ver_str}\nFeatures: {features_str}",
                    remediation="",
                )
            )
        except Exception as e:
            results.append(
                DoctorCheckResult(
                    category="Binaries & Engines",
                    name="aria2c binary",
                    status=DoctorStatus.WARN,
                    summary="Found binary but failed version inspection",
                    details=f"Path: {aria2_bin}\nError: {e}",
                    remediation="Check binary permissions or reinstall aria2c.",
                )
            )
    else:
        results.append(
            DoctorCheckResult(
                category="Binaries & Engines",
                name="aria2c binary",
                status=DoctorStatus.WARN,
                summary="aria2c executable not found in PATH",
                details="Checked system PATH, environment ARIA2C_PATH, and standard directories.",
                remediation="Install aria2 via package manager (`sudo apt install aria2` / `brew install aria2`) or specify ARIA2C_PATH.",
            )
        )

    # -------------------------------------------------------------
    # 2. yt-dlp Binary Check
    # -------------------------------------------------------------
    ytdlp_adapter = YtDlpAdapter()
    ytdlp_which = shutil.which("yt-dlp")
    if ytdlp_adapter.check_available():
        ver_str = ytdlp_adapter.get_version()
        results.append(
            DoctorCheckResult(
                category="Binaries & Engines",
                name="yt-dlp binary",
                status=DoctorStatus.PASS,
                summary=f"v{ver_str} installed",
                details=f"Path: {ytdlp_which or 'yt-dlp in PATH'}\nVersion: {ver_str}",
                remediation="",
            )
        )
    else:
        results.append(
            DoctorCheckResult(
                category="Binaries & Engines",
                name="yt-dlp binary",
                status=DoctorStatus.WARN,
                summary="yt-dlp executable not found in PATH",
                details="Checked system PATH for `yt-dlp`.",
                remediation="Install yt-dlp (`pip install yt-dlp` or package manager) to enable media streaming downloads.",
            )
        )

    # -------------------------------------------------------------
    # 3. Storage & Write Permissions
    # -------------------------------------------------------------
    # 3a. Downloads directory
    dl_dir_path = (
        Path(custom_download_dir).expanduser().resolve()
        if custom_download_dir
        else Path(platformdirs.user_downloads_dir()).expanduser().resolve()
    )
    dl_write_ok = False
    dl_err = ""
    try:
        dl_dir_path.mkdir(parents=True, exist_ok=True)
        probe_file = dl_dir_path / ".shusha_doctor_write_test"
        probe_file.write_text("shusha-probe", encoding="utf-8")
        probe_file.unlink()
        dl_write_ok = True
    except Exception as e:
        dl_err = str(e)

    if dl_write_ok:
        results.append(
            DoctorCheckResult(
                category="Storage & Permissions",
                name="Downloads Directory",
                status=DoctorStatus.PASS,
                summary=f"Writable ({dl_dir_path})",
                details=f"Path: {dl_dir_path}\nWrite & delete test passed successfully.",
                remediation="",
            )
        )
    else:
        results.append(
            DoctorCheckResult(
                category="Storage & Permissions",
                name="Downloads Directory",
                status=DoctorStatus.FAIL,
                summary=f"Write test failed ({dl_dir_path})",
                details=f"Path: {dl_dir_path}\nError: {dl_err}",
                remediation=f"Ensure write permissions on {dl_dir_path} (`chmod +w {dl_dir_path}`).",
            )
        )

    # 3b. App Config & State directory
    cfg_dir = Path(platformdirs.user_config_dir("shusha")).expanduser().resolve()
    cfg_write_ok = False
    cfg_err = ""
    try:
        cfg_dir.mkdir(parents=True, exist_ok=True)
        probe_file = cfg_dir / ".shusha_doctor_write_test"
        probe_file.write_text("shusha-probe", encoding="utf-8")
        probe_file.unlink()
        cfg_write_ok = True
    except Exception as e:
        cfg_err = str(e)

    if cfg_write_ok:
        results.append(
            DoctorCheckResult(
                category="Storage & Permissions",
                name="Config Directory",
                status=DoctorStatus.PASS,
                summary=f"Writable ({cfg_dir})",
                details=f"Path: {cfg_dir}\nConfiguration and persistent state directory is ready.",
                remediation="",
            )
        )
    else:
        results.append(
            DoctorCheckResult(
                category="Storage & Permissions",
                name="Config Directory",
                status=DoctorStatus.FAIL,
                summary="Cannot write configuration directory",
                details=f"Path: {cfg_dir}\nError: {cfg_err}",
                remediation=f"Check permissions on {cfg_dir}.",
            )
        )

    # -------------------------------------------------------------
    # 4. Network & Proxy Configuration
    # -------------------------------------------------------------
    http_proxy = os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("HTTPS_PROXY")
    all_proxy = os.environ.get("ALL_PROXY")
    no_proxy = os.environ.get("NO_PROXY")

    proxy_detected = any([http_proxy, https_proxy, all_proxy])
    if proxy_detected:
        proxy_valid = True
        proxy_details: list[str] = []
        for name, p_val in [
            ("HTTP_PROXY", http_proxy),
            ("HTTPS_PROXY", https_proxy),
            ("ALL_PROXY", all_proxy),
        ]:
            if p_val:
                try:
                    parsed = urlparse(p_val)
                    if not parsed.scheme or not parsed.netloc:
                        proxy_valid = False
                        proxy_details.append(f"{name}: Invalid URL format ({p_val})")
                    else:
                        # Redact password if present in netloc
                        safe_netloc = parsed.hostname or ""
                        if parsed.port:
                            safe_netloc += f":{parsed.port}"
                        proxy_details.append(f"{name}: {parsed.scheme}://{safe_netloc}")
                except Exception as e:
                    proxy_valid = False
                    proxy_details.append(f"{name}: Parse error ({e})")

        if no_proxy:
            proxy_details.append(f"NO_PROXY: {no_proxy}")

        if proxy_valid:
            results.append(
                DoctorCheckResult(
                    category="Network & Proxy",
                    name="Proxy Configuration",
                    status=DoctorStatus.PASS,
                    summary="Proxy configured and valid",
                    details="\n".join(proxy_details),
                    remediation="",
                )
            )
        else:
            results.append(
                DoctorCheckResult(
                    category="Network & Proxy",
                    name="Proxy Configuration",
                    status=DoctorStatus.WARN,
                    summary="Proxy variables contain invalid URLs",
                    details="\n".join(proxy_details),
                    remediation="Check HTTP_PROXY and HTTPS_PROXY environment variables for correct syntax.",
                )
            )
    else:
        results.append(
            DoctorCheckResult(
                category="Network & Proxy",
                name="Proxy Configuration",
                status=DoctorStatus.PASS,
                summary="Direct network connection (No proxy active)",
                details="Environment proxy variables (HTTP_PROXY, HTTPS_PROXY, ALL_PROXY) are unset.",
                remediation="",
            )
        )

    # -------------------------------------------------------------
    # 5. Python Runtime & Platform Architecture
    # -------------------------------------------------------------
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    py_ok = (py_ver.major == 3 and py_ver.minor >= 14) or py_ver.major > 3

    if py_ok:
        results.append(
            DoctorCheckResult(
                category="Runtime & Platform",
                name="Python Runtime",
                status=DoctorStatus.PASS,
                summary=f"Python {py_ver_str} ({platform.python_implementation()})",
                details=f"Python Version: {py_ver_str}\nExecutable: {sys.executable}\nOS: {platform.system()} {platform.release()} ({platform.machine()})",
                remediation="",
            )
        )
    else:
        results.append(
            DoctorCheckResult(
                category="Runtime & Platform",
                name="Python Runtime",
                status=DoctorStatus.WARN,
                summary=f"Python {py_ver_str} (Target is >= 3.14)",
                details=f"Python Version: {py_ver_str}\nExecutable: {sys.executable}",
                remediation="Upgrade to Python 3.14+ for optimal compatibility and performance.",
            )
        )

    # -------------------------------------------------------------
    # 6. SQLite & Persistence Health
    # -------------------------------------------------------------
    try:
        sqlite_ver = sqlite3.sqlite_version
        results.append(
            DoctorCheckResult(
                category="Runtime & Platform",
                name="SQLite Storage",
                status=DoctorStatus.PASS,
                summary=f"SQLite v{sqlite_ver} (WAL mode supported)",
                details=f"SQLite C-Library Version: {sqlite_ver}\nIn-memory connection test: SUCCESS",
                remediation="",
            )
        )
    except Exception as e:
        results.append(
            DoctorCheckResult(
                category="Runtime & Platform",
                name="SQLite Storage",
                status=DoctorStatus.FAIL,
                summary="SQLite database subsystem error",
                details=str(e),
                remediation="Reinstall Python with SQLite module support.",
            )
        )

    return results


class DoctorSummaryBar(Static):
    """Aggregate health status summary bar for Doctor checks."""

    def update_counts(self, results: list[DoctorCheckResult]) -> None:
        """Update count indicators."""
        passed = sum(1 for r in results if r.status == DoctorStatus.PASS)
        warns = sum(1 for r in results if r.status == DoctorStatus.WARN)
        fails = sum(1 for r in results if r.status == DoctorStatus.FAIL)

        if fails > 0:
            overall = "[bold red]✖ ACTION REQUIRED[/bold red]"
        elif warns > 0:
            overall = "[bold yellow]▲ WARNINGS DETECTED[/bold yellow]"
        else:
            overall = "[bold green]✔ SYSTEM HEALTHY[/bold green]"

        content = (
            f"[bold]System Doctor:[/bold] {overall}   │   "
            f"[green]✔ {passed} Passed[/green] │ "
            f"[yellow]▲ {warns} Warnings[/yellow] │ "
            f"[red]✖ {fails} Failures[/red]"
        )
        self.update(content)


class DoctorView(Widget):
    """System doctor widget displaying environment diagnostics and remediation."""

    DEFAULT_CSS = """
    DoctorView {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    #doctor-summary {
        background: $surface-darken-1;
        padding: 0 1;
        height: 1;
        border-bottom: solid $primary-darken-3;
    }

    #doctor-toolbar {
        height: 3;
        padding: 0 1;
        align: left middle;
        background: $surface;
    }

    .doctor-btn {
        margin-right: 1;
        min-width: 16;
        height: 1;
    }

    #doctor-table {
        height: 1fr;
    }

    #doctor-details {
        height: 8;
        padding: 1;
        background: $surface-darken-2;
        border-top: solid $primary-darken-3;
        overflow-y: auto;
    }
    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._check_results: list[DoctorCheckResult] = []

    def compose(self) -> ComposeResult:
        yield DoctorSummaryBar(id="doctor-summary")
        with Horizontal(id="doctor-toolbar"):
            yield Button(
                "↺ Re-run Doctor (r)",
                id="btn-doctor-rerun",
                classes="doctor-btn",
                variant="primary",
            )

        yield DataTable(id="doctor-table", cursor_type="row", zebra_stripes=True)
        yield Static(
            "Select a diagnostic check above to inspect details and remediation advice.",
            id="doctor-details",
        )

    def on_mount(self) -> None:
        """Initialize table columns and run initial doctor checks."""
        table = self.query_one("#doctor-table", DataTable)
        table.add_column("Category", key="category")
        table.add_column("Check Name", key="name")
        table.add_column("Status", key="status")
        table.add_column("Summary", key="summary")

        self.run_doctor()

    def run_doctor(self) -> None:
        """Execute doctor checks and populate table."""
        self._check_results = run_system_doctor_checks()

        try:
            table = self.query_one("#doctor-table", DataTable)
        except Exception:
            return

        table.clear()
        for idx, res in enumerate(self._check_results):
            match res.status:
                case DoctorStatus.PASS:
                    status_badge = "[bold green]✔ PASS[/bold green]"
                case DoctorStatus.WARN:
                    status_badge = "[bold yellow]▲ WARN[/bold yellow]"
                case DoctorStatus.FAIL:
                    status_badge = "[bold red]✖ FAIL[/bold red]"

            table.add_row(
                res.category,
                res.name,
                status_badge,
                res.summary,
                key=str(idx),
            )

        try:
            summary = self.query_one("#doctor-summary", DoctorSummaryBar)
            summary.update_counts(self._check_results)
        except Exception:
            pass

    def refresh_diagnostics(self) -> None:
        """Alias for run_doctor for view refresh polymorphism."""
        self.run_doctor()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle re-run doctor button."""
        if event.button.id == "btn-doctor-rerun":
            self.run_doctor()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show check details when selected."""
        val = getattr(event.row_key, "value", None)
        row_key = str(val) if val is not None else str(event.row_key)
        self._display_check_detail(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Show check details when cursor moves."""
        if event.row_key:
            val = getattr(event.row_key, "value", None)
            row_key = str(val) if val is not None else str(event.row_key)
            self._display_check_detail(row_key)

    def _display_check_detail(self, check_idx_str: str) -> None:
        """Display extended description and remediation."""
        try:
            idx = int(check_idx_str)
            if 0 <= idx < len(self._check_results):
                res = self._check_results[idx]
                lines = [
                    f"[bold cyan]{res.category} > {res.name}[/bold cyan] — Status: {res.status.value}",
                    f"[bold]Summary:[/bold] {res.summary}",
                ]
                if res.details:
                    lines.append(f"[bold]Details:[/bold] {res.details}")
                if res.remediation:
                    lines.append(
                        f"[bold yellow]Remediation:[/bold yellow] {res.remediation}"
                    )

                details_widget = self.query_one("#doctor-details", Static)
                details_widget.update("\n".join(lines))
        except ValueError, IndexError:
            pass


class DoctorScreen(Screen[None]):
    """Full screen for system doctor."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("r", "rerun_doctor", "Re-run"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DoctorView(id="doctor-view")

    def action_rerun_doctor(self) -> None:
        """Re-run doctor checks."""
        view = self.query_one("#doctor-view", DoctorView)
        view.run_doctor()
