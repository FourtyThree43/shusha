# PLAN.md

# Shusha Rewrite — Master Implementation Plan

**Project:** Shusha  
**Backend:** aria2c  
**Language:** Python 3.14+  
**GUI:** Tkinter + ttk + ttkbootstrap  
**Toolchain:** Astral `uv`, Ruff, ty  
**Testing:** pytest / pytest-cov  
**Architecture:** Typed Clean Architecture / Ports & Adapters  
**UI scope:** 132 screens across 12 screen groups  
**Document status:** Authoritative implementation plan

---

# 1. Mission

Rewrite Shusha as a modern, typed, maintainable desktop download manager built on top of aria2c.

The new application must combine:

- complete practical aria2c functionality;
- a modern ttkbootstrap desktop experience;
- strong Python typing;
- predictable state management;
- resilient daemon/RPC integration;
- persistent application state;
- comprehensive testing;
- complete documentation;
- cross-platform support;
- accessibility-conscious interaction design.

This is a **rewrite**, not a cosmetic modernization.

The old implementation is evidence for behavior and compatibility, not the architectural foundation of the new application.

---

# 2. Technology Contract

## 2.1 Runtime

Required:

```text
Python >= 3.14
```

Use modern Python typing and language features.

---

## 2.2 GUI

The only supported GUI stack is:

```text
tkinter
ttk
ttkbootstrap
```

Do not introduce:

```text
CustomTkinter
PyQt
PySide
wxPython
Kivy
Electron
webview
```

The official visual framework is **ttkbootstrap**.

Native Tk/ttk widgets may be used where ttkbootstrap does not provide a suitable abstraction.

---

## 2.3 Toolchain

Use Astral tooling:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest --cov
uv build
```

Dependency management must be performed through `uv`.

---

# 3. Architectural Principles

The target dependency graph is:

```text
┌────────────────────────────────────────────────────────────┐
│                     PRESENTATION                           │
│ ttkbootstrap / ttk / Tkinter                               │
│ windows / dialogs / widgets / view models / navigation    │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                     APPLICATION                            │
│ commands / queries / services / orchestration              │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                       DOMAIN                               │
│ downloads / torrents / files / options / queue / schedules │
└──────────────────────────┬─────────────────────────────────┘
                           ▲
                           │
┌──────────────────────────┴─────────────────────────────────┐
│                    INFRASTRUCTURE                          │
│ aria2 RPC / daemon / database / filesystem / OS / network │
└────────────────────────────────────────────────────────────┘
```

### Mandatory rule

The domain must never import:

```text
tkinter
ttkbootstrap
subprocess
sqlite implementation
aria2 RPC transport
platform-specific APIs
```

The presentation layer must never directly call aria2.

---

# 4. Target Repository Tree

```text
src/shusha/
├── domain/
│   ├── download.py
│   ├── download_file.py
│   ├── download_source.py
│   ├── download_status.py
│   ├── torrent.py
│   ├── metalink.py
│   ├── peer.py
│   ├── server.py
│   ├── tracker.py
│   ├── checksum.py
│   ├── statistics.py
│   ├── category.py
│   ├── scheduler.py
│   ├── queue.py
│   ├── settings.py
│   ├── daemon.py
│   ├── capabilities.py
│   ├── events.py
│   └── errors.py
│
├── application/
│   ├── commands/
│   ├── queries/
│   ├── services/
│   ├── ports/
│   └── app.py
│
├── infrastructure/
│   ├── aria2/
│   │   ├── rpc/
│   │   ├── models/
│   │   ├── options/
│   │   ├── events/
│   │   └── capabilities/
│   ├── daemon/
│   ├── persistence/
│   ├── filesystem/
│   ├── networking/
│   ├── notifications/
│   └── os/
│
├── presentation/
│   ├── app.py
│   ├── router.py
│   ├── state.py
│   ├── actions.py
│   ├── bindings.py
│   ├── theme/
│   │   ├── tokens.py
│   │   ├── bootstrap.py
│   │   └── styles.py
│   ├── components/
│   ├── layouts/
│   ├── widgets/
│   ├── windows/
│   ├── dialogs/
│   ├── screens/
│   │   ├── dashboard/
│   │   ├── downloads/
│   │   ├── add_download/
│   │   ├── inspector/
│   │   ├── torrent/
│   │   ├── metalink/
│   │   ├── queue/
│   │   ├── scheduler/
│   │   ├── statistics/
│   │   ├── settings/
│   │   ├── daemon/
│   │   └── diagnostics/
│   └── accessibility/
│
├── platform/
└── shared/
```

---

# 5. UI Architecture

## 5.1 Core rule

A screen is a composition of:

```text
Screen
 ├── ViewModel / presentation state
 ├── Layout
 ├── reusable widgets
 ├── command bindings
 └── navigation metadata
```

A screen does not contain application business logic.

---

# 6. ttkbootstrap Architecture

## 6.1 Application root

Create one application root:

```python
class ShushaApplication(ttk.Window): ...
```

The root owns:

- ttkbootstrap theme;
- top-level menus;
- global keyboard bindings;
- application-level routing;
- notification host;
- modal manager;
- lifecycle;
- shutdown handling.

No child screen creates another application root.

---

## 6.2 Screen host

Implement:

```text
ScreenHost
```

as the central content region.

Responsibilities:

```text
navigate(screen_id)
replace(screen)
show_dialog(dialog)
close_dialog(dialog)
refresh_current()
```

Screens are mounted into the host.

---

## 6.3 Screen contract

Every screen implements a consistent protocol conceptually equivalent to:

```python
class Screen(Protocol):
    screen_id: str

    def mount(self, parent: ttk.Frame) -> None: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def dispose(self) -> None: ...
