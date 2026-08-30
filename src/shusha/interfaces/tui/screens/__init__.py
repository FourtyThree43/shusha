"""Textual TUI screens package."""

from __future__ import annotations

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

__all__ = [
    "AddDownloadModal",
    "DiagnosticsScreen",
    "DiagnosticsView",
    "DoctorScreen",
    "DoctorView",
    "InboxView",
    "JobMonitorScreen",
    "JobMonitorView",
    "MediaGrabberView",
]
