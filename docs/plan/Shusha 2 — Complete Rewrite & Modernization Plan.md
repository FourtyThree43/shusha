# Shusha 2 — Complete Rewrite & Modernization Plan

**Project:** Shusha  
**Rewrite:** Shusha 2  
**Target Python:** Python 3.14+  
**Package / Environment Manager:** Astral `uv`  
**Formatter / Linter:** Ruff  
**Type Checker:** ty  
**Testing:** pytest  
**GUI:** Tkinter + ttkbootstrap  
**Download Engine:** aria2c  
**Persistence:** SQLite  
**Primary RPC:** JSON-RPC  
**Compatibility RPC:** XML-RPC  
**Architecture:** Typed layered application / MVVM-inspired presentation architecture  
**Platforms:** Windows, Linux, macOS  
**Status:** Master implementation specification

---

# 1. Purpose

Shusha 2 is a ground-up modernization of the existing Shusha application.

The rewrite MUST preserve the fundamental purpose of Shusha:

> Provide a modern, powerful, understandable desktop control plane for aria2c.

The rewrite MUST NOT attempt to replace aria2c's download engine.

aria2 remains responsible for:

- HTTP
- HTTPS
- FTP
- SFTP
- BitTorrent
- Magnet
- Metalink
- networking
- connection management
- piece scheduling
- protocol handling
- checksum operations
- peer communication
- download execution

Shusha is responsible for:

- desktop UX
- configuration
- orchestration
- queue management
- profiles
- categories
- scheduling
- persistence
- history
- monitoring
- diagnostics
- daemon lifecycle
- typed RPC
- automation
- documentation
- accessibility
- user-facing abstractions

---

# 2. Primary Rewrite Goals

The rewrite MUST accomplish all of the following:

1. Move to Python 3.14+.
2. Standardize development on Astral `uv`.
3. Use Ruff for formatting and linting.
4. Use ty for static typing.
5. Use pytest for testing.
6. Use SQLite for durable application state.
7. Replace fragile/implicit application state with explicit domain models.
8. Create a strongly typed aria2 RPC layer.
9. Provide comprehensive aria2 option coverage.
10. Provide JSON-RPC support.
11. Retain XML-RPC compatibility.
12. Provide robust aria2 daemon supervision.
13. Provide a modern Tkinter/ttkbootstrap UI.
14. Preserve cross-platform operation.
15. Improve accessibility.
16. Improve keyboard usability.
17. Improve large-download performance.
18. Provide complete download history.
19. Provide categories and profiles.
20. Provide scheduling.
21. Provide diagnostics.
22. Provide configuration import/export.
23. Provide comprehensive documentation.
24. Make the repository AI-agent friendly.
25. Build an automated aria2 compatibility matrix.
26. Avoid undocumented gaps.
27. Avoid duplicated aria2 option definitions.
28. Avoid business logic inside UI widgets.

---

# 3. GUI Technology Decision

## 3.1 Mandatory GUI Stack

Shusha 2 MUST use:

```text
Tkinter
    +
ttk
    +
ttkbootstrap
```

`ttkbootstrap` is the project's primary visual design/styling layer.

---

## 3.2 Explicitly Excluded GUI Frameworks

The rewrite MUST NOT migrate to:

- PySide6
- PyQt
- Qt
- CustomTkinter
- Dear PyGui
- Electron
- webview-based UI
- browser-first UI
- another desktop GUI toolkit

The project intentionally remains within the Tkinter/ttk ecosystem.

---

# 4. Why ttkbootstrap

ttkbootstrap provides a strong foundation for modernizing the existing Tk/ttk UI without introducing a completely different desktop framework.

Use it for:

- themes
- semantic styles
- buttons
- labels
- entries
- comboboxes
- notebooks
- treeviews
- progress bars
- scrollbars
- checkbuttons
- radiobuttons
- frames
- dialogs
- navigation elements

Standard Tkinter and ttk remain available whenever ttkbootstrap does not provide an appropriate abstraction.

---

# 5. GUI Architectural Principle

The application MUST NOT become:

```text
Tkinter
    ↓
RPC
    ↓
aria2
```

Instead:

```text
┌──────────────────────────────────────────┐
│                 UI Layer                 │
│                                          │
│ ttkbootstrap / Tkinter                   │
│ Views / Widgets / ViewModels             │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            Application Layer             │
│                                          │
│ DownloadService                          │
│ QueueService                             │
│ CategoryService                          │
│ SchedulerService                         │
│ SettingsService                          │
│ HistoryService                           │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│               Domain Layer               │
│                                          │
│ Download                                 │
│ File                                     │
│ Queue                                    │
│ Category                                 │
│ Profile                                  │
│ Statistics                               │
│ Options                                  │
│ Events                                   │
└───────────────────┬──────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            Infrastructure Layer          │
│                                          │
│ aria2 RPC                                │
│ daemon supervisor                        │
│ SQLite                                   │
│ filesystem                               │
│ notifications                            │
│ secrets                                  │
└───────────────────┬──────────────────────┘
                    │
                    ▼
                  aria2c
```

---

# 6. UI Rule

A widget MUST NOT directly call:

```python
aria2.addUri(...)
```

A widget calls a ViewModel/application command.

Example:

```text
AddDownloadDialog
        ↓
AddDownloadViewModel
        ↓
DownloadService
        ↓
Aria2Client
        ↓
JsonRpcTransport
        ↓
aria2c
```

---

# 7. Repository Structure

Target repository:

```text
.
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── docs.yml
│   │   ├── build.yml
│   │   ├── security.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── assets/
│   ├── icons/
│   ├── themes/
│   └── images/
│
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── installation.md
│   ├── configuration.md
│   ├── downloads.md
│   ├── torrents.md
│   ├── metalink.md
│   ├── networking.md
│   ├── proxy.md
│   ├── authentication.md
│   ├── scheduler.md
│   ├── categories.md
│   ├── profiles.md
│   ├── history.md
│   ├── ui.md
│   ├── accessibility.md
│   ├── keyboard.md
│   ├── rpc.md
│   ├── cli.md
│   ├── diagnostics.md
│   ├── security.md
│   ├── compatibility.md
│   │
│   ├── aria2/
│   │   ├── compatibility.md
│   │   ├── options.md
│   │   ├── rpc-methods.md
│   │   ├── notifications.md
│   │   ├── errors.md
│   │   └── version-matrix.md
│   │
│   ├── development/
│   │   ├── setup.md
│   │   ├── architecture.md
│   │   ├── testing.md
│   │   ├── typing.md
│   │   ├── ui-development.md
│   │   ├── release.md
│   │   └── contributing.md
│   │
│   └── adr/
│
├── spec/
│   └── aria2/
│       ├── options.json
│       ├── rpc.json
│       ├── notifications.json
│       ├── errors.json
│       └── versions.json
│
├── src/
│   └── shusha/
│
├── tests/
│
├── tools/
│
├── scripts/
│
├── AGENTS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── PLAN.md
├── README.md
├── SECURITY.md
├── pyproject.toml
└── uv.lock
```

---

# 8. Python Package Structure

```text
src/shusha/
├── __init__.py
├── __main__.py
│
├── app/
│   ├── application.py
│   ├── lifecycle.py
│   ├── commands.py
│   ├── events.py
│   └── services.py
│
├── domain/
│   ├── download.py
│   ├── file.py
│   ├── queue.py
│   ├── category.py
│   ├── profile.py
│   ├── history.py
│   ├── statistics.py
│   ├── options.py
│   ├── identifiers.py
│   ├── states.py
│   └── errors.py
│
├── aria2/
│   ├── client.py
│   ├── protocol.py
│   ├── jsonrpc.py
│   ├── xmlrpc.py
│   ├── models.py
│   ├── methods.py
│   ├── notifications.py
│   ├── errors.py
│   ├── capabilities.py
│   │
│   └── options/
│       ├── registry.py
│       ├── definitions.py
│       ├── validators.py
│       ├── serializers.py
│       └── generated.py
│
├── daemon/
│   ├── manager.py
│   ├── process.py
│   ├── discovery.py
│   ├── health.py
│   └── executable.py
│
├── persistence/
│   ├── database.py
│   ├── migrations.py
│   ├── repositories.py
│   ├── models.py
│   └── session.py
│
├── services/
│   ├── downloads.py
│   ├── queue.py
│   ├── categories.py
│   ├── profiles.py
│   ├── scheduler.py
│   ├── history.py
│   ├── notifications.py
│   ├── reconciliation.py
│   ├── import_export.py
│   └── diagnostics.py
│
├── cli/
│   ├── main.py
│   ├── commands.py
│   └── output.py
│
├── ui/
│   ├── application.py
│   ├── theme.py
│   ├── state.py
│   ├── navigation.py
│   │
│   ├── views/
│   │   ├── dashboard.py
│   │   ├── downloads.py
│   │   ├── history.py
│   │   ├── settings.py
│   │   └── diagnostics.py
│   │
│   ├── viewmodels/
│   │   ├── downloads.py
│   │   ├── add_download.py
│   │   ├── settings.py
│   │   ├── history.py
│   │   └── diagnostics.py
│   │
│   ├── widgets/
│   │   ├── download_tree.py
│   │   ├── progress.py
│   │   ├── speed_graph.py
│   │   ├── piece_map.py
│   │   ├── option_editor.py
│   │   ├── status_badge.py
│   │   ├── inspector.py
│   │   └── navigation.py
│   │
│   ├── dialogs/
│   │   ├── add_download.py
│   │   ├── torrent.py
│   │   ├── metalink.py
│   │   ├── settings.py
│   │   ├── category.py
│   │   ├── profile.py
│   │   ├── scheduler.py
│   │   ├── connection.py
│   │   ├── import_export.py
│   │   └── errors.py
│   │
│   └── resources/
│
├── security/
│   ├── secrets.py
│   ├── redaction.py
│   └── paths.py
│
├── telemetry/
│   ├── logging.py
│   └── metrics.py
│
└── utils/
    ├── paths.py
    ├── sizes.py
    ├── rates.py
    ├── time.py
    └── platform.py
```

---

# 9. Domain Layer

The domain layer MUST be GUI-independent.

It MUST NOT import:

```text
tkinter
ttkbootstrap
aria2 transport
sqlite3
subprocess
```

It contains:

- entities
- value objects
- enums
- state transitions
- invariants
- domain events

---

# 10. Typed Identifiers

Use dedicated types for:

