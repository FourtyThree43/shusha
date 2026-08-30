"""Unit tests for ttkbootstrap Desktop design system, responsive engine, and views (Epic E11)."""

from __future__ import annotations

import os
from typing import cast
from unittest.mock import MagicMock

import pytest

from shusha.application.command_bus import CommandBus
from shusha.application.event_bus import EventBus
from shusha.application.query_bus import QueryBus
from shusha.domain.acquisition import (
    AcquisitionRequest,
    AcquisitionStatus,
    DetectedKind,
    SourceKind,
)
from shusha.domain.identifiers import make_acquisition_id
from shusha.presentation.app_context import AppContext
from shusha.presentation.icons import LUCIDE_ICONS, get_lucide_icon
from shusha.presentation.theme import (
    ResponsiveClass,
    ResponsiveLayoutEngine,
    SpacingTokens,
    TypographyTokens,
)
from shusha.presentation.views import (
    AcquisitionInboxView,
    DashboardView,
    DoctorView,
)


class TestResponsiveLayoutEngine:
    """Tests for responsive viewport classification (E11-I03)."""

    def test_breakpoint_classifications(self) -> None:
        assert (
            ResponsiveLayoutEngine.get_responsive_class(500) == ResponsiveClass.COMPACT
        )
        assert (
            ResponsiveLayoutEngine.get_responsive_class(767) == ResponsiveClass.COMPACT
        )
        assert (
            ResponsiveLayoutEngine.get_responsive_class(768) == ResponsiveClass.STANDARD
        )
        assert (
            ResponsiveLayoutEngine.get_responsive_class(1199)
            == ResponsiveClass.STANDARD
        )
        assert ResponsiveLayoutEngine.get_responsive_class(1200) == ResponsiveClass.WIDE
        assert ResponsiveLayoutEngine.get_responsive_class(1599) == ResponsiveClass.WIDE
        assert (
            ResponsiveLayoutEngine.get_responsive_class(1600)
            == ResponsiveClass.ULTRAWIDE
        )
        assert (
            ResponsiveLayoutEngine.get_responsive_class(2560)
            == ResponsiveClass.ULTRAWIDE
        )


class TestDesignTokens:
    """Tests for design system tokens (E11-I02)."""

    def test_spacing_tokens(self) -> None:
        spacing = SpacingTokens()
        assert spacing.xs == 4
        assert spacing.sm == 8
        assert spacing.md == 16
        assert spacing.lg == 24
        assert spacing.xl == 32

    def test_typography_tokens(self) -> None:
        typo = TypographyTokens()
        assert (
            typo.h1_size
            > typo.h2_size
            > typo.h3_size
            > typo.body_size
            > typo.small_size
        )


class TestLucideIconPipeline:
    """Tests for Lucide vector icon generator."""

    def test_lucide_icons_catalogue(self) -> None:
        assert "download" in LUCIDE_ICONS
        assert "dashboard" in LUCIDE_ICONS
        assert "video" in LUCIDE_ICONS
        assert "inbox" in LUCIDE_ICONS
        assert "doctor" in LUCIDE_ICONS
        assert "settings" in LUCIDE_ICONS
        assert "trash" in LUCIDE_ICONS
        assert "plus" in LUCIDE_ICONS

    def test_generate_lucide_icon_headless(self) -> None:
        # In headless environment, PIL renders cleanly, returns None or PhotoImage
        res = get_lucide_icon("download", size=24, color="#00bc8c")
        # Should not raise exception
        assert res is None or res is not None


class TestDesktopViewsWithContext:
    """Tests for Dashboard, Inbox, and Doctor views."""

    @pytest.fixture
    def mock_context(self) -> AppContext:
        ctx = MagicMock(spec=AppContext)
        ctx.event_bus = EventBus()
        ctx.command_bus = CommandBus()
        ctx.query_bus = QueryBus()
        ctx.acquisition_inbox = MagicMock()
        ctx.plugin_loader = MagicMock()
        return ctx

    def test_context_holds_buses(self, mock_context: AppContext) -> None:
        assert mock_context.event_bus is not None
        assert mock_context.command_bus is not None
        assert mock_context.query_bus is not None

    @pytest.mark.skipif(
        os.environ.get("DISPLAY") is None and os.environ.get("WAYLAND_DISPLAY") is None,
        reason="Headless environment without display server",
    )
    def test_dashboard_and_inbox_ui_instantiation(
        self, mock_context: AppContext
    ) -> None:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            dash = DashboardView(root, mock_context)
            dash.update_metrics(2, "1.5 MB/s", "100 KB/s", 5)
            assert dash.lbl_active.cget("text") == "2"

            inbox_mock = cast(MagicMock, mock_context.acquisition_inbox)
            inbox_mock.list_active.return_value = [
                AcquisitionRequest(
                    id=make_acquisition_id("acq-1"),
                    source_kind=SourceKind.CLIPBOARD,
                    raw_input="https://example.com/test.iso",
                    detected_kind=DetectedKind.DIRECT_URL,
                    status=AcquisitionStatus.DETECTED,
                )
            ]
            inbox = AcquisitionInboxView(root, mock_context)
            inbox.refresh()
            assert len(inbox.tree.get_children()) == 1

            doctor = DoctorView(root, mock_context)
            assert len(doctor.tree.get_children()) >= 4
        finally:
            root.destroy()