```

The concrete implementation may use classes rather than protocols, but lifecycle semantics must remain explicit.

---

# 7. Navigation Architecture

Primary navigation:

```text
Dashboard
Downloads
Queue
Scheduler
Statistics
Categories
Settings
Diagnostics
```

Secondary navigation is contextual.

Example:

```text
Downloads
 ├── All
 ├── Active
 ├── Waiting
 ├── Paused
 ├── Completed
 ├── Error
 └── Removed
```

Inspector navigation:

```text
Overview
Files
Peers
Servers
Trackers
Options
Hashes
Logs
```

---

# 8. Responsive Desktop Layout

Tkinter is not a responsive web framework. "Responsive" therefore means:

- sensible resizing;
- adaptive grid weights;
- minimum sizes;
- collapsible panels;
- optional compact modes;
- horizontal scrolling for dense data;
- dynamic column visibility;
- usable behavior at small desktop dimensions.

---

## 8.1 Supported logical sizes

Design and test at:

```text
1280 × 720
1440 × 900
1920 × 1080
2560 × 1440
```

Minimum supported main-window size:

```text
1100 × 700
```

Dialogs must define their own minimum dimensions.

---

## 8.2 Grid policy

Use:

```python
frame.grid_columnconfigure(0, weight=1)
frame.grid_rowconfigure(0, weight=1)
```

for primary expandable regions.

Avoid fixed pixel coordinates.

Do not use `place()` for normal application layout.

---

## 8.3 Layout priorities

When space becomes constrained:

1. preserve primary content;
2. preserve primary actions;
3. collapse secondary navigation;
4. hide optional metadata;
5. allow scrolling;
6. never truncate critical controls silently.

---

# 9. Main Shell Layout

The desktop shell is:

```text
┌───────────────────────────────────────────────────────────────┐
│ Application Menu                                               │
├───────────────────────────────────────────────────────────────┤
│ Toolbar                                                        │
├───────────────┬───────────────────────────────────────────────┤
│               │                                               │
│ Navigation    │                 ScreenHost                    │
│ Sidebar       │                                               │
│               │                                               │
│               │                                               │
├───────────────┴───────────────────────────────────────────────┤
│ Status / Connection / Speed / Active Tasks                    │
└───────────────────────────────────────────────────────────────┘
```

---

# 10. ttkbootstrap Widget Inventory

The implementation must standardize the following widget families.

## 10.1 Buttons

Required variants:

```text
PrimaryButton
SecondaryButton
DangerButton
SuccessButton
OutlineButton
IconButton
SplitButton
ToolbarButton
```

Implementation:

- subclass or wrapper around ttkbootstrap button primitives;
- centralized styles;
- tooltip support for icon-only buttons;
- keyboard focus;
- disabled state.

---

# 10.2 Navigation

```text
Sidebar
NavItem
NavSection
Breadcrumbs
TabBar
SubTabBar
```

Requirements:

- selected state;
- keyboard navigation;
- tooltip in collapsed mode;
- disabled state;
- notification badge.

---

# 10.3 Data presentation

```text
DownloadTree
DataTree
SortableTree
FileTree
PeerTable
ServerTable
TrackerTable
LogTable
StatisticsTable
```

Requirements:

- typed row model;
- column registry;
- sort state;
- selection state;
- contextual actions;
- incremental updates;
- virtualized/incremental refresh strategy where required.

---

# 10.4 Progress

```text
DownloadProgress
SegmentedProgress
CircularProgress
ProgressWithText
SpeedIndicator
EtaLabel
StatusBadge
```

No important state may be conveyed solely through color.

---

# 10.5 Forms

```text
ValidatedEntry
UrlEntry
PathEntry
NumericEntry
EnumSelector
BooleanSwitch
DurationEditor
SizeEditor
MultiValueEditor
OptionEditor
SecretEntry
```

Each field supports:

```text
label
description
validation
error state
disabled state
help
reset
```

---

# 10.6 Containers

```text
Card
SectionCard
Toolbar
Panel
CollapsiblePanel
InspectorPanel
StatusBar
EmptyState
ErrorState
LoadingState
```

---

# 10.7 Dialogs

```text
ConfirmDialog
ErrorDialog
WarningDialog
InfoDialog
InputDialog
ProgressDialog
SettingsDialog
CredentialDialog
ConnectionDialog
```

Every dialog provides:

```text
title
body
primary action
secondary action
keyboard behavior
validation
focus management
```

---

# 11. Design System

## 11.1 Design principles

The visual language should communicate:

```text
calm
technical
dense but readable
fast
reliable
predictable
professional
```

Avoid:

- excessive gradients;
- oversized cards;
- excessive rounded containers;
- decorative animation;
- information hidden behind unnecessary clicks.

---

# 11.2 ttkbootstrap Theme

The application must select one ttkbootstrap theme centrally.

Theme initialization occurs once.

Do not call theme configuration independently from individual screens.

---

# 11.3 Design tokens

Create:

```python
class DesignTokens: ...
```

covering:

```text
spacing
font sizes
line heights
control heights
border widths
corner radii where supported
icon sizes
sidebar width
toolbar height
status-bar height
```

All reusable components consume tokens.

---

# 11.4 Spacing scale

Base spacing:

```text
4
8
12
16
20
24
32
40
48
```

Avoid arbitrary spacing values unless required by native widget geometry.

---

# 11.5 Typography

Define:

```text
Display
Heading 1
Heading 2
Heading 3
Body
Body Small
Caption
Monospace
```

Use platform-appropriate system fonts.

Do not bundle a font unless explicitly required.

---

# 11.6 Status semantics

Standard status categories:

```text
success
info
warning
danger
neutral
active
paused
completed
error
offline
connecting
```

Status must have:

```text
icon + text
```

where feasible.

---

# 11.7 Icons

Use one coherent icon strategy.

Icon-only controls require tooltips and accessible names.

Do not mix arbitrary icon sets.

---

# 12. UI State Architecture

Every screen receives a presentation state.

Example:

```text
Loading
Ready
Empty
Error
Offline
Busy
```

Data state must be separate from widget state.

Do not use widget existence as application state.

---

# 13. ViewModel Rules

A screen ViewModel may expose:

```text
display values
formatted values
enabled states
visibility states
commands
selection
validation
```

It must not perform:

```text
RPC
database access
subprocess execution
filesystem mutation
```

---

# 14. Event Flow

Preferred flow:

```text
User interaction
      ↓