```text
GID
DownloadId
CategoryId
ProfileId
HistoryId
ConnectionId
```

Do not pass arbitrary strings everywhere.

---

# 11. Download Model

Example conceptual model:

```python
@dataclass(frozen=True, slots=True)
class Download:
    gid: Gid
    name: str
    status: DownloadStatus
    total_bytes: ByteSize | None
    completed_bytes: ByteSize
    download_speed: BitRate
    upload_speed: BitRate
    eta: Duration | None
    connections: int
    category_id: CategoryId | None
```

The actual model should remain appropriately normalized.

---

# 12. Download State Machine

States:

```text
NEW
QUEUED
STARTING
ACTIVE
PAUSING
PAUSED
RESUMING
COMPLETING
COMPLETED
FAILED
REMOVING
REMOVED
```

BitTorrent:

```text
SEEDING
```

Invalid transitions MUST be rejected.

---

# 13. Value Objects

Create strongly typed representations for:

```text
ByteSize
BitRate
Duration
Percentage
Port
Gid
Uri
Checksum
FilePath
```

---

# 14. Unit Handling

Support aria2-compatible values:

```text
1K
1M
1G
1MiB
1GiB
```

where semantics permit.

Internally normalize values.

Display according to user preferences.

---

# 15. Configuration Architecture

Configuration precedence:

```text
aria2 defaults
      ↓
application defaults
      ↓
global configuration
      ↓
profile
      ↓
category
      ↓
download
      ↓
one-off override
```

Every effective option should have an identifiable source.

---

# 16. Full aria2 Option Registry

This is one of the most important components.

Create a machine-readable registry containing every supported aria2 option.

Each option definition should include:

```text
name
short name
type
default
minimum
maximum
choices
scope
protocols
dynamic status
repeatability
deprecated status
experimental status
sensitive status
description
examples
UI editor type
```

---

# 17. Option Scopes

Distinguish:

```text
GLOBAL
DOWNLOAD
INPUT
RPC
DAEMON
```

and whether the option can be changed dynamically.

---

# 18. Option Types

Support:

```text
BOOLEAN
OPTIONAL_BOOLEAN
INTEGER
FLOAT
STRING
ENUM
SIZE
RATE
DURATION
PATH
URI
LIST
REPEATABLE
HASH
HEADER
```

---

# 19. Option Registry as Source of Truth

The registry MUST drive:

```text
CLI serialization
aria2.conf serialization
RPC option serialization
validation
UI controls
settings search
documentation
compatibility tests
schema generation
```

No separate copies of option definitions should exist.

---

# 20. UI Option Generation

Map metadata to ttkbootstrap controls:

```text
boolean
    → Checkbutton

enum
    → Combobox

integer
    → Spinbox

string
    → Entry

path
    → Entry + Browse button

size
    → SizeEntry

rate
    → RateEntry

duration
    → DurationEntry

repeatable
    → ListEditor
```

Specialized controls can override generated editors.

---

# 21. Expert Mode

Normal mode:

```text
curated user-friendly options
```

Expert mode:

```text
complete aria2 option registry
```

Expert mode MUST include:

- option search
- description
- type
- current value
- effective value
- source
- protocol applicability
- dynamic/static status
- raw value editor

---

# 22. Raw Option Escape Hatch

Provide an advanced/raw option editor.

Users must be able to specify supported aria2 options that do not yet have specialized UI controls.

Unknown options MUST NOT be silently discarded.

---

# 23. Protocol Coverage

The application MUST provide first-class workflows for:

```text
HTTP
HTTPS
FTP
SFTP
BitTorrent
Magnet
Metalink
```

---

# 24. HTTP/HTTPS

Support the full applicable aria2 feature surface:

- redirects
- authentication
- headers
- cookies
- proxy
- TLS
- range requests
- resume
- mirrors
- checksum
- server statistics
- connection settings
- timeout
- retry
- file naming

---

# 25. FTP

Support applicable:

- authentication
- passive/active behavior
- proxy
- resume
- timestamps
- directory behavior
- connection options
- retries

---

# 26. SFTP

Support applicable aria2 options:

- authentication
- host verification
- resume
- SSH configuration
- connection settings

---

# 27. BitTorrent

Provide first-class visibility/control for:

- torrent files
- magnet
- trackers
- DHT
- PEX
- peers
- upload
- seeding
- seed ratio
- seed time
- peer limits
- file selection
- piece selection
- web seeds
- encryption
- tracker behavior

---

# 28. Metalink

Support:

- local Metalink
- remote Metalink
- mirrors
- checksum information
- piece hashes
- file selection
- metadata
- HTTP/FTP sources

---

# 29. Magnet Workflow

Magnet URI detection MUST automatically identify:

```text
magnet:
```

The Add dialog should provide:

```text
Magnet URI
Display name if available
Advanced BitTorrent options
Destination
File selection after metadata retrieval
```

---

# 30. Add Download Dialog

The main Add Download dialog should support:

```text
URL / Magnet / Torrent / Metalink
```

with automatic type detection.

Layout:

```text
┌─────────────────────────────────────────────┐
│ Add Download                                │
├─────────────────────────────────────────────┤
│ Source                                      │
│ [ URL / Magnet / File.................... ] │
│                                             │
│ Destination                                 │
│ [ /Downloads............................. ] │
│                                             │
│ Profile       [Default ▼]                   │
│ Category      [None ▼]                      │
│                                             │
│ ▼ Advanced Options                          │
│                                             │
│                     [Cancel] [Add Download] │
└─────────────────────────────────────────────┘
```

---

# 31. Advanced Add Layout

Advanced options grouped into:

```text
Destination
Files
Connections
Speed
Resume
Integrity
Authentication
Headers
Cookies
Proxy
TLS
Mirrors
Scheduling
BitTorrent
Metalink
Advanced
```

---

# 32. Main Window

The primary application shell:

```text
┌─────────────────────────────────────────────────────┐
│ Shusha   Add   Start   Pause   Stop   Search   ⋮    │
├─────────────┬───────────────────────────────────────┤
│             │                                       │
│ Navigation  │        Download Workspace             │
│             │                                       │
│ All         │  Search / Filters / Sort              │
│ Active      │                                       │
│ Waiting     │  Download Tree                        │
│ Paused      │                                       │
│ Completed   │                                       │
│ Failed      │                                       │
│ Seeding     │                                       │
│ Categories  │                                       │
│             │                                       │
├─────────────┴───────────────────────────────────────┤
│ ↓ 12.4 MiB/s │ ↑ 1.2 MiB/s │ 8 Active │ aria2 ✓    │
└─────────────────────────────────────────────────────┘
```

---

# 33. Navigation

Primary navigation:

```text
Dashboard
All Downloads
Active
Waiting
Paused
Completed
Failed
Seeding
History
Categories
Profiles
Scheduler
Diagnostics
Settings
```

---

# 34. Download Tree

Use `ttk.Treeview` as the primary large-data presentation.

Columns:

```text
Status
Name
Progress
Size
Downloaded
Download Speed
Upload Speed
ETA
Connections
Seeds
Peers
Category
Destination
GID
```

Columns MUST support:

- resize
- reorder
- hide/show
- persistent configuration
- sorting

---

# 35. Download Row

Each row should expose:

```text
status icon
name
progress
speed
ETA
```

without requiring the user to open an inspector.

---

# 36. Status Indicators

Do not rely exclusively on colors.

Examples:

```text
↓  Downloading
Ⅱ  Paused
◷  Waiting
✓  Completed
↑  Seeding
!  Failed
↻  Retrying
```

Icons + text + optional color.

---

# 37. Inspector Pane

Selecting a download opens a detail inspector.

Tabs:

```text
Overview
Files
Pieces
Sources
Servers
Peers
Trackers
Options
Headers
Hashes
Logs
Activity
Metadata
History
```

The inspector can be docked or collapsed.

---

# 38. Overview Inspector

Display:

```text
Name
Status
Progress
Total size
Completed
Remaining
Download speed
Upload speed
ETA
Connections
Destination
GID
Source
Category
Profile
Started
```

---

# 39. Files Inspector

Tree columns:

```text
Path
Size
Progress
Selected
Priority
Completed
```

Operations:

```text
select
deselect
select directory
deselect directory
select all
invert
search
```

---

# 40. Piece Map

Implement a Tk Canvas-based virtualized piece map.

Do NOT create one Tk object per piece.

The renderer should calculate:

```text
visible viewport
piece range
piece state
```

and draw only what is visible.

States:

```text
missing
requested
downloading
complete
verified
failed
```

---

# 41. Peer Inspector

Display:

```text
IP
Client
Country
Download speed
Upload speed
Progress
Latency
Flags
Choking
Interested
```

Only query peers when the inspector is visible.

---

# 42. Tracker Inspector

Display:

```text
Tracker
Status
Peers
Seeds
Last announce
Next announce
Error
```

---

# 43. Server Inspector

Display:

```text
Server
Connections
Speed
Score
Failure count
Last used
```

---

# 44. Source/Mirror Inspector

Display:

```text
URI
Protocol
Availability
Response
Speed
Selected
```

---

# 45. Options Inspector

Show effective options:

```text
Option
Value
Source
Scope
Dynamic
Protocol
```

Example:

```text
max-connection-per-server
8
Category: Large Files
Download-level override: none
Dynamic: yes
```

---

# 46. Configuration Diff

Allow comparison between:

```text
Global
Profile
Category
Download
```

Example:

```text
max-concurrent-downloads
Global:   5
Profile:  10
Category: inherited
Download: inherited
Effective: 10
```

---

# 47. Queue

Queue operations:

```text
Add
Pause
Resume
Retry
Remove
Force Remove
Move Up
Move Down
Move Top
Move Bottom
Start Now
```

Support:

- priority
- categories
- scheduling
- concurrency limits

---

# 48. Scheduler

Scheduler must support:

- time ranges
- days
- bandwidth rules
- concurrency rules
- automatic pause
- automatic resume
- category rules

Example:

```text
00:00–06:00
Unlimited

06:00–18:00
2 MiB/s

18:00–00:00
20 MiB/s
```

---

# 49. Categories

Category model:

```text
id
name
icon
directory
default profile
options
priority
scheduler
notification rules
```

---

# 50. Profiles

Profiles are reusable aria2 option collections.

Built-ins:

```text
Default
Fast HTTP
Large File
Torrent
Private Tracker
Slow Connection
Night Download
Verification First
```

Users can create custom profiles.

---

# 51. History

