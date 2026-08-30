# ADR-012: Textual Terminal TUI & Real-Time Diagnostics

## Status
Accepted

## Context
Headless servers, remote SSH sessions, and terminal power-users require full operational monitoring, media inspection, and system health checks without launching a graphical window.

## Decision
1. Technology: Use `textual` framework (`src/shusha/interfaces/tui/app.py`).
2. Tabbed Architecture:
   - Tab 1 (`1`): ⚡ Live Job Monitor (`JobMonitorView`) with real-time throughput and status filters.
   - Tab 2 (`2`): 📥 Acquisition Inbox (`InboxView`) for accepting or ignoring detected items.
   - Tab 3 (`3`): 🎬 Media Grabber (`MediaGrabberView`) for stream quality inspection and enqueuing.
   - Tab 4 (`4`): 🔍 Diagnostics (`DiagnosticsView`) inspecting daemon uptime and active backends.
   - Tab 5 (`5`): 🩺 System Doctor (`DoctorView`) probing platform health.
3. Modal Dialogs: `AddDownloadModal` for interactive URL/backend selection via keyboard hotkeys (`a`, `p`, `s`, `x`, `d`, `q`).

## Consequences
- **Positive**: First-class terminal interface sharing 100% of application commands and domain logic with GUI.
- **Positive**: Flicker-free reactive rendering via domain event subscriptions.