Widget command
      ↓
Application command
      ↓
Service
      ↓
Infrastructure
      ↓
Domain/application event
      ↓
Presentation state
      ↓
Widget update
```

Never:

```text
Button → RPC
```

---

# 15. Background Operations

Tkinter's UI thread must never block.

Long-running operations must execute outside the UI thread.

Examples:

```text
RPC
daemon startup
daemon shutdown
network calls
filesystem scanning
database migration
diagnostic generation
large imports
```

Background tasks must have:

```text
start
success
failure
cancellation
cleanup
```

---

# 16. Screen Catalogue

The application specification contains **132 screens across 12 groups**.

A "screen" means a meaningful application state/view that may be implemented as:

- a full window;
- a main-screen mode;
- a routed view;
- a wizard page;
- a modal dialog;
- a contextual inspector;
- a dedicated system state.

Screens sharing the same component architecture may reuse implementation.

---

# GROUP 01 — Application Shell & Navigation

**10 screens**

| ID | Screen | Type |
|---|---|---|
| S001 | Application Shell | Main |
| S002 | Collapsed Sidebar Shell | Main |
| S003 | Command Palette | Overlay |
| S004 | Global Search | Overlay |
| S005 | Keyboard Shortcuts | Dialog |
| S006 | Notification Center | Panel |
| S007 | About Shusha | Dialog |
| S008 | What's New | Dialog |
| S009 | Application Update Available | Dialog |
| S010 | Application Update Error | Dialog |

### Implementation

`presentation/screens/shell/`

The shell owns:

```text
menu
toolbar
sidebar
ScreenHost
status bar
notification host
```

---

# GROUP 02 — Dashboard

**8 screens**

| ID | Screen |
|---|---|
| S011 | Dashboard |
| S012 | Dashboard Empty |
| S013 | Dashboard Loading |
| S014 | Dashboard Offline |
| S015 | Dashboard RPC Error |
| S016 | Dashboard Compact |
| S017 | Dashboard Expanded Statistics |
| S018 | Dashboard Customization |

Dashboard widgets:

```text
Active Downloads
Waiting Downloads
Completed Today
Download Speed
Upload Speed
Disk Usage
Daemon Health
Recent Errors
```

---

# GROUP 03 — Downloads

**18 screens**

| ID | Screen |
|---|---|
| S019 | All Downloads |
| S020 | Active Downloads |
| S021 | Waiting Downloads |
| S022 | Paused Downloads |
| S023 | Completed Downloads |
| S024 | Error Downloads |
| S025 | Removed Downloads |
| S026 | Download Search Results |
| S027 | Download Filter Builder |
| S028 | Multi-selection Mode |
| S029 | Download Context Menu |
| S030 | Download Bulk Actions |
| S031 | Download Sort Configuration |
| S032 | Download Column Configuration |
| S033 | Downloads Loading |
| S034 | Downloads Empty |
| S035 | Downloads Offline |
| S036 | Downloads Error |

### Primary widget

```text
DownloadTree
```

Columns must be configurable.

Default columns:

```text
Name
Status
Size
Completed
Progress
Download Speed
Upload Speed
ETA
Connections
Category
```

---

# GROUP 04 — Add Download

**16 screens**

| ID | Screen |
|---|---|
| S037 | Add Download — Source |
| S038 | Add Download — URL List |
| S039 | Add Download — Magnet |
| S040 | Add Download — Torrent File |
| S041 | Add Download — Metalink |
| S042 | Add Download — Clipboard |
| S043 | Add Download — Destination |
| S044 | Add Download — File Selection |
| S045 | Add Download — HTTP Options |
| S046 | Add Download — FTP Options |
| S047 | Add Download — BitTorrent Options |
| S048 | Add Download — Metalink Options |
| S049 | Add Download — Authentication |
| S050 | Add Download — Advanced Options |
| S051 | Add Download — Review |
| S052 | Add Download — Submission Error |

### Wizard architecture

Implement:

```text
Wizard
 ├── WizardState
 ├── WizardPage
 ├── WizardNavigation
 ├── Validation
 └── SubmitCommand