History records:

```text
GID
Name
Sources
Category
Started
Completed
Duration
Bytes
Average speed
Peak speed
Destination
Result
Error
```

Operations:

```text
search
filter
retry
redownload
export
clear
```

---

# 52. Dashboard

Dashboard metrics:

```text
Current download speed
Current upload speed
Peak download speed
Peak upload speed
Active downloads
Waiting downloads
Completed
Failed
Disk usage
Available disk
RPC latency
aria2 state
```

---

# 53. Charts

Use Tk Canvas or a small dedicated plotting implementation.

Do not introduce a heavy visualization dependency unless necessary.

Charts:

```text
Download rate
Upload rate
Active connections
Queue size
Disk write rate
```

---

# 54. Daemon Supervisor

The local aria2 supervisor must support:

```text
discover
validate
version detect
start
readiness check
health check
restart
stop
force stop
stdout capture
stderr capture
crash detection
```

---

# 55. Executable Discovery

Search:

```text
PATH
configured executable
application directory
platform-specific common paths
user-selected path
```

Expose:

```text
Executable
Version
Capabilities
RPC endpoint
```

---

# 56. aria2 Capability Detection

At connection:

```text
aria2.getVersion
```

Create:

```python
@dataclass(frozen=True, slots=True)
class Aria2Capabilities:
    version: str
    features: frozenset[str]
```

Use capabilities to enable/disable UI features.

---

# 57. Local vs Remote aria2

Support:

```text
Local aria2
Remote aria2
```

The connection model should support multiple endpoints in the future.

---

# 58. Connection Profiles

A connection profile:

```text
name
host
port
path
TLS
certificate verification
secret reference
local/remote
```

Never store plaintext secrets in ordinary settings.

---

# 59. JSON-RPC

Implement typed JSON-RPC.

Required functionality includes applicable aria2 methods such as:

```text
addUri
addTorrent
addMetalink
remove
forceRemove
pause
pauseAll
forcePause
forcePauseAll
unpause
unpauseAll
changePosition
tellStatus
tellActive
tellWaiting
tellStopped
getOption
changeOption
getGlobalOption
changeGlobalOption
getFiles
getPeers
getServers
getUris
getVersion
getSessionInfo
saveSession
purgeDownloadResult
removeDownloadResult
shutdown
forceShutdown
```

The exact supported method registry MUST be generated/verified against the target aria2 versions.

---

# 60. XML-RPC

Implement XML-RPC behind the same client interface.

```text
Aria2Client
├── JsonRpcClient
└── XmlRpcClient
```

The application layer MUST NOT care about the transport.

---

# 61. RPC Notifications

Convert aria2 notifications into typed application events.

Support applicable:

```text
download start
download pause
download stop
download complete
download error
BitTorrent complete
```

The notification registry must be versioned.

---

# 62. RPC Transport

Support:

```text
request IDs
timeouts
retry
authentication
batch calls
connection reuse
structured errors
notification handling
```

---

# 63. RPC Polling

Avoid polling every download separately.

Use bulk methods:

```text
tellActive
tellWaiting
tellStopped
```

and targeted calls only when necessary.

Suggested polling:

```text
Active: 0.5–1 sec
Waiting: 2–5 sec
Stopped: 5–30 sec
Hidden inspectors: on-demand
```

Polling must adapt to application load.

---

# 64. Incremental State Updates

Never rebuild the entire download table on every poll.

Pipeline:

```text
aria2 snapshot
       ↓
state diff
       ↓
domain events
       ↓
updated models
       ↓
Treeview row updates
```

---

# 65. Tkinter Event Loop

Tk's main thread MUST remain responsive.

No blocking:

- RPC
- subprocess
- filesystem scan
- SQLite query
- metadata operation
- peer retrieval
- large configuration operation

inside UI callbacks.

---

# 66. Async Architecture

Use asynchronous/background services while preserving Tkinter's event loop.

Recommended approach:

```text
Tk main thread
       │
       │ UI events
       ▼
Application command queue
       │
       ▼
Background async/service runtime
       │
       ├── aria2 RPC
       ├── daemon
       ├── SQLite
       └── filesystem
       │
       ▼
Thread-safe event queue
       │
       ▼
Tk `after()` dispatcher
       │
       ▼
UI model update
```

Tkinter widgets MUST only be manipulated from the Tk main thread.

---

# 67. Thread Safety

Rules:

- Tk widgets only from UI thread.
- RPC clients may run in background.
- Database access must be coordinated.
- Domain models should be immutable where possible.
- Cross-thread communication must use queues/events.
- No arbitrary shared mutable state.

---

# 68. Event Bus

Typed events:

```text
DownloadAdded
DownloadStarted
DownloadProgressed
DownloadPaused
DownloadResumed
DownloadCompleted
DownloadFailed
DownloadRemoved
QueueChanged
Aria2Connected
Aria2Disconnected
Aria2Restarted
SettingsChanged
CategoryChanged
HistoryChanged
```

---

# 69. Persistence

Use SQLite as the authoritative Shusha application database.

Tables:

```text
downloads
download_files
download_sources
download_events
categories
category_options
profiles
profile_options
history
settings
scheduler_rules
connections
ui_state
```

---

# 70. aria2 Session vs Shusha Database

They are different systems.

aria2 owns:

```text
download execution state
```

Shusha owns:

```text
application metadata
history
categories
profiles
UI state
user configuration
```

Startup must reconcile both.

---

# 71. Startup Reconciliation

```text
Load database
       ↓
Start/connect aria2
       ↓
Query active/waiting/stopped
       ↓
Match GIDs
       ↓
Import unknown downloads
       ↓
Mark stale records
       ↓
Refresh state
```

---

# 72. Unknown aria2 Downloads

If aria2 contains a GID unknown to Shusha:

```text
Unknown download detected

[Import]
[Ignore]
```

Configurable policy:

```text
ask
auto-import
ignore
```

---

# 73. Crash Recovery

If Shusha crashes:

- aria2 may continue
- Shusha reconnects
- GIDs are reconciled
- history resumes
- UI state is restored

The application MUST NOT assume its own lifetime equals aria2's lifetime.

---

# 74. aria2 Crash Recovery

When local aria2 crashes:

```text
Disconnected
    ↓
detect
    ↓
retry
    ↓
restart if enabled
    ↓
wait for readiness
    ↓
reconnect
    ↓
reconcile
```

Never duplicate downloads.

---

# 75. Database Migrations

Every schema change requires a migration.

Example:

```text
001_initial
002_profiles
003_scheduler
004_connections
```

Migrations must be tested.

---

# 76. Settings

Settings groups:

```text
General
Downloads
Queue
Network
Proxy
Authentication
BitTorrent
Metalink
RPC
Daemon
Notifications
Appearance
Keyboard
Accessibility
Privacy
Advanced
Developer
```

---

# 77. TOML

Use TOML for human-editable application configuration where appropriate.

SQLite remains responsible for state.

Do not mix:

```text
configuration
database state
UI state
```

without a clear reason.

---

# 78. Secrets

Use platform credential stores where practical:

```text
Windows Credential Manager
macOS Keychain
Linux Secret Service
```

Secrets MUST NOT appear in:

```text
logs
diagnostics
RPC dumps
crash reports
configuration previews
```

---

# 79. Security

Threat model includes:

```text
malicious URLs
malicious filenames
malicious torrent metadata
malicious Metalink metadata
path traversal
RPC exposure
credential leakage
shell injection
unsafe downloaded files
```

Never execute downloaded content automatically.

Never construct shell commands by string concatenation.

---

# 80. Filesystem Safety

Support:

- Windows paths
- UNC paths
- POSIX paths
- Unicode
- long paths where supported
- invalid Windows filename characters
- symlinks
- path normalization

---

# 81. Destructive Actions

Deleting downloaded files requires explicit confirmation.

Confirmation should identify:

```text
download
number of files
total size
destination
```

---

# 82. Notifications

Support:

```text
download completed
download failed
download paused
download resumed
queue completed
aria2 disconnected
aria2 restarted
low disk space
```

Allow per-category rules.

---

# 83. System Tray

Provide:

```text
Show Shusha
Pause All
Resume All
Stop Queue
Current Speed
Active Downloads
Exit
```

Closing the window MUST NOT necessarily terminate aria2.

---

# 84. Clipboard

Optional clipboard monitoring.

Recognize:

```text
http://
https://
ftp://
sftp://
magnet:
```

Never auto-download without explicit configuration.

---

# 85. Drag and Drop

Support dropping:

```text
URLs
torrent files
Metalink files
text files containing URLs
```

---

# 86. Search

Global search:

```text
name
URI
GID
path
category
error
tracker
filename
```

Advanced filters:

```text
status:active
category:movies
size:>1GB
speed:>1MB
error:true
```

---

# 87. Context Menu

Download context menu:

```text
Open
Open Folder
Copy URI
Copy GID
Copy Magnet
Copy Path
Pause
Resume
Retry
Force Start
Remove
Delete Files
Properties
Inspect
Set Category
Set Priority
```

---

# 88. Keyboard Shortcuts

Defaults:

```text
Ctrl+N
Space
Delete
Shift+Delete
Enter
Ctrl+F
Ctrl+R
Ctrl+Shift+R
Ctrl+,
```

All shortcuts must be configurable.

---

# 89. Accessibility

Support:

- keyboard-only operation
- logical focus order
- visible focus
- accessible labels
- no color-only status
- scalable text
- high contrast
- reduced animation
- meaningful status messages

---

# 90. ttkbootstrap Theme System

Create Shusha themes:

```text
Shusha Light
Shusha Dark
Shusha High Contrast
```

Use ttkbootstrap semantic styles.

Avoid scattered raw colors.

Centralize:

```text
primary
secondary
success
info
warning
danger
background
surface
border
text
muted
```

---

# 91. UI Design Tokens

Define:

```text
spacing
font sizes
row heights
icon sizes
border widths
corner radius where supported
control heights
```

Use consistent tokens across screens.

---

# 92. High DPI

Test on:

```text
100%
125%
150%
175%
200%
```

where supported.

UI must remain usable.

---

# 93. Responsive Tk Layout

Use:

```text
grid
pack
place
```

appropriately.

Prefer `grid` for structured application layouts.

Use weights/minimum sizes carefully.

Avoid fixed absolute positioning.

---

# 94. Window Layout

The primary window should support:

```text
navigation width
main content
inspector width
```

with resizable panes.

