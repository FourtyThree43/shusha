"""Shusha Textual TUI interface package."""

from __future__ import annotations

from shusha.interfaces.tui.app import ShushaTUIApp
from shusha.interfaces.tui.screens.diagnostics import DiagnosticsScreen, DiagnosticsView
from shusha.interfaces.tui.screens.doctor import DoctorScreen, DoctorView
from shusha.interfaces.tui.screens.job_monitor import JobMonitorScreen, JobMonitorView

__all__ = [
    "DiagnosticsScreen",
    "DiagnosticsView",
    "DoctorScreen",
    "DoctorView",
    "JobMonitorScreen",
    "JobMonitorView",
    "ShushaTUIApp",
]