```

Navigation:

```text
Back
Next
Cancel
Start
```

Pages must not directly invoke aria2.

---

# GROUP 05 — Download Inspector

**16 screens**

| ID | Screen |
|---|---|
| S053 | Inspector Overview |
| S054 | Inspector Files |
| S055 | Inspector Files Loading |
| S056 | Inspector Files Error |
| S057 | Inspector Peers |
| S058 | Inspector Servers |
| S059 | Inspector Trackers |
| S060 | Inspector Options |
| S061 | Inspector Advanced Options |
| S062 | Inspector Hashes |
| S063 | Inspector Sources |
| S064 | Inspector URIs |
| S065 | Inspector Logs |
| S066 | Inspector Statistics |
| S067 | Inspector Metadata |
| S068 | Inspector Error Detail |

Inspector layout:

```text
┌───────────────────────────────────────────────┐
│ Download Header                               │
├──────────────┬────────────────────────────────┤
│ Inspector    │ Content                        │
│ Navigation   │                                │
│              │                                │
└──────────────┴────────────────────────────────┘
```

---

# GROUP 06 — Queue & Categories

**10 screens**

| ID | Screen |
|---|---|
| S069 | Queue |
| S070 | Queue Empty |
| S071 | Queue Reordering |
| S072 | Queue Priority Editor |
| S073 | Category List |
| S074 | Category Detail |
| S075 | Create Category |
| S076 | Edit Category |
| S077 | Delete Category Confirmation |
| S078 | Category Assignment |

Queue controls:

```text
Move Top
Move Up
Move Down
Move Bottom
Priority
Pause
Resume
Remove
```

---

# GROUP 07 — Scheduler & Automation

**10 screens**

| ID | Screen |
|---|---|
| S079 | Scheduler |
| S080 | Scheduler Empty |
| S081 | Create Schedule |
| S082 | Edit Schedule |
| S083 | Schedule Time Editor |
| S084 | Bandwidth Schedule |
| S085 | Queue Schedule |
| S086 | Recurrence Editor |
| S087 | Schedule Conflict |
| S088 | Automation History |

Scheduler must support:

```text
time
day
recurrence
bandwidth
concurrency
pause/resume
queue behavior
```

---

# GROUP 08 — BitTorrent & Metalink

**10 screens**

| ID | Screen |
|---|---|
| S089 | Torrent Summary |
| S090 | Torrent File Selection |
| S091 | Torrent Peer Detail |
| S092 | Torrent Tracker Detail |
| S093 | Torrent Piece Map |
| S094 | Torrent Options |
| S095 | Magnet Metadata Loading |
| S096 | Magnet Metadata Error |
| S097 | Metalink Summary |
| S098 | Metalink Mirror/Checksum Detail |

---

# GROUP 09 — Statistics & Diagnostics

**10 screens**

| ID | Screen |
|---|---|
| S099 | Statistics Dashboard |
| S100 | Global Statistics |
| S101 | Download Statistics |
| S102 | Speed History |
| S103 | Server Statistics |
| S104 | Peer Statistics |
| S105 | Event Log |
| S106 | Error Log |
| S107 | Diagnostics |
| S108 | Export Diagnostics |

Charts must degrade gracefully if the environment does not support advanced charting.

The base UI must remain usable without introducing a heavyweight GUI chart framework.

---

# GROUP 10 — Settings & aria2 Options

**14 screens**

| ID | Screen |
|---|---|
| S109 | Settings Home |
| S110 | General Settings |
| S111 | Appearance Settings |
| S112 | Download Defaults |
| S113 | HTTP/HTTPS Settings |
| S114 | FTP/SFTP Settings |
| S115 | BitTorrent Settings |
| S116 | Metalink Settings |
| S117 | Proxy Settings |
| S118 | Authentication Settings |
| S119 | File/Filesystem Settings |
| S120 | RPC Settings |
| S121 | Advanced aria2 Options |
| S122 | Expert aria2 Options |

Settings must be generated from the authoritative option registry where practical.

---

# GROUP 11 — Daemon / Connection / Session

**10 screens**

| ID | Screen |
|---|---|
| S123 | Daemon Status |
| S124 | Start Daemon |
| S125 | Stop Daemon Confirmation |
| S126 | Restart Daemon |
| S127 | Local Daemon Configuration |
| S128 | Remote Daemon Configuration |
| S129 | RPC Authentication |
| S130 | Connection Test |
| S131 | Session Import |
| S132 | Session Recovery |

---

# GROUP 12 — System & Failure States

The catalogue's final group consists of **cross-cutting state variants** that are not additional numbered screens. These must be implemented across the preceding 132 routes.

Required states:

```text
Loading
Empty
No Results
Offline
Connecting
RPC Failure
Daemon Failure
Permission Denied
Authentication Failure
Validation Failure
Network Failure
Filesystem Failure
Unsupported Feature
aria2 Version Mismatch
Partial Success
Cancellation
Busy
Read-only
Recovery Required
Fatal Application Error
```

These states are part of the screen specification and must not be treated as optional polish.

---

# 17. Screen Implementation Contract

Every screen must define:

```text
screen ID
route
title
purpose
parent
layout
minimum size
state model
data dependencies
commands
queries
widgets
keyboard shortcuts
context menu
loading state
empty state
error state
offline state
validation
accessibility
tests
```

---

# 18. Screen Specification Template

Every screen document/code module must contain the equivalent of:

```text
## Screen

ID:
Route:
Title:

## Purpose

...

## Layout

...

## Components

...

## Data

...

## Commands

...

## Queries

...

## States

Loading:
Empty:
Error:
Offline:
Busy:

## Interactions

...

## Keyboard

...

## Accessibility

...