Use Tkinter `PanedWindow` or ttk-compatible equivalents where appropriate.

---

# 95. View Architecture

Each major view should have:

```text
View
ViewModel
State
Commands
Event subscriptions
```

The ViewModel must not depend on concrete widgets.

---

# 96. Widget Architecture

Custom widgets should be small and reusable:

```text
StatusBadge
SpeedLabel
ProgressIndicator
RateGraph
OptionEditor
SearchBar
FilterBar
DownloadTree
Inspector
PieceMap
```

---

# 97. Large Dataset Rendering

Never create thousands of permanent widgets.

Use:

```text
Treeview
Canvas viewport rendering
lazy loading
incremental updates
```

Target:

```text
1,000+ downloads
10,000+ files
10,000+ peers
100,000+ pieces
```

---

# 98. Virtual Piece Map

Piece map should calculate visible pieces:

```text
canvas viewport
        ↓
visible piece indices
        ↓
render
```

Use coarse zoom levels where useful.

---

# 99. File Tree Performance

For huge torrents:

- lazy-expand directories
- avoid loading all descendants at once
- update only visible nodes
- search asynchronously

---

# 100. History Performance

History table should use:

- pagination
- filtering
- indexed SQLite queries
- incremental loading

Do not load millions of history rows into Tk at once.

---

# 101. CLI

Provide:

```text
shusha add
shusha list
shusha status
shusha pause
shusha resume
shusha retry
shusha remove
shusha inspect
shusha history
shusha category
shusha profile
shusha config
shusha daemon
shusha version
```

Output formats:

```text
human
table
JSON
```

---

# 102. CLI and GUI Share Services

CLI MUST use the same:

```text
Application services
Domain
aria2 client
Persistence
```

as the GUI.

No duplicated command logic.

---

# 103. aria2 Configuration Import

Support importing:

```text
aria2.conf
```

Behavior:

```text
parse
validate
classify
preview
import
report
```

Never silently drop unknown settings.

---

# 104. Input Files

Support aria2 input-file semantics.

Parser must preserve:

- URI lines
- comments
- per-entry options
- repeated values
- whitespace
- applicable compression behavior

---

# 105. Session Files

Support:

```text
save-session
session restore
```

Provide import/recovery tooling.

---

# 106. Export

Export:

```text
settings
profiles
categories
history
download lists
aria2-compatible configuration
```

Formats:

```text
JSON
TOML
CSV
aria2.conf
```

---

# 107. Import Report

Example:

```text
Imported: 94
Supported: 87
Deprecated: 3
Unsupported: 2
Invalid: 2
```

Every skipped item must be explainable.

---

# 108. aria2 Compatibility Matrix

Create:

```text
docs/aria2/compatibility.md
```

Columns:

```text
Feature
aria2 support
Shusha domain
Shusha service
GUI
CLI
RPC
Tests
Documentation
```

---

# 109. Full Option Coverage Requirement

CI MUST fail if an authoritative option exists without:

```text
registry definition
```

and appropriate coverage.

---

# 110. Option Coverage Categories

Ensure coverage across:

```text
Basic
HTTP
HTTPS
FTP
SFTP
Proxy
Authentication
TLS
Cookies
Headers
File
Directory
Naming
Resume
Integrity
Checksum
Connections
Splitting
Mirrors
Bandwidth
Timeout
Retry
Scheduling
Queue
Logging
Daemon
RPC
Session
Input
Hooks
File Allocation
Metalink
BitTorrent
DHT
PEX
Peers
Seeding
Trackers
Web Seed
Magnet
Advanced
Experimental
Deprecated
```

---

# 111. aria2 CLI Serializer

Implement a safe serializer.

Never build:

```text
shell command string
```

Use:

```python
subprocess.Popen([
    aria2_path,
    "--enable-rpc=true",
    ...
])
```

Arguments must remain separate.

---

# 112. aria2 Config Serializer

Implement:

```text
Aria2ConfigWriter
```

with correct:

```text
name=value
```

serialization.

---

# 113. Option Validation

Validation MUST occur before RPC submission when possible.

Examples:

```text
port range
integer bounds
enum values
size syntax
rate syntax
duration syntax
URI validity
path validity
```

aria2 remains authoritative for semantics that cannot be locally validated.

---

# 114. RPC DTOs

Typed DTOs for:

```text
StatusResponse
FileResponse
PeerResponse
ServerResponse
UriResponse
VersionResponse
OptionResponse
SessionResponse
```

---

# 115. Unknown RPC Fields

Unknown response fields MUST NOT crash the parser.

This allows compatibility with newer aria2 versions.

---

# 116. Missing Fields

Use:

```text
Optional
```

only where omission is valid.

Never fabricate values.

---

# 117. RPC Errors

Typed hierarchy:

```text
Aria2Error
RpcError
AuthenticationError
InvalidArgumentError
DownloadNotFoundError
NetworkError
FileError
ServerError
UnknownAria2Error
```

Preserve:

```text
code
message
method
request id
GID
```

---

# 118. Network Failure Semantics

Distinguish:

```text
Download failure
RPC failure
Network failure
aria2 unavailable
Timeout
Daemon crash
```

A lost RPC connection MUST NOT automatically mark downloads as failed.

---

# 119. Logging

Structured logs:

```text
timestamp
level
component
event
GID
method
duration
error
```

Never log:

```text
passwords
tokens
cookies
authorization headers
private keys
```

---

# 120. Diagnostics

Provide:

```text
aria2 version
Shusha version
Python version
OS
daemon PID
RPC endpoint
RPC latency
connection state
capabilities
database status
recent errors
```

---

# 121. Raw RPC Inspector

Developer mode:

```text
Request
Response
Latency
Error
```

All secrets MUST be redacted.

---

# 122. Diagnostic Export

Export:

```text
system information
aria2 version
capabilities
configuration schema
logs
errors
RPC health
```

without sensitive data.

---

# 123. Performance

Target:

```text
1,000 downloads
10,000 files
10,000 peers
100,000 pieces
large history
```

without unacceptable UI freezes.

---

# 124. Startup Performance

Do not block startup on:

- complete history
- peer data
- full file trees
- expensive directory scans
- nonessential diagnostics

Load lazily.

---

# 125. Lazy Loading

Lazy-load:

```text
history
peers
servers
trackers
pieces
advanced options
diagnostics
```

when possible.

---

# 126. Notifications

Notifications must never steal application focus unexpectedly.

---

# 127. Empty States

Every major view requires a designed empty state.

Example:

```text
No active downloads

Add a URL, torrent, magnet or Metalink file to begin.

[Add Download]
```

---

# 128. Loading States

Every asynchronous view requires a loading state.

Use:

```text
progress indicator
loading label
skeleton-like placeholders where appropriate
```

---

# 129. Error States

Every backend-dependent view needs:

```text
friendly error
retry
details
```

---

# 130. First Run Wizard

Steps:

```text
Welcome
aria2 detection
executable selection
RPC configuration
download directory
theme
notifications
clipboard option
finish
```

---

# 131. Connection Wizard

Support:

```text
Local aria2
Remote aria2
```

Fields:

```text
Host
Port
Path
Secret
TLS
Certificate validation
```

Provide:

```text
[Test Connection]
```

---

# 132. Closing Behavior

Configurable:

```text
Leave aria2 running
Stop aria2
Pause downloads
Ask
```

Default should avoid unexpectedly killing active downloads.

---

# 133. Multi-Instance Preparation

The architecture MUST permit:

```text
Connection A
Connection B
Connection C
```

even if the first release only exposes one active connection.

Every download record should be associated with a connection.

---

# 134. Automation

Future-compatible event hooks:

```text
download.started
download.completed
download.failed
queue.empty
```

Actions:

```text
notification
script
webhook
```

All commands must be safely parameterized.

---

# 135. Browser Integration

Keep browser integration outside the core.

Future API may expose:

```text
local application protocol
CLI command
localhost endpoint
```

Do not embed browser-specific assumptions in the domain.

---

# 136. Localization

Build UI strings through a localization abstraction.

Initial language:

```text
English
```

Future support can include:

```text
Swahili
French
German
Spanish
etc.
```

---

# 137. Internationalization

Handle:

- Unicode
- locale-independent serialization
- dates
- times
- decimal values
- Unicode filesystem paths

---

# 138. Time

Store timestamps consistently.

Prefer UTC persistence.

Display local time.

Use timezone-aware datetime values.

---

# 139. Privacy

Downloaded URLs may contain sensitive information.

Therefore:

- no external URL telemetry
- no automatic cloud synchronization
- no unnecessary URL logging
- no credential logging
- no hidden analytics

---

# 140. Telemetry

No telemetry by default.

If ever added:

- opt-in
- documented
- minimal
- anonymous
- disableable

---

# 141. Backup

Provide backup/export of:

```text
settings
profiles
categories
history
scheduler
connection metadata
```

Do not include downloaded files unless explicitly requested.

---

# 142. Restore

Restore should be previewable.

Example:

```text
Settings: 32
Profiles: 8
Categories: 12
History records: 4,281
```

---

# 143. Python 3.14 Standards

Use modern Python typing:

```text
X | None
list[str]
dict[str, T]
TypeAlias
Protocol
Self
Literal
TypeGuard
dataclass(slots=True)
```

Avoid unnecessary legacy typing syntax.

---

# 144. Typing Policy

No untyped public functions.

No unnecessary `Any`.

No untyped dictionaries in the core domain.

All external data must be validated at boundaries.

---

# 145. Dataclass Policy

Prefer:

```python
@dataclass(frozen=True, slots=True)
```

for immutable domain/value objects.

Use mutable models only where justified.

---

# 146. Protocol Interfaces

Use `Protocol` for infrastructure boundaries.

Examples:

```text
Aria2Client
DownloadRepository
SettingsRepository
ProcessSupervisor
NotificationService
SecretStore
FilesystemService
Scheduler
```

---

# 147. Dependency Inversion

The domain/application layers depend on abstractions.

Infrastructure implements them.

The UI consumes application services.

---

# 148. Anti-Patterns

The rewrite MUST NOT introduce:

```text
giant controllers
giant Tk classes
global mutable state
raw RPC dictionaries everywhere
business logic inside widgets
SQL inside UI classes
blocking RPC callbacks
shell command strings
duplicated aria2 option definitions
silent exceptions
hard-coded platform paths
plaintext secrets
```

---

# 149. Dependency Policy

Keep dependencies minimal.

Required development stack:

```text
uv
ruff
ty
pytest
```

Application:

```text
ttkbootstrap
platformdirs
```

Add other libraries only with justification.

---

# 150. Packaging

Use `pyproject.toml`.

Target:

```toml
requires-python = ">=3.14"
```

Do not preserve obsolete packaging files solely for historical reasons.

---

# 151. Astral Toolchain

Required commands:

```bash
uv sync

uv run ruff check .

uv run ruff format .

uv run ty check

uv run pytest

uv build
```

---

# 152. CI

Required CI gates:

```text
uv lock validation
dependency installation
Ruff lint
Ruff format
ty
pytest
coverage
build
documentation
```

---

# 153. Coverage

Targets:

```text
Overall: >=90%
Core domain: >=95%
aria2 compatibility: >=95%
Critical persistence: >=95%
```

Coverage alone is not sufficient.

Real aria2 integration tests are mandatory.

---

# 154. Test Layout

```text
tests/
├── unit/
│   ├── domain/
│   ├── services/
│   ├── aria2/
│   ├── persistence/
│   └── utils/
│
├── integration/
│   ├── aria2/
│   ├── daemon/
│   ├── persistence/
│   └── application/
│
├── contract/
│   ├── rpc/
│   ├── options/
│   └── compatibility/
│
├── ui/
│   ├── smoke/
│   ├── viewmodels/
│   └── widgets/
│
├── fixtures/
└── golden/
```

---

# 155. Real aria2 Integration Harness

Tests should launch real aria2c when available.

Lifecycle:

```text
temporary directory
        ↓
temporary RPC port
        ↓
launch aria2c
        ↓
wait for readiness
        ↓
execute tests
        ↓
capture logs
        ↓
shutdown
        ↓
cleanup
```

---

# 156. Contract Tests

Verify:

```text
RPC request serialization
RPC response parsing
error mapping
option serialization
option validation
notification parsing
```

---

# 157. Property Tests

Use Hypothesis where useful for:

```text
size parsing
rate parsing
duration parsing
GID parsing
URI classification
option serialization
configuration round trips
```

---

# 158. UI Tests

Test:

```text
startup
main window
add dialog
download selection
pause/resume
context menu
settings
theme switching
keyboard navigation
error dialogs
```

---

# 159. UI Smoke Tests

At minimum:

```text
application starts
aria2 connection can be configured
download appears
download state changes
download can be paused
download can be resumed
download can be removed
```

---

# 160. Visual Regression

Where practical, capture reference screenshots for:

```text
Main dashboard
Dark theme
Light theme
Add dialog
Settings
Inspector
History
Torrent inspector
Error state
```

Test at multiple scaling factors.

---

# 161. Cross-Platform Testing

Platforms:

```text
Windows
Linux
macOS
```

Test:

- filesystem
- executable discovery
- tray
- notifications
- fonts
- Unicode
- paths
- subprocess handling

---

# 162. Windows

Test:

- Windows 10+
- Windows 11
- Unicode
- UNC paths
- long paths
- tray
- notifications
- aria2 discovery

---

# 163. Linux

Test:

- X11
- Wayland
- common desktop environments
- notifications
- tray behavior
- desktop integration

---

# 164. macOS

Test:

- Apple Silicon
- Intel where supported
- application bundle
- Keychain
- notifications
- executable discovery

---

# 165. Documentation Strategy

Documentation MUST be divided into:

```text
User documentation
Developer documentation
Reference documentation
Compatibility documentation
Security documentation
```

---

# 166. README

README should include:

```text
Project overview
Screenshots
Features
Supported protocols
Installation
Quick start
aria2 requirements
GUI usage
CLI usage
Compatibility
Development
Testing
Security
Contributing
License
```

Do not make README the complete manual.

---

# 167. User Manual

Document:

```text
Adding downloads
Managing downloads
Queues
Categories
Profiles
Torrents
Metalinks
Scheduling
Settings
History
Notifications
Troubleshooting
```

---

# 168. aria2 Reference

Generated documentation:

```text
ARIA2_OPTIONS.md
ARIA2_RPC.md
ARIA2_NOTIFICATIONS.md
ARIA2_COMPATIBILITY.md
```

---

# 169. Generated Documentation

The option registry generates:

```text
docs/aria2/options.md
spec/aria2/options.json
spec/aria2/options.schema.json
```

RPC registry generates:

```text
docs/aria2/rpc-methods.md
spec/aria2/rpc.json
```

---

# 170. aria2 Specification Synchronization

Provide:

```bash
uv run shusha-dev sync-aria2-spec
```

It should:

1. retrieve authoritative upstream data
2. parse options
3. identify changes
4. compare registry
5. generate a diff
6. update normalized spec snapshots
7. generate documentation
8. require human review for semantic changes

---

# 171. Spec Snapshots

Commit normalized snapshots:

```text
spec/aria2/
├── options.json
├── rpc.json
├── notifications.json
├── errors.json
└── versions.json
```

This makes compatibility reproducible.

---

# 172. Compatibility Levels

## Native

Fully represented by Shusha.

## Passthrough

Supported by aria2 and available through raw configuration/RPC but not specialized UI.

## Unsupported

Known aria2 behavior not currently exposed.

Every unsupported area must be documented.

---

# 173. No False Feature Claims

Never claim:

```text
"Full BitTorrent support"
```

if only magnet downloading works.

Feature documentation must reflect actual coverage.

---

# 174. aria2 Version Matrix

Document:

```text
minimum supported aria2
recommended aria2
latest tested aria2
```

Runtime capability detection should handle compatible version differences.

---

# 175. Developer Documentation

Document:

```text
architecture
domain
RPC
daemon
persistence
Tkinter UI
ttkbootstrap styling
ViewModels
testing
typing
security
release process
```

---

# 176. Architecture Decision Records

Create:

```text
docs/adr/
```

Initial ADRs:

```text
0001-aria2-as-download-engine.md
0002-tkinter-ttkbootstrap-ui.md
0003-layered-architecture.md
0004-sqlite-persistence.md
0005-jsonrpc-primary.md
0006-xmlrpc-compatibility.md
0007-typed-option-registry.md
0008-tk-event-loop-integration.md
0009-capability-detection.md
0010-generated-aria2-documentation.md
```

---

# 177. AI Agent Documentation

Create:

```text
AGENTS.md
```

It MUST state:

- architecture
- directory boundaries
- typing requirements
- testing requirements
- UI rules
- aria2 compatibility rules
- security rules
- documentation rules
- no PySide/PyQt/CustomTkinter migration
- no direct UI→RPC calls
- no undocumented features
- no silent option loss

---

# 178. AI Task Specification

Every AI coding task should define:

```text
Goal
Context
Files
Interfaces
Constraints
Acceptance criteria
Tests
Documentation
Non-goals
```

---

# 179. Example AI Task

```text
TASK: Implement typed aria2 option registry

Goal:
Represent all supported aria2 options.

Requirements:
- name
- type
- default
- scope
- protocol
- dynamic status
- validation
- description

Acceptance:
- complete registry coverage
- serializer tests
- validation tests
- generated documentation
- UI metadata
- CI passes
```

---

# 180. Existing Repository Migration

The existing Shusha repository is a source of:

- useful code
- domain knowledge
- documentation
- tests
- UX ideas
- compatibility requirements

It is NOT automatically the architecture for Shusha 2.

Classify existing code:

```text
KEEP
PORT
REWRITE
REPLACE
DELETE
```

---

# 181. Existing Tests

Classify tests:

```text
valuable → port
obsolete → remove
architecture-specific → replace
missing coverage → add
```

Do not blindly copy tests from the old architecture.

---

# 182. Existing Documentation

Classify every document:

```text
keep
rewrite
merge
generate
archive
delete
```

Useful knowledge MUST be migrated before deletion.

---

# 183. Archive

Legacy source should not participate in production tooling.

It may remain:

```text
Git history
archive branch
migration reference
```

but should not be imported by the new application.

---

# 184. Migration Strategy

Do not attempt a single enormous rewrite.

Use phases.

---

# 185. Phase 0 — Repository Audit

Deliver:

```text
docs/REWRITE_AUDIT.md
```

Inventory:

- source
- tests
- docs
- dependencies
- aria2 features
- RPC methods
- UI screens
- settings
- extensions
- platform behavior
- known bugs

---

# 186. Phase 1 — Foundation

Build:

```text
Python 3.14
uv
Ruff
ty
pytest
CI
domain
errors
identifiers
value objects
logging
configuration
```

Acceptance:

```text
uv sync
ruff
ty
pytest
```

all pass.

---

# 187. Phase 2 — aria2 Core

Implement:

```text
JSON-RPC
XML-RPC
typed DTOs
RPC errors
notifications
capabilities
daemon supervisor
```

Acceptance:

```text
connect
add
status
pause
resume
remove
shutdown
```

against real aria2c.

---

# 188. Phase 3 — Option Registry

Implement:

```text
all options
types
defaults
scope
protocol applicability
validation
serialization
documentation generation
```

Acceptance:

```text
complete registry coverage
```

---

# 189. Phase 4 — Persistence

Implement:

```text
SQLite
repositories
migrations
history
profiles
categories
settings
reconciliation
```

---

# 190. Phase 5 — Application Services

Implement:

```text
DownloadService
QueueService
CategoryService
ProfileService
HistoryService
SchedulerService
NotificationService
ReconciliationService
```

---

# 191. Phase 6 — CLI

Implement:

```text
add
list
status
pause
resume
retry
remove
inspect
history
category
profile
config
daemon
```

---

# 192. Phase 7 — ttkbootstrap UI Foundation

Implement:

```text
Tk application shell
theme system
navigation
toolbar
status bar
event dispatcher
ViewModel infrastructure
```

---

# 193. Phase 8 — Main Download UI

Implement:

```text
Dashboard
Download Tree
Search
Filters
Context menu
Inspector
Add Download
```

---

# 194. Phase 9 — Advanced UI

Implement:

```text
Files
Pieces
Peers
Trackers
Servers
Options
Headers
Hashes
Torrent
Metalink
History
Scheduler
Profiles
Categories
Diagnostics
```

---

# 195. Phase 10 — Full aria2 Compatibility

Complete:

```text
options
RPC
notifications
configuration
input files
sessions
protocol-specific behavior
error mapping
capabilities
```

---

# 196. Phase 11 — Testing

Complete:

```text
unit
integration
contract
real aria2
UI smoke
visual regression
performance
cross-platform
```

