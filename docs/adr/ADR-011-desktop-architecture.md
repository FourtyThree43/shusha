# ADR-011: ttkbootstrap Desktop Architecture & Lucide Icon Pipeline

## Status
Accepted

## Context
Desktop GUI requires a modern visual aesthetic, responsiveness across diverse window resolutions, dark/light theme switching, and high-DPI clarity without external web font dependencies or web rendering runtimes (Electron).

## Decision
1. Technology: Use `ttkbootstrap` atop standard Tkinter.
2. Architecture: MVVM with ViewModels / AppContext (`src/shusha/presentation/app_context.py`) and UI dispatcher (`UiDispatcher`) marshaling asynchronous background worker updates onto the Tk main thread.
3. Design System Tokens: Standardized `SpacingTokens`, `TypographyTokens`, and `ResponsiveLayoutEngine` (`Compact`, `Standard`, `Wide`, `UltraWide`).
4. Icon Engine: Pure-vector Lucide SVG coordinate rendering in `src/shusha/presentation/icons.py` with 4x anti-aliased Lanczos downsampling.
5. Navigation: Multi-view stack (Dashboard, Transfers, Acquisition Inbox, Media Grabber, Plugins, System Doctor).

## Consequences
- **Positive**: Lightweight memory footprint (< 40MB RAM) with instant startup.
- **Positive**: Native OS widgets with zero external font asset requirements.