## Tests

...

## Dependencies

...
```

---

# 19. Download Table Specification

The download table is the application's primary information surface.

Implementation:

```text
DownloadTree
DownloadRowModel
DownloadColumn
DownloadTableState
DownloadTableController
```

---

## Required behavior

### Selection

Support:

```text
single
Ctrl/Cmd multi-select
Shift range-select
Select All
Clear Selection
```

### Sorting

Every sortable column must expose:

```text
ascending
descending
unsorted
```

### Filtering

Filters must be composable.

Example:

```text
status = ACTIVE
AND category = Movies
AND progress < 100%
```

### Search

Search must support at least:

```text
name
URI
GID
category
status
```

---

# 20. Inspector Specification

The inspector is a reusable contextual surface.

Header:

```text
Name
Status
Progress
Speed
ETA
GID
```

Actions:

```text
Pause
Resume
Retry
Remove
Open
Reveal
Copy URI
```

Tabs:

```text
Overview
Files
Peers
Servers
Trackers
Options
Hashes
Sources
URIs
Logs
Statistics
Metadata
```

---

# 21. Option Editor Architecture

Implement:

```text
OptionRegistry
OptionDefinition
OptionValue
OptionValidator
OptionFormatter
OptionEditorFactory
```

Mapping:

```text
aria2 option
      ↓
OptionDefinition
      ↓
OptionEditorFactory
      ↓
ttkbootstrap control
      ↓
validated OptionValue
      ↓
application command
      ↓
aria2 RPC
```

---

# 22. Option Widget Mapping

| aria2 type | UI |
|---|---|
| boolean | `BooleanSwitch` / Checkbutton |
| integer | `NumericEntry` |
| enum | Combobox |
| string | Entry |
| URL | `UrlEntry` |
| path | `PathEntry` |
| duration | `DurationEditor` |
| size | `SizeEditor` |
| list | `MultiValueEditor` |
| secret | `SecretEntry` |

Every editor must support:

```text
default
current
modified
reset
validation
help
```

---

# 23. Responsive Widget Rules

Reusable widgets must never assume their parent dimensions.

Bad:

```python
widget.place(x=300, y=100)
```

Preferred:

```python
widget.grid(...)
```

or:

```python
widget.pack(...)
```

Use:

```text
grid weights
sticky
padding
minsize
scrollable containers
PanedWindow
```

where appropriate.

---

# 24. Dense Information Layouts

For highly technical surfaces:

```text
Options
Peers
Servers
Trackers
Logs
Files
Statistics
```

use:

```text
toolbar
filter row
table
details panel
status footer
```

rather than a large collection of cards.

---

# 25. Adaptive Sidebar

Default width:

```text
220–260 px
```

Collapsed width:

```text
56–72 px
```

At narrow dimensions:

```text
sidebar → collapsed
```

Never hide navigation without providing a visible way to restore it.

---

# 26. Adaptive Inspector

The inspector uses a split view:

```text
wide:
navigation | content

medium:
navigation | content

narrow:
tabs across top
```

Do not maintain separate business implementations for each layout.

---

# 27. Scrolling

Use scrolling for:

```text
long settings pages
advanced options
logs
file lists
large forms
diagnostics
```

Scrolling must preserve keyboard focus.

---

# 28. Modal Rules

Use modal dialogs only when:

- confirmation is required;
- data entry is isolated;
- the operation is destructive;
- the user must resolve an error.

Do not use modal dialogs for ordinary navigation.

---

# 29. Notifications

Implement non-modal notifications for:

```text
download started
download completed
download paused
download failed
daemon connected
daemon disconnected
settings saved
configuration imported
diagnostics exported
```

Notifications must be dismissible and non-blocking.

---

# 30. Keyboard Architecture

Global shortcuts:

```text
Ctrl/Cmd+N     Add Download
Ctrl/Cmd+F     Search
Ctrl/Cmd+,     Settings
Ctrl/Cmd+R     Refresh
Ctrl/Cmd+A     Select All
Delete         Remove
Space          Pause/Resume
Enter          Open Inspector
Escape         Close dialog/clear selection
```

Exact platform conventions must be respected.

---

# 31. Accessibility Requirements

Every interactive element must have:

```text
accessible label
keyboard focus
visible focus
logical tab order
disabled state
error state
```

Color must not be the only status indicator.

Tables must expose meaningful column headings.

Icon-only buttons must have tooltips.

---

# 32. aria2 Specification Coverage

The rewrite must maintain a machine-readable compatibility matrix.

Required categories include:

```text
HTTP
HTTPS
FTP
SFTP
BitTorrent
Magnet
Metalink
cookies
authentication
proxy
checksum
file allocation
URI selection
connection management
bandwidth control
timeouts
retry
DNS
IPv4/IPv6
logging
console behavior
RPC
session management
hooks
security-related options
experimental options
deprecated options
```

---

# 33. RPC Coverage

The typed RPC layer must account for the complete relevant aria2 RPC API.

The implementation must cover operations for:

```text
adding downloads
adding torrents
adding metalinks
status
active downloads
waiting downloads
stopped downloads
pause
unpause
remove
remove result
change position
change options
get options
global options
tell files
tell peers
tell servers
global statistics
version
shutdown
session operations
```

The exact method set must be generated/verified against the project's pinned aria2 specification.

---

# 34. aria2 Capability Detection

The application must detect:

```text
aria2 version
RPC availability
supported methods
supported options
feature capabilities
```

The UI must gracefully handle unsupported functionality.

Example:

```text
Feature unavailable