---

# 197. Phase 12 — Documentation

Complete:

```text
README
user manual
developer manual
aria2 reference
compatibility matrix
security
configuration
CLI
UI
```

---

# 198. Phase 13 — Packaging

Produce:

```text
wheel
sdist
Windows package
macOS package
Linux package
```

---

# 199. Phase 14 — Release Candidate

RC requires:

```text
complete aria2 option registry
required RPC coverage
>=90% test coverage
>=95% core coverage
zero critical type errors
zero critical security defects
zero data-loss defects
cross-platform smoke tests
documentation build
package build
```

---

# 200. UI Screen/Surface Inventory

The UI should be treated as a catalogue of composable surfaces rather than 100+ independent top-level windows.

Major surfaces include:

```text
Main Shell
Dashboard
Download Workspace
History Workspace
Category Workspace
Profile Workspace
Scheduler Workspace
Settings Workspace
Diagnostics Workspace
```

Dialogs:

```text
Add Download
Add Torrent
Add Magnet
Add Metalink
Batch Import
Connection
Category
Profile
Scheduler
Settings
Import
Export
Error
Confirmation
Keyboard Shortcuts
```

Inspectors:

```text
Overview
Files
Pieces
Peers
Trackers
Servers
Sources
Options
Headers
Hashes
Logs
Activity
Metadata
History
```

---

# 201. Every UI Surface Must Define

```text
layout
controls
navigation
keyboard behavior
loading state
empty state
error state
disabled state
accessibility
persistence
events
commands
```

---

# 202. UI State Model

Each screen should distinguish:

```text
Loading
Ready
Empty
Updating
Error
Disconnected
Read-only
Disabled
```

---

# 203. Download Workspace

The download workspace is the primary application screen.

Required:

```text
toolbar
search
filter bar
download tree
selection model
context menu
inspector
status bar
```

---

# 204. Selection Model

Support:

```text
single selection
multi-selection
range selection
Ctrl selection
keyboard navigation
select all
```

Actions should operate consistently on selected downloads.

---

# 205. Bulk Actions

Bulk actions:

```text
Pause
Resume
Retry
Remove
Delete Files
Category
Priority
Move
```

The application must show how many items will be affected.

---

# 206. Confirmation UX

Example:

```text
Remove 8 downloads?

Downloaded data will be preserved.

[Cancel] [Remove]
```

For deletion:

```text
Delete 8 downloads and their local files?

Total data:
14.8 GiB

[Cancel] [Delete Files]
```

---

# 207. Notification Center

Provide a lightweight notification/history surface.

Show:

```text
completed
failed
warnings
aria2 connection events
disk warnings
```

Allow dismissal.

---

# 208. Status Bar

Show:

```text
↓ speed
↑ speed
active count
queue count
aria2 status
RPC latency
```

Do not overload the status bar.

---

# 209. Connection Status

Global indicator:

```text
● Connected
◌ Connecting
! Disconnected
↻ Reconnecting
```

with text.

---

# 210. Theme Switching

Theme switching should occur at runtime where ttkbootstrap supports it.

Do not require restart unless a specific platform limitation makes it necessary.

---

# 211. Custom ttkbootstrap Styling

Prefer semantic `bootstyle` usage.

Centralize custom styles.

Do not put random hex values in individual widgets.

---

# 212. Icon Strategy

Use a consistent icon set.

Icons must have:

- semantic meaning
- accessible labels where necessary
- tooltip text
- consistent sizing

---

# 213. Tooltips

Use tooltips for unfamiliar icons.

Never rely on tooltips as the only way to understand critical actions.

---

# 214. Keyboard Navigation

Every important operation must be reachable without a mouse.

Focus order must be logical.

---

# 215. Accessibility Text

Controls must have meaningful labels.

Bad:

```text
[ ... ]
```

Good:

```text
More actions
```

---

# 216. Settings UI

Settings should use:

```text
navigation
search
category
option editor
description
effective value
reset
apply/save
```

---

# 217. Settings Reset

Support:

```text
Reset option
Reset category
Reset profile
Reset all settings
```

with appropriate confirmation.

---

# 218. Effective Configuration

For each setting display:

```text
Current value
Default value
Source
```

---

# 219. Import Preview

Before importing configuration:

```text
Source
Items
Supported
Deprecated
Unsupported
Invalid
```

Allow selective import where practical.

---

# 220. Error Reporting

Errors should be actionable.

Example:

```text
Unable to connect to aria2.

Host:
127.0.0.1

Port:
6800

Reason:
Connection refused

[Retry]
[Connection Settings]
[Diagnostics]
```

---

# 221. Retry Behavior

Retries must be bounded.

Show:

```text
Retrying...
Attempt 2 of 5
```

Avoid infinite silent retry loops.

---

# 222. Rate Formatting

Use consistent display:

```text
1.2 MiB/s
850 KiB/s
0 B/s
```

Allow user preference:

```text
IEC
SI
```

---

# 223. ETA Formatting

Examples:

```text
12s
4m 12s
2h 13m
Unknown
Seeding
Complete
```

Never display misleading values.

---

# 224. Progress

Show:

```text
73.4%
```

plus:

```text
4.2 GiB / 5.7 GiB
```

where space permits.

---

# 225. Download Details

The user should be able to inspect the complete aria2 state without opening a terminal.

This is a central Shusha value proposition.

---

# 226. Developer Mode

Developer mode may expose:

```text
raw RPC
aria2 capabilities
option metadata
event stream
database diagnostics
performance metrics
```

---

# 227. Performance Diagnostics

Track internally:

```text
RPC latency
poll duration
UI update duration
database query duration
event queue size
```

---

# 228. Event Queue Backpressure

If events arrive faster than the UI can render:

- coalesce progress updates
- preserve important lifecycle events
- drop redundant intermediate progress events

Never drop:

```text
completed
failed
removed
started
paused
```

without replacement.

---

# 229. Progress Coalescing

For example:

```text
10.1%
10.2%
10.3%
10.4%
10.5%
```

may be coalesced into a single UI update while maintaining current state.

---

# 230. Memory Management

Bound:

```text
event history
logs
statistics
peer snapshots
RPC history
```

Avoid unbounded collections.

---

# 231. Database Indexes

Add indexes for:

```text
gid
status
category_id
created_at
completed_at
name
```

and common history queries.

---

# 232. Transaction Rules

Multi-step state mutations should use transactions.

Example:

```text
change category
    ↓
database update
    ↓
event
    ↓
UI update
```

---

# 233. Repository Testing

Every repository should have tests for:

```text
insert
update
delete
query
transaction
migration
corruption handling
```

---

# 234. Database Recovery

Detect corruption/open failures.

Provide a useful diagnostic rather than crashing with a raw SQLite exception.

---

# 235. Configuration Corruption

If configuration is invalid:

```text
preserve original
create recovery copy
report errors
offer reset
```

Never destroy the user's configuration automatically.

---

# 236. Backup Before Migration

Before destructive schema migration:

```text
backup database
run migration
verify
```

---

# 237. Release Versioning

Use Semantic Versioning.

Maintain:

```text
CHANGELOG.md
```

---

# 238. Release Notes

Release notes should distinguish:

```text
New
Changed
Fixed
Security
Deprecated
Removed
```

---

# 239. Security Policy

Create:

```text
SECURITY.md
```

Document responsible disclosure.

---

# 240. Dependency Security

Periodically audit dependencies.

Prioritize security fixes.

---

# 241. License Compliance

Track licenses for:

- Python packages
- icons
- themes
- assets
- bundled components

---

# 242. Build Reproducibility

Use:

```text
uv.lock
```

and pinned spec snapshots.

---

# 243. Generated Files

Clearly identify generated artifacts.

Do not manually edit generated aria2 references.

---

# 244. CI Compatibility Check

CI should run:

```text
aria2 minimum
aria2 recommended
aria2 latest tested
```

where practical.

---

# 245. aria2 Integration Test Categories

```text
HTTP
HTTPS
FTP
SFTP
Torrent
Magnet
Metalink
RPC
Session
Options
Queue
Resume
Checksum
Proxy
Authentication
```

---

# 246. HTTP Test Server

Use a controlled local HTTP server for deterministic tests.

Test:

```text
range requests
redirect
authentication
headers
cookies
resume
checksum
```

---

# 247. FTP Test Environment

Where practical, use a controlled local FTP test server.

---

# 248. SFTP Test Environment

Use a controlled local SSH/SFTP test fixture.

---

# 249. BitTorrent Test Environment

Use deterministic test torrents.

Verify:

```text
metadata
file selection
download
seeding
tracker
peer state
```

---

# 250. Metalink Test Environment

Use controlled Metalink fixtures with:

```text
multiple mirrors
checksums
multiple files
```

---

# 251. Failure Testing

Test:

```text
network failure
server failure
disk failure
invalid URI
permission denied
RPC timeout
aria2 crash
corrupt configuration
invalid option
```

---

# 252. Resume Testing

Test:

```text
partial file
restart aria2
restart Shusha
resume
verify
```

---

# 253. Authentication Testing

Test:

```text
correct credentials
incorrect credentials
missing credentials
expired/invalid auth where applicable
```

Ensure credentials never appear in logs.

---

# 254. Proxy Testing

Test:

```text
HTTP proxy
HTTPS proxy
authentication
no-proxy
```

---

# 255. Checksum Testing

Test:

```text
valid checksum
invalid checksum
missing checksum
piece verification
```

---

# 256. Queue Testing

Test:

```text
position changes
priority
concurrency
pause
resume
restart
```

---

# 257. Scheduler Testing

Test around:

```text
start boundary
end boundary
midnight
weekday/weekend
timezone
```

---

# 258. Clock Handling

Avoid relying directly on wall-clock time in tests.

Inject a clock abstraction where scheduler logic requires it.

---

# 259. Filesystem Testing

Use temporary directories.

Never run tests against user directories.

---

# 260. Test Isolation

Every test should clean up:

```text
downloads
temporary files
aria2 instances
ports
databases
configuration
```

---

# 261. Benchmark Suite

Benchmarks:

```text
startup
RPC polling
100 downloads
1,000 downloads
large history
large torrent
piece map
Treeview updates
database reconciliation
```

---

# 262. Performance Regression Policy

A significant performance regression must be investigated before release.

---

# 263. UI Responsiveness Target

No ordinary user operation should visibly freeze the main window.

Long operations must:

- execute asynchronously
- show progress where useful
- permit cancellation where appropriate

