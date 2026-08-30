"""Design system tokens and responsive layout engine for ttkbootstrap desktop (E11-I02, E11-I03)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResponsiveClass(StrEnum):
    """Responsive viewport classification."""

    COMPACT = "compact"  # < 768px (sidebar collapses to icons)
    STANDARD = "standard"  # 768px - 1199px (standard navigation and table)
    WIDE = "wide"  # 1200px - 1599px (expanded inspector panel)
    ULTRAWIDE = "ultrawide"  # >= 1600px (multi-column dashboard + live graphs)


@dataclass(frozen=True, slots=True)
class SpacingTokens:
    """Standardized spacing tokens in pixels."""

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    """Standardized typography definitions."""

    h1_size: int = 20
    h2_size: int = 16
    h3_size: int = 14
    body_size: int = 10
    small_size: int = 8
    mono_font: str = "Courier"
    ui_font: str = "Helvetica"


class ResponsiveLayoutEngine:
    """Determines active layout mode based on window dimensions."""

    BREAKPOINT_COMPACT: int = 768
    BREAKPOINT_STANDARD: int = 1200
    BREAKPOINT_WIDE: int = 1600

    @classmethod
    def get_responsive_class(cls, width: int) -> ResponsiveClass:
        """Classify window width into a responsive design class."""
        if width < cls.BREAKPOINT_COMPACT:
            return ResponsiveClass.COMPACT
        if width < cls.BREAKPOINT_STANDARD:
            return ResponsiveClass.STANDARD
        if width < cls.BREAKPOINT_WIDE:
            return ResponsiveClass.WIDE
        return ResponsiveClass.ULTRAWIDE