Your aria2 version does not expose this capability.

Detected version: X
Required capability: Y
```

---

# 35. Daemon Architecture

Implement:

```text
DaemonDiscovery
DaemonConfiguration
DaemonCommandBuilder
DaemonSupervisor
DaemonHealthMonitor
DaemonConnection
```

Lifecycle:

```text
UNKNOWN
SEARCHING
FOUND
STARTING
RUNNING
UNHEALTHY
STOPPING
STOPPED
FAILED
```

---

# 36. Persistence Architecture

Repositories:

```text
DownloadRepository
SettingsRepository
CategoryRepository
ScheduleRepository
SessionRepository
```

Persistence must support:

```text
schema versions
migrations
transactions
atomic writes
recovery
backup
```

---

# 37. Security Architecture

Protect:

```text
RPC secrets
passwords
proxy credentials
HTTP authentication
cookies where sensitive
private URLs
diagnostic exports
logs
```

Sensitive data must be redacted.

---

# 38. Testing Architecture

```text
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   └── shared/
├── integration/
│   ├── aria2/
│   ├── daemon/
│   ├── persistence/
│   └── filesystem/
├── presentation/
│   ├── screens/
│   ├── widgets/
│   ├── navigation/
│   └── state/
├── e2e/
└── fixtures/
```

---

# 39. UI Testing Matrix

Every major screen must test:

```text
initial rendering
loading
empty
normal data
selection
primary action
secondary action
validation
error
offline
keyboard navigation
resize behavior
```

Not every state needs a separate test if covered through shared components, but every state must be exercised.

---

# 40. Component Test Matrix

Shared components require dedicated tests:

```text
Button
Sidebar
DataTree
DownloadTree
Progress
StatusBadge
ValidatedEntry
OptionEditor
Dialog
Wizard
Notification
CommandPalette
```

---

# 41. Performance Requirements

The UI must not rebuild the complete download table for every status event.

Prefer:

```text
event
 ↓
affected download
 ↓
row update
```

rather than:

```text
event
 ↓
fetch everything
 ↓
destroy table
 ↓