---

# 264. Cancellation

Long operations should support cancellation when safe:

```text
history export
configuration import
filesystem scan
large metadata operation
```

---

# 265. Progress Reporting

Long operations should expose:

```text
current
total
percentage
phase
```

where measurable.

---

# 266. Application Lifecycle

Startup:

```text
initialize configuration
initialize logging
initialize database
load UI state
initialize services
connect/start aria2
reconcile
show UI
```

Shutdown:

```text
save UI state
flush database
stop background tasks
apply aria2 policy
close RPC
exit
```

---

# 267. Graceful Shutdown

Background workers MUST stop cleanly.

No hanging processes.

No orphaned threads where avoidable.

---

# 268. Daemon Shutdown Policy

Respect user preference:

```text
leave running
stop
pause
ask
```

---

# 269. Orphan Process Detection

On startup, detect possible stale local aria2 processes where practical.

Do not kill arbitrary processes.

---

# 270. RPC Port Allocation

For local daemon:

- configured port
- detect conflicts
- choose safe temporary port if policy permits
- record endpoint
- verify readiness

---

# 271. Local Security

Default local aria2 binding should be conservative.

Do not expose RPC publicly by default.

---

# 272. Remote Security

Remote connections should support:

```text
TLS
authentication
certificate validation
```

and clearly warn about insecure connections.

---

# 273. Credential UX

Passwords should display as masked values.

Provide:

```text
show/hide
test
clear
```

without logging the value.

---

# 274. Proxy Credential UX

Treat proxy credentials as secrets.

---

# 275. Header Security

Headers such as:

```text
Authorization
Cookie
Proxy-Authorization
```

must be considered sensitive.

---

# 276. Diagnostic Redaction

Create one centralized:

```text
Redactor
```

used by:

```text
logs
diagnostics
RPC inspector
error reporting
exports
```

---

# 277. No Shell Injection

All process execution must use argument arrays.

Never:

```python
os.system(command)
```

for user-controlled values.

---

# 278. URI Safety

Do not execute URI contents.

URI is data.

---

# 279. Downloaded Files

Never automatically execute downloaded files.

---

# 280. Path Safety

Validate application-generated paths.

Use safe path joining.

---

# 281. Future REST/WebSocket Architecture

Do not implement a web server in the first release.

However, application services must remain sufficiently isolated that a future API can call:

```text
DownloadService
QueueService
HistoryService
```

without depending on Tkinter.

---

# 282. Future Browser Extension

Browser extension should communicate through a future stable API boundary.

---

# 283. Future Multi-Client Architecture

Future clients may include:

```text
desktop
CLI
web
browser extension
mobile
```

all consuming application capabilities.

---

# 284. Plugin Architecture

Do not implement a complicated plugin marketplace in v1.

Create limited internal extension points.

---

# 285. Extension Points

Potential:

```text
DownloadCompletedHandler
DownloadFailedHandler
NotificationProvider
MetadataProvider
AutomationHandler
```

---

# 286. Documentation Source of Truth

The authoritative relationship is:

```text
aria2 upstream specification
        +
normalized spec snapshot
        ↓
typed registry
        ↓
implementation
        ↓
tests
        ↓
generated docs
        ↓
UI
```

---

# 287. Documentation Drift Prevention

CI should detect:

```text
registry differs from generated docs
```

and fail.

---

# 288. API Stability

Internal APIs may change during 2.x development.

Public application interfaces should be documented and versioned.

---

# 289. Deprecation

When removing an application API:

```text
mark deprecated
document replacement
retain transition period
remove in planned release
```

---

# 290. aria2 Deprecated Options

Deprecated aria2 options:

- remain importable where appropriate
- display deprecation status
- remain available in expert mode where compatibility requires
- have migration guidance

---

# 291. Experimental Options

Experimental options:

- expert mode
- warning
- compatibility status
- documentation

---

# 292. Unknown Future aria2 Options

If a newer aria2 supports an option unknown to Shusha:

```text
Unknown aria2 option
```

must be preserved through raw configuration where feasible.

Shusha must not destroy it during config import/export.

---

# 293. Capability-Based UI

If an aria2 capability is unavailable:

```text
feature disabled
reason shown
```

Do not show broken controls.

---

# 294. UI Option Applicability

For protocol-specific options:

```text
BitTorrent only
HTTP only
FTP only
```

the UI should show applicability.

---

# 295. UI Dynamic Status

For startup-only options:

```text
Requires aria2 restart
```

must be displayed.

---

# 296. Restart Workflow

When a configuration change requires restart:

```text
Change detected

This option requires aria2 restart.

[Restart Now]
[Restart Later]
[Cancel]
```

---

# 297. Restart Safety

Before restarting:

```text
save session
confirm active state
restart
reconnect
reconcile
```

---

# 298. User Experience Principle

The UI should explain aria2 concepts rather than expose raw implementation complexity unnecessarily.

Example:

Instead of only:

```text
max-connection-per-server
```

show:

```text
Connections per server

Maximum simultaneous connections Shusha/aria2 may use
against a single server.

Advanced name:
max-connection-per-server
```

---

# 299. Expert User Principle

Advanced users must still be able to access the raw aria2 vocabulary.

Provide:

```text
friendly label
technical option name
raw value
```

---

# 300. Documentation Principle

Every technical option should be explainable in two levels:

```text
User explanation
Technical aria2 explanation
```

---

# 301. UI Tooltip Principle

Tooltips should be concise.

Detailed explanations belong in:

```text
help panel
option documentation
```

---

# 302. Help System

Every advanced option can expose:

```text
What does this do?
```

opening the corresponding documentation.

---

# 303. Search-to-Help

Searching:

```text
max-download-limit
```

should find:

```text
UI setting
profile option
aria2 reference
```

---

# 304. Main UI Information Hierarchy

Priority:

```text
Name
Status
Progress
Speed
ETA
```

Secondary:

```text
size
connections
category
destination
```

Advanced:

```text
GID
server
peer
RPC
raw options
```

---

# 305. Color Usage

Color is supplementary.

Use color for:

```text
positive
warning
error
active
```

but always combine with text/icon/state.

---

# 306. Dark Theme

Dark theme must not simply invert light theme.

Review:

- contrast
- borders
- disabled controls
- Treeview selection
- progress bars
- dialogs
- tooltips
- menus

---

# 307. High Contrast Theme

Provide stronger contrast and avoid subtle state distinctions.

---

# 308. Reduced Motion

Avoid unnecessary animations.

Where animation exists, provide reduced-motion behavior.

---

# 309. Window Persistence

Persist:

```text
window size
window position
navigation width
inspector width
column configuration
theme
sort
filter
```

---

# 310. Safe Defaults

Defaults should favor:

```text
local RPC
secure authentication
non-destructive actions
reasonable concurrency
reasonable polling
```

---

# 311. Advanced User Controls

Power users can override:

```text
polling interval
RPC timeout
connection behavior
UI density
option visibility
```

---

# 312. UI Density

Provide:

```text
Comfortable
Compact
```

density modes where practical.

---

# 313. Table Density

Compact mode reduces:

```text
row height
padding
secondary information
```

without removing core data.

---

# 314. Mobile Is Not a Goal

Shusha 2 is a desktop application.

Do not distort desktop UX to imitate mobile UI patterns.

---

# 315. Desktop-First Design

Prioritize:

- keyboard
- mouse
- multi-select
- context menus
- tables
- inspectors
- docks/panes
- large screens
- high information density

---

# 316. CLI-First Automation

Everything useful in automation should be accessible through the CLI/application layer even if the UI has a richer presentation.

---

# 317. Scriptability

CLI JSON output must be stable enough for scripting.

Example:

```bash
shusha list --json
```

---

# 318. Machine-Readable Errors

CLI should provide structured errors:

```json
{
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

---

# 319. Exit Codes

Document Shusha CLI exit codes.

Do not confuse them with aria2's own exit codes.

---

# 320. aria2 Exit Codes

Document aria2 exit/error semantics separately.

---

# 321. Documentation Links

Where behavior belongs to aria2 rather than Shusha, reference upstream aria2 documentation instead of duplicating it.

---

# 322. Release Artifacts

Each release should include:

```text
source
wheel
platform package
checksums
release notes
compatibility matrix
```

---

# 323. Build Verification

Test installed artifact, not only source tree.

---

# 324. Clean Install Test

Every release candidate should be tested in a clean environment.

---

# 325. Upgrade Test

Test:

```text
old Shusha database
        ↓
new version
        ↓
migration
        ↓
application
```

---

# 326. Downgrade Policy

Document whether downgrade is supported after migrations.

If not:

```text
backup required
```

---

# 327. Data Loss Policy

No migration may silently delete user state.

---

# 328. Corrupt State Policy

When state is corrupt:

```text
preserve
diagnose
recover
```

rather than silently reset.

---

# 329. User Data Locations

Use platform-appropriate directories via `platformdirs`.

Separate:

```text
configuration
database
logs
cache
downloads
```

---

# 330. Cache

Cache only non-authoritative data.

The database remains authoritative for application metadata.

---

# 331. Temporary Files

Use platform temporary directories.

Always clean up.

---

# 332. Log Rotation

Logs must have bounded size.

---

# 333. Crash Logs

Crash diagnostics must be local by default.

No automatic external upload.

---

# 334. Feature Flags

Use feature flags only where necessary.

Do not turn the application into an unmanageable matrix of flags.

---

# 335. Beta Features

Clearly label experimental features.

---

# 336. Configuration Schema Version

Application configuration should include:

```text
schema_version
```

---

# 337. Spec Version

aria2 snapshots should include:

```text
source version
retrieval date
parser version
```

---

# 338. Build Metadata

Application diagnostics should report:

```text
Shusha version
commit
Python
aria2
OS
```

---

# 339. Repository Quality

The repository should be understandable by:

```text
human developers
AI coding agents
future maintainers
```

---

# 340. Code Style

Prefer:

```text
small modules
small functions
explicit dependencies
descriptive names
typed boundaries
```

Avoid cleverness.

---

# 341. Comments

Comments should explain:

```text
why
compatibility constraints
aria2 quirks
threading constraints
```

not restate obvious code.

---

# 342. Docstrings

Public APIs require concise docstrings.

Internal functions require docstrings when behavior is non-obvious.

---

# 343. Type Checker Policy

CI failure on typing errors.

Exceptions must be documented.

---

# 344. Ruff Policy

CI failure on lint/format violations.

---

# 345. Test Policy

New behavior requires tests.

Bug fixes require regression tests.

---

# 346. Documentation Policy

New public behavior requires documentation.

---

# 347. Compatibility Policy

New aria2 behavior requires compatibility metadata.

---

# 348. UI Policy

New UI features require:

```text
loading
empty
error
disabled
keyboard
accessibility
```

states as applicable.

---

# 349. Security Review Policy

Any feature touching:

```text
credentials
filesystem
processes
RPC
remote connections
external commands
```

requires security review.

---

# 350. PR Checklist

```text
Architecture:
[ ] correct layer
[ ] no UI→RPC violation
[ ] no domain→UI dependency