rebuild table
```

---

# 42. Refresh Strategy

aria2 polling must use a centralized scheduler.

Do not create one independent polling loop per screen.

The application should maintain a shared data/update stream.

Inactive screens may reduce refresh frequency where safe.

---

# 43. Event Coalescing

Rapid aria2 events must be coalesced where appropriate.

Example:

```text
100 progress updates
```

must not necessarily produce:

```text
100 complete widget-tree redraws
```

---

# 44. Documentation Architecture

Required documentation:

```text
README.md
CONTRIBUTING.md
SECURITY.md
docs/
├── architecture/
├── aria2/
├── api/
├── ui/
├── development/
└── audit/
```

---

# 45. UI Documentation

`docs/ui/SCREEN_CATALOGUE.md` must reproduce the authoritative screen inventory.

`docs/ui/DESIGN_SYSTEM.md` must document:

```text
themes
tokens
typography
spacing
components
states
layouts
accessibility
```

---

# 46. Machine-Readable UI Registry

Create a registry conceptually containing:

```text
screen_id
route
title
group
minimum_size
parent
components
states
commands
queries
```

This enables consistency checks.

---

# 47. UI Consistency Checker

Create:

```text
scripts/check_ui.py
```

It must detect:

```text
duplicate screen IDs
missing screen IDs
missing titles
unknown components
unknown routes
missing state declarations
```

---

# 48. aria2 Consistency Checker

Create:

```text
scripts/check_options.py
```

Validate:

```text
registry
implementation
UI
documentation
tests
```

---

# 49. Phase 0 — Repository Audit

## P0-001 — Baseline

**Dependencies:** none.

### Agent actions

Record:

- git state;
- Python;
- uv;
- aria2;
- dependency state;
- tests;
- lint;
- type checking;
- build.

### Acceptance criteria

`docs/audit/PHASE_0_FINDINGS.md` exists and records all failures.

---

## P0-002 — Source Inventory

**Dependencies:** P0-001.

Inventory every source file.

Acceptance:

Every file has:

```text
purpose
dependencies
feature
test coverage
rewrite disposition
```

---

## P0-003 — Existing UI Audit

**Dependencies:** P0-002.

Record every current:

```text
window
dialog
frame
widget
menu
toolbar
screen
state
```

Map them against S001–S132.

---

## P0-004 — Existing aria2 Audit

**Dependencies:** P0-002.

Map current aria2 functionality against the new option/RPC registry.

---

## P0-005 — Test Audit

**Dependencies:** P0-002.

Map tests to features.

---

## P0-006 — Documentation Audit

**Dependencies:** P0-002.

Inventory:

```text
README
docs
comments
examples
configuration documentation
aria2 references
```

---

# 50. EPIC 1 — aria2 Specification Registry

## P1-001 — Option Registry

Create the authoritative aria2 option registry.

Acceptance:

Every supported option has:

```text
name
type
default
scope
category
validation
RPC support
CLI support
sensitivity
documentation reference
version information
```

---

## P1-002 — RPC Registry

Create the complete typed RPC method registry.

---

## P1-003 — Event Registry

Create event/notification mappings.

---

## P1-004 — Capability Matrix

Map features to aria2 versions/capabilities.

---

# 51. EPIC 2 — Domain

## P2-001 — Download Model

Implement typed download entities/value objects.

## P2-002 — File Model

Implement file state and metadata.

## P2-003 — Torrent Model

Implement torrent entities.

## P2-004 — Metalink Model

Implement metalink entities.

## P2-005 — Peer/Server/Tracker Models

Implement connection entities.

## P2-006 — Queue Model

Implement queue state.

## P2-007 — Scheduler Model

Implement scheduling.

## P2-008 — Statistics Model

Implement statistics.

## P2-009 — Event Model

Implement typed events.

## P2-010 — Error Model

Implement structured application errors.

All issues require unit tests.

---

# 52. EPIC 3 — aria2 Infrastructure

## P3-001 — JSON-RPC Transport

Implement resilient typed JSON-RPC transport.

## P3-002 — RPC Serialization

Convert wire models into typed application representations.

## P3-003 — Typed RPC Client

Implement the complete RPC registry.

## P3-004 — Capability Detection

Implement version/capability negotiation.

## P3-005 — Event Subscription

Implement notification/event processing.

---

# 53. EPIC 4 — Daemon

## P4-001 — Executable Discovery

## P4-002 — Argument Builder

## P4-003 — Process Supervisor

## P4-004 — Health Monitor

## P4-005 — Local Profiles

## P4-006 — Remote Profiles

## P4-007 — Connection Test

---

# 54. EPIC 5 — Persistence

## P5-001 — Repository Contracts

## P5-002 — Database Schema

## P5-003 — Migration System

## P5-004 — Settings Persistence

## P5-005 — Category Persistence

## P5-006 — Schedule Persistence

## P5-007 — Session Persistence

## P5-008 — Import/Export

---

# 55. EPIC 6 — Application Services

## P6-001 — Composition Root

## P6-002 — Add Download

## P6-003 — Pause/Resume

## P6-004 — Remove

## P6-005 — Retry

## P6-006 — Queue Operations

## P6-007 — Option Management

## P6-008 — Inspector Queries

## P6-009 — Statistics Queries

## P6-010 — Scheduling

## P6-011 — Notifications

---

# 56. EPIC 7 — ttkbootstrap Foundation

## P7-001 — Theme Bootstrap

Create centralized ttkbootstrap initialization.

Acceptance:

No screen independently initializes a theme.

---

## P7-002 — Design Tokens

Create centralized tokens.

---

## P7-003 — Base Components

Implement:

```text
Card
Toolbar
StatusBadge
EmptyState
ErrorState
LoadingState
IconButton
ValidatedEntry
```

---

## P7-004 — Navigation

Implement:

```text
Sidebar
NavItem
Breadcrumbs
TabBar
ScreenHost
Router
```

---

## P7-005 — Main Shell

Implement S001–S010.

---

# 57. EPIC 8 — Downloads UI

**Dependencies:** P6, P7.

Implement:

```text
S019–S036
```

Acceptance:

All download states, filters, sorting, selection, context actions and keyboard interactions work.

---

# 58. EPIC 9 — Add Download UI

**Dependencies:** P6, P7, P8.

Implement:

```text
S037–S052
```

Acceptance:

All supported source types can enter the wizard.

---

# 59. EPIC 10 — Inspector UI

**Dependencies:** P6, P7, P8.

Implement:

```text
S053–S068
```

Acceptance:

Inspector data is loaded through application queries, never directly through RPC.

---

# 60. EPIC 11 — Queue, Categories & Scheduler UI

Implement:

```text
S069–S088
```

---

# 61. EPIC 12 — Torrent & Metalink UI

Implement:

```text
S089–S098
```

---

# 62. EPIC 13 — Statistics & Diagnostics UI

Implement:

```text
S099–S108
```

---

# 63. EPIC 14 — Settings & Option UI

Implement:

```text
S109–S122
```

The option editor must be registry-driven.

---

# 64. EPIC 15 — Daemon UI

Implement:

```text
S123–S132
```

while sharing the cross-cutting failure-state framework.

---

# 65. EPIC 16 — Security

Implement:

```text
secret storage
credential redaction
secure subprocess
filesystem validation
URL validation
diagnostic sanitization
```

---

# 66. EPIC 17 — Testing

Required:

```text
domain tests
application tests
RPC tests
daemon tests
persistence tests
UI component tests
screen tests
E2E tests
compatibility tests
```

---

# 67. EPIC 18 — Documentation

Update:

```text
README
architecture docs
aria2 compatibility docs
option matrix
RPC matrix
UI catalogue
design system
developer documentation
AI-agent documentation
troubleshooting
release documentation
```

---

# 68. EPIC 19 — Consistency Automation

Implement:

```text
check_options.py
check_ui.py
check_docs.py
architecture import checker
```

CI must fail on registry/documentation drift.

---

# 69. EPIC 20 — Packaging

Validate:

```text
uv build
installation
Windows
Linux
macOS
```

---

# 70. EPIC 21 — CI/CD

CI must execute:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv build
```

Use a supported multi-platform matrix.

---

# 71. EPIC 22 — Legacy Removal

Only after feature parity:

```text
legacy UI
legacy controllers
legacy RPC
legacy persistence
obsolete utilities
dead code
```

may be removed.

---

# 72. Dependency Graph