Typing:
[ ] ty passes

Quality:
[ ] Ruff passes

Tests:
[ ] unit tests
[ ] integration where appropriate

UI:
[ ] loading
[ ] empty
[ ] error
[ ] accessibility
[ ] keyboard

Security:
[ ] secrets reviewed
[ ] filesystem reviewed
[ ] subprocess reviewed

Documentation:
[ ] user docs
[ ] developer docs
[ ] compatibility docs
```

---

# 351. Master Definition of Done

A feature is complete only when:

```text
implementation
+
typing
+
tests
+
integration where relevant
+
UI
+
error handling
+
documentation
+
compatibility metadata
+
security review
```

are complete.

---

# 352. Full aria2 Support Definition

Shusha may claim full practical aria2 support only when:

```text
all applicable protocols
all documented options
JSON-RPC
XML-RPC
notifications
sessions
input files
configuration
BitTorrent
Metalink
Magnet
checksums
proxy
authentication
resume
queue
scheduling
daemon lifecycle
errors
logging
```

are represented by the compatibility system and tested to the project's supported aria2 version range.

---

# 353. No Silent Gaps

If Shusha does not expose something:

```text
document it
classify it
provide raw/passthrough access where possible
```

---

# 354. Priority Model

```text
P0 — release blocker
P1 — core
P2 — important UX
P3 — enhancement
P4 — future
```

---

# 355. P0 Examples

```text
data loss
download corruption
credential leakage
RPC security flaw
aria2 process leak
application crash on common workflow
```

---

# 356. P1 Examples

```text
download
pause
resume
remove
queue
HTTP
HTTPS
FTP
SFTP
BitTorrent
Metalink
RPC
configuration
```

---

# 357. P2 Examples

```text
history
graphs
scheduler
profiles
advanced inspector
diagnostics
visual polish
```

---

# 358. P3 Examples

```text
automation
browser integration
advanced themes
additional exports
```

---

# 359. P4 Examples

```text
web interface
mobile client
plugin marketplace
cloud synchronization
```

---

# 360. First Usable Milestone

Deliver:

```text
Python 3.14
uv
Ruff
ty
pytest
typed domain
JSON-RPC
daemon supervisor
CLI
real aria2 integration
```

CLI:

```bash
shusha add URL
shusha list
shusha status
shusha pause GID
shusha resume GID
shusha remove GID
```

---

# 361. Second Milestone

Add:

```text
SQLite
history
profiles
categories
queue
configuration
reconciliation
```

---

# 362. Third Milestone

Add ttkbootstrap:

```text
main shell
download table
add dialog
inspector
settings
themes
```

---

# 363. Fourth Milestone

Add:

```text
BitTorrent inspector
Metalink inspector
files
pieces
peers
trackers
servers
advanced options
scheduler
history
diagnostics
```

---

# 364. Fifth Milestone

Complete:

```text
aria2 compatibility
documentation
CI
cross-platform packaging
security
performance
release
```

---

# 365. Final Product Definition

Shusha 2 is:

> **A modern, strongly typed, cross-platform Tkinter/ttkbootstrap desktop control plane for aria2c.**

It is not:

> a thin GUI wrapper around aria2c.

It is an application platform that makes aria2's extensive capability surface:

- understandable
- discoverable
- configurable
- observable
- scriptable
- testable
- persistent
- accessible

while allowing advanced users to retain direct access to aria2's native vocabulary.

---

# 366. Final Architecture

```text
                         SHUSHA 2
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
       GUI                 CLI              Automation
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    Application Services
                            │
                    Domain / State Models
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
       aria2 RPC         SQLite            OS Services
          │                 │                  │
          │                 │             filesystem
          │                 │             notifications
          │                 │             secrets
          │                 │
          ▼                 ▼
        aria2c          Shusha State
```

---

# 367. GUI Architecture

```text
Tk main thread
       │
       ├── ttkbootstrap
       ├── ttk
       ├── Tk Canvas
       └── Treeview
       │
       ▼
Views
       │
       ▼
ViewModels
       │
       ▼
Application Services
       │
       ▼
Domain
       │
       ▼
Infrastructure
```

The UI MUST never bypass the application layer.

---

# 368. Core Engineering Principle

The most important architectural rule is:

> **The aria2 compatibility layer, not the GUI, is the center of the rewrite.**

The UI is one consumer of the application layer.

The CLI is another.

Future automation is another.

Future remote clients can be another.

---

# 369. Core Compatibility Principle

The most important compatibility rule is:

> **Never invent aria2 semantics.**

When uncertain:

1. consult the authoritative aria2 specification
2. inspect upstream behavior
3. verify against a real aria2 binary
4. encode the behavior in the compatibility registry
5. add a regression test
6. document the behavior

---

# 370. Core Documentation Principle

The documentation pipeline must be:

```text
aria2 specification
        ↓
normalized spec
        ↓
typed registry
        ↓
implementation
        ↓
tests
        ↓
generated reference
        ↓
user documentation
```

---

# 371. Core UI Principle

The UI should expose complexity progressively:

```text
Simple user
    ↓
friendly controls

Power user
    ↓
advanced controls

Expert
    ↓
complete aria2 option registry

Developer
    ↓
raw RPC / diagnostics
```

Everyone accesses the same underlying typed system.

---

# 372. Final Acceptance Matrix

## Runtime

```text
[ ] Python 3.14+
[ ] Windows
[ ] Linux
[ ] macOS
```

## Toolchain

```text
[ ] uv
[ ] Ruff
[ ] ty
[ ] pytest
```

## UI

```text
[ ] Tkinter
[ ] ttk
[ ] ttkbootstrap
[ ] Light theme
[ ] Dark theme
[ ] High contrast
[ ] keyboard support
[ ] accessibility
[ ] responsive large datasets
```

## aria2

```text
[ ] HTTP
[ ] HTTPS
[ ] FTP
[ ] SFTP
[ ] BitTorrent
[ ] Magnet
[ ] Metalink
[ ] options
[ ] JSON-RPC
[ ] XML-RPC
[ ] notifications
[ ] sessions
[ ] input files
[ ] configuration
[ ] proxy
[ ] authentication
[ ] checksum
[ ] resume
[ ] queue
[ ] scheduling
```

## Engineering

```text
[ ] typed domain
[ ] typed RPC
[ ] typed option registry
[ ] SQLite
[ ] daemon supervision
[ ] crash recovery
[ ] reconciliation
[ ] structured logging
[ ] secret handling
```

## Documentation

```text
[ ] README
[ ] user manual
[ ] developer manual
[ ] architecture
[ ] aria2 options
[ ] RPC
[ ] compatibility
[ ] configuration
[ ] CLI
[ ] security
[ ] contributing
[ ] AI agent instructions
```

---

# 373. Final AI Implementation Directive

An AI coding agent implementing this plan MUST:

1. Read `PLAN.md`.
2. Read `AGENTS.md`.
3. Audit the current repository.
4. Produce `docs/REWRITE_AUDIT.md`.
5. Inventory all existing functionality.
6. Inventory all aria2 features.
7. Build the new Python 3.14 foundation.
8. Establish `uv`, Ruff, ty and pytest.
9. Build typed domain models.
10. Build typed aria2 transport.
11. Build daemon supervision.
12. Build capability detection.
13. Build the aria2 option registry.
14. Generate compatibility documentation.
15. Build persistence.
16. Build application services.
17. Build CLI.
18. Build the ttkbootstrap UI shell.
19. Build download management.
20. Build advanced inspectors.
21. Build complete option UI.
22. Build configuration/import/export.
23. Build history.
24. Build scheduler.
25. Build diagnostics.
26. Run real aria2 integration tests.
27. Complete cross-platform testing.
28. Rewrite documentation.
29. Build packages.
30. Perform release-candidate verification.

At every step:

```text
Do not guess aria2 behavior.

Do not introduce PySide6.

Do not introduce PyQt.

Do not introduce CustomTkinter.

Do not put RPC logic in Tk widgets.

Do not put business logic in Tk widgets.

Do not weaken typing.

Do not silently drop aria2 options.

Do not silently swallow errors.

Do not log credentials.

Do not use shell command strings.

Do not declare functionality complete without tests.

Do not declare functionality complete without documentation.

Do not duplicate the aria2 option registry.

Do not create unnecessary dependencies.

Do not sacrifice UI responsiveness for implementation convenience.
```

---

# 374. Ultimate Success Criterion

A Shusha 2 release is successful when:

```text
User
 │
 ▼
Modern ttkbootstrap desktop UI
 │
 ▼
Typed application services
 │
 ▼
Typed domain model
 │
 ▼
Complete aria2 compatibility layer
 │
 ▼
JSON-RPC / XML-RPC
 │
 ▼
aria2c
 │
 ▼
Real downloads
```

and every important capability can be traced backwards through:

```text
UI
 ↓
application
 ↓
domain
 ↓
aria2
 ↓
specification
 ↓
test
 ↓
documentation
```

with no undocumented or silently unsupported behavior.

---

# 375. End State

The final Shusha repository should represent:

```text
Python 3.14+
        +
Astral uv
        +
Ruff
        +
ty
        +
pytest
        +
Typed Domain Architecture
        +
Typed aria2 RPC
        +
Complete aria2 Option Registry
        +
JSON-RPC
        +
XML-RPC
        +
Daemon Supervision
        +
SQLite
        +
ttkbootstrap
        +
Modern Tkinter UX
        +
Keyboard Accessibility
        +
Light/Dark Themes
        +
Large Dataset Performance
        +
CLI
        +
History
        +
Profiles
        +
Categories
        +
Scheduler
        +
Diagnostics
        +
Cross-platform Packaging
        +
Comprehensive Documentation
        +
AI-Friendly Repository
```

This is the authoritative target architecture for **Shusha 2**.