```text
P0 Audit
 │
 ├───────────────┐
 ▼               ▼
P1 aria2       P5 Persistence
 │               │
 ▼               │
P2 Domain ◄──────┘
 │
 ├───────────────┐
 ▼               ▼
P3 RPC          P4 Daemon
 │               │
 └───────┬───────┘
         ▼
        P6
 Application
         │
         ▼
        P7
 ttkbootstrap
         │
 ┌───────┼─────────┬─────────┐
 ▼       ▼         ▼         ▼
P8      P9        P10       P11
Downloads Add      Inspector Queue
 │
 ├──────────────┬───────────────┐
 ▼              ▼               ▼
P12            P13             P14
Torrent        Stats           Settings
 │              │               │
 └──────────────┴───────┬───────┘
                        ▼
                       P15
                      Daemon UI
                        │
                        ▼
                       P16
                     Security
                        │
                        ▼
                       P17
                     Testing
                        │
                        ▼
                       P18
                 Documentation
                        │
                        ▼
                       P19
                 Consistency Gates
                        │
                        ▼
                       P20
                    Packaging
                        │
                        ▼
                       P21
                       CI/CD
                        │
                        ▼
                       P22
                 Legacy Removal
```

---

# 73. Definition of Done — Code

An implementation issue is complete only when:

```text
[ ] implementation complete
[ ] architecture boundary correct
[ ] Python 3.14 compatible
[ ] typed
[ ] no unjustified Any
[ ] error handling complete
[ ] tests added
[ ] existing tests pass
[ ] UI states handled
[ ] accessibility considered
[ ] security considered
[ ] documentation updated
[ ] aria2 matrix updated
[ ] no unrelated changes
```

---

# 74. Definition of Done — UI

A screen is complete only when:

```text
[ ] screen ID registered
[ ] route registered
[ ] title defined
[ ] minimum size defined
[ ] normal state implemented
[ ] loading state implemented
[ ] empty state implemented
[ ] error state implemented
[ ] offline state implemented where relevant
[ ] resize behavior verified
[ ] keyboard behavior implemented
[ ] accessibility labels implemented
[ ] primary action implemented
[ ] secondary actions implemented
[ ] validation implemented
[ ] tests added
[ ] documentation updated
```

---

# 75. Definition of Done — aria2 Feature

A feature is complete only when:

```text
[ ] specification identified
[ ] option/method registered
[ ] typed representation implemented
[ ] application operation implemented
[ ] UI exposure assessed
[ ] validation implemented
[ ] error behavior implemented
[ ] tests added
[ ] documentation updated
[ ] compatibility/version behavior documented
```

---

# 76. UI Quality Gate

Before merging a UI issue, verify:

```text
1280×720
1440×900
1920×1080
```

At minimum.

Check:

```text
resize
focus
keyboard
scroll
selection
disabled states
error states
long labels
long filenames
large numbers
zero values
missing data
slow data
offline
```

---

# 77. AI Coding Agent Rules

The agent must:

1. Read `AGENTS.md`.
2. Read the relevant section of `PLAN.md`.
3. Inspect existing implementation.
4. Inspect tests.
5. Inspect dependencies.
6. Identify the architectural boundary.
7. Implement the smallest coherent change.
8. Add tests.
9. Update documentation.
10. Run validation.

The agent must not:

```text
invent aria2 behavior
disable type checking
delete tests to pass CI
replace ttkbootstrap
introduce another GUI toolkit
bypass application services
put RPC code into widgets
put database code into screens
use shell=True casually
introduce global mutable state
duplicate option registries
delete legacy code prematurely
```

---

# 78. Stop Conditions

Stop and report if:

- aria2 documentation is ambiguous;
- protocol behavior cannot be established;
- an API contract conflicts with existing tests;
- a migration may destroy user data;
- credentials/security behavior is unclear;
- platform behavior cannot be verified;
- a required capability is absent in the selected aria2 version;
- the implementation would require an architectural violation.

Use:

```text
BLOCKED

Issue:
Question:
Evidence:
Current behavior:
Expected behavior:
Recommended decision:
Impact:
```

---

# 79. Final Acceptance

The rewrite is complete only when:

```text
Phase 0 audit
        +
aria2 option coverage
        +
RPC coverage
        +
typed domain
        +
application layer
        +
daemon management
        +
persistence
        +
ttkbootstrap foundation
        +
132-screen UI catalogue implemented
        +
responsive layouts
        +
design system
        +
BitTorrent
        +
Metalink
        +
scheduler
        +
queue
        +
statistics
        +
security
        +
testing
        +
documentation
        +
consistency automation
        +
packaging
        +
CI
        +
legacy removal
```

All automated gates must pass.

---

# 80. Final Product Architecture

The final product should conceptually look like:

```text
                         SHUSHA
                           │
              ┌────────────┴────────────┐
              │                         │
          ttkbootstrap               Services
              │                         │
      ┌───────┴────────┐        ┌───────┴────────┐
      │                │        │                │
   Navigation       Screens   Commands         Queries
      │                │        │                │
      └────────┬───────┘        └───────┬────────┘
               │                        │
               └───────────┬────────────┘
                           ▼
                       Application
                           │
                           ▼
                         Domain
                           │
              ┌────────────┼────────────┐
              │            │            │
           aria2c       Persistence   OS/Network
              │
        ┌─────┴─────┐
        │           │
       RPC        Events
        │           │
        └─────┬─────┘
              ▼
        Typed application state
              │
              ▼
        ttkbootstrap presentation
```

The guiding principle is:

> **aria2c is the engine, the domain is the source of application meaning, the application layer is the orchestration boundary, and ttkbootstrap is the presentation layer—not the business layer.**

The 132-screen catalogue is therefore not 132 independent implementations. It is a controlled set of user-facing states built from a relatively small set of strongly typed, reusable ttkbootstrap components, layouts, state models, commands, and application services.