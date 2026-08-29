# PLAN.md

# Shusha Rewrite — Python 3.14 / ttkbootstrap / aria2c Full-Coverage Plan

> **Status:** Rewrite master plan  
> **Target:** Python 3.14+  
> **GUI:** `ttkbootstrap` / Tkinter / ttk  
> **Toolchain:** Astral `uv`, Ruff, ty, pytest  
> **Backend:** aria2c  
> **Architecture:** typed domain + application services + infrastructure adapters + presentation layer  
> **Primary objective:** modernize Shusha while achieving comprehensive aria2c feature/specification coverage without coupling the UI to aria2's transport protocol.

---

## 1. Mission

Shusha is to be rewritten as a modern, strongly typed Python 3.14 desktop download manager built around aria2c.

The rewrite must provide:

1. A polished `ttkbootstrap` desktop UI.
2. Full practical coverage of the aria2c command-line/RPC capability surface.
3. Strong type safety.
4. Clean separation between domain, application, infrastructure, and presentation.
5. Reliable local and remote aria2 daemon management.
6. HTTP/HTTPS/FTP/SFTP support.
7. BitTorrent and Magnet support.
8. Metalink support.
9. Checksums and integrity verification.
10. Queue management.
11. Scheduling.
12. Session persistence.
13. Proxy/authentication configuration.
14. Server/peer/tracker inspection.
15. Statistics and diagnostics.
16. Secure credential handling.
17. Cross-platform behavior.
18. Comprehensive automated tests.
19. Complete developer/user documentation.
20. Machine-checkable correspondence between aria2 documentation, option registry, implementation, UI, and tests.

The rewrite is **not** a mechanical port.

The intended strategy is:

```text
Existing Shusha
      │
      ▼
Phase 0 audit
      │
      ▼
Compatibility map
      │
      ▼
New typed domain
      │
      ▼
New application services
      │
      ▼
New aria2 infrastructure
      │
      ▼
New ttkbootstrap UI
      │
      ▼
Feature parity
      │
      ▼
Validation
      │
      ▼
Legacy removal
```

---

# 2. Non-Negotiable Decisions

## 2.1 Python

Target:

```text
Python 3.14+
```

The rewrite does not maintain compatibility with Python 3.10–3.13.

Use modern Python typing and language features where they improve correctness.

---

## 2.2 GUI

The official GUI framework is:

```text
Tkinter
  └── ttk
       └── ttkbootstrap
```

Do **not** introduce CustomTkinter.

Do not mix CustomTkinter and ttkbootstrap.

Do not introduce a second widget toolkit.

---

## 2.3 Toolchain

Use Astral tooling:

```bash
uv
ruff
ty
```

Testing:

```bash
pytest
pytest-cov
```

Canonical commands:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest --cov
uv build
```

---

## 2.4 Architecture

Required dependency direction:

```text
presentation
     │
     ▼
application
     │
     ▼
domain

infrastructure ───────► domain/application contracts
```

The domain must never import:

```text
tkinter
ttkbootstrap
aria2 RPC implementation
subprocess
sqlite implementation
platform-specific APIs
```

The presentation layer must not directly invoke aria2 RPC.

---

## 2.5 aria2 as an external system

aria2 is an external dependency.

Treat it as:

```text
external process
external protocol
external version
external state machine
external failure domain
```

Never make aria2 implementation details leak throughout the application.

---

# 3. Target Repository

```text
shusha/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── tests.yml
│   │   ├── typecheck.yml
│   │   ├── docs.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug.yml
│   │   ├── feature.yml
│   │   ├── aria2-compatibility.yml
│   │   └── ui-ux.yml
│   └── pull_request_template.md
│
├── docs/
│   ├── architecture/
│   │   ├── OVERVIEW.md
│   │   ├── DOMAIN.md
│   │   ├── APPLICATION.md
│   │   ├── INFRASTRUCTURE.md
│   │   ├── UI.md
│   │   └── DATA_FLOW.md
│   ├── aria2/
│   │   ├── ARIA2_COMPATIBILITY.md
│   │   ├── ARIA2_OPTION_MATRIX.md
│   │   ├── ARIA2_RPC_MATRIX.md
│   │   ├── ARIA2_EVENT_MATRIX.md
│   │   ├── ARIA2_STATUS_MODEL.md
│   │   ├── ARIA2_ERROR_MODEL.md
│   │   └── ARIA2_VERSION_POLICY.md
│   ├── api/
│   │   ├── DOMAIN_API.md
│   │   ├── APPLICATION_API.md
│   │   └── RPC_API.md
│   ├── ui/
│   │   ├── DESIGN_SYSTEM.md
│   │   ├── INFORMATION_ARCHITECTURE.md
│   │   ├── SCREEN_CATALOGUE.md
│   │   ├── INTERACTION_MODEL.md
│   │   └── ACCESSIBILITY.md
│   ├── development/
│   │   ├── DEVELOPMENT.md
│   │   ├── TESTING.md
│   │   ├── TYPE_CHECKING.md
│   │   ├── RELEASES.md
│   │   └── AI_AGENT_GUIDE.md
│   └── audit/
│       ├── REPOSITORY_AUDIT.md
│       ├── CURRENT_ARCHITECTURE.md
│       ├── CURRENT_FEATURE_MATRIX.md
│       ├── CURRENT_ARIA2_COVERAGE.md
│       ├── CURRENT_UI_AUDIT.md
│       ├── CURRENT_TEST_AUDIT.md
│       ├── CURRENT_DOCUMENTATION_AUDIT.md
│       ├── DEPENDENCY_AUDIT.md
│       ├── TYPE_AUDIT.md
│       ├── SECURITY_AUDIT.md
│       ├── DEAD_CODE_AUDIT.md
│       ├── MIGRATION_MAP.md
│       └── PHASE_0_FINDINGS.md
│
├── src/
│   └── shusha/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       │
│       ├── domain/
│       │   ├── download.py
│       │   ├── download_file.py
│       │   ├── download_source.py
│       │   ├── download_status.py
│       │   ├── torrent.py
│       │   ├── metalink.py
│       │   ├── peer.py
│       │   ├── server.py
│       │   ├── checksum.py
│       │   ├── speed.py
│       │   ├── statistics.py
│       │   ├── category.py
│       │   ├── scheduler.py
│       │   ├── settings.py
│       │   ├── session.py
│       │   ├── errors.py
│       │   └── events.py
│       │
│       ├── application/
│       │   ├── app.py
│       │   ├── commands/
│       │   ├── queries/
│       │   └── services/
│       │
│       ├── infrastructure/
│       │   ├── aria2/
│       │   ├── daemon/
│       │   ├── persistence/
│       │   ├── configuration/
│       │   ├── filesystem/
│       │   ├── os/
│       │   └── networking/
│       │
│       ├── presentation/
│       │   ├── app.py
│       │   ├── state.py
│       │   ├── commands.py
│       │   ├── bindings.py
│       │   ├── components/
│       │   ├── windows/
│       │   ├── dialogs/
│       │   └── theme/
│       │
│       ├── platform/
│       └── shared/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── presentation/
│   ├── e2e/
│   └── fixtures/
│
├── scripts/
│   ├── audit_repository.py
│   ├── generate_aria2_matrix.py
│   ├── check_docs.py
│   └── check_options.py
│
├── AGENTS.md
├── PLAN.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE.txt
├── pyproject.toml
└── uv.lock
```

The tree is a **target state**, not a requirement to move every file immediately.

---

# 4. Work State Model

Every issue must be maintained in one of:

```text
PLANNED
READY
IN_PROGRESS
BLOCKED
IN_REVIEW
DONE
REJECTED
SUPERSEDED
```

An issue may only become `DONE` when its acceptance criteria are satisfied.

---

# 5. Dependency Graph

High-level dependency graph:

```text
EPIC 0  Audit
  │
  ├───────────────┐
  ▼               ▼
EPIC 1          EPIC 5
aria2 spec      persistence design
  │
  ▼
EPIC 2
domain
  │
  ├──────────────┐
  ▼              ▼
EPIC 3          EPIC 4
RPC             daemon
  │              │
  └──────┬───────┘
         ▼
      EPIC 6
    application
         │
         ▼
      EPIC 7
        UI
         │
   ┌─────┼──────────────┐
   ▼     ▼              ▼
EPIC 8 EPIC 9         EPIC 10
Options Scheduler     Queue
   │     │              │
   └─────┼──────────────┘
         ▼
   EPIC 11 / 12
 BitTorrent / Metalink
         │
         ▼
      EPIC 13
      Security
         │
         ▼
      EPIC 14
   Observability
         │
         ▼
      EPIC 15
 OS integration
         │
         ▼
      EPIC 16
      Testing
         │
         ▼
      EPIC 17
 Documentation
         │
         ▼
      EPIC 18
 Consistency gates
         │
         ▼
      EPIC 19
 Packaging
         │
         ▼
      EPIC 20
 CI/CD
         │
         ▼
      EPIC 21
 Migration/removal
```

---

# 6. EPIC 0 — Repository Audit

## P0-001 — Establish reproducible baseline

**Dependencies:** none.

### Agent task

Inspect the repository without modifying application architecture.

Record:

- git branch
- commit
- Python version
- uv version
- aria2 version if installed
- operating system
- dependency lock state
- Ruff status
- ty status
- pytest status
- coverage
- build status

### Acceptance criteria

- `docs/audit/PHASE_0_FINDINGS.md` exists.
- Baseline commands are documented.
- Every failing command has its failure captured.
- No failures are hidden or silently ignored.

---

## P0-002 — Source inventory

**Dependencies:** P0-001.

### Agent task

Inventory every Python module and classify:

- purpose
- public API
- imports
- side effects
- UI coupling
- aria2 coupling
- persistence coupling
- subprocess usage
- network usage
- test coverage
- rewrite disposition

### Acceptance criteria

Every source file appears exactly once in the inventory.

Each is marked:

```text
KEEP
REWRITE
ADAPT
REMOVE
UNKNOWN
```

---

## P0-003 — Feature inventory

**Dependencies:** P0-002.

### Agent task

Inventory all current functionality.

Minimum categories:

- downloads
- HTTP
- HTTPS
- FTP
- SFTP
- BitTorrent
- Magnet
- Metalink
- RPC
- daemon
- scheduler
- authentication
- proxy
- checksums
- file selection
- sessions
- notifications
- tray
- clipboard
- trackers
- peers
- mirrors
- media extraction
- WebSocket
- webhook
- statistics
- categories
- search
- filtering
- settings

### Acceptance criteria

`CURRENT_FEATURE_MATRIX.md` exists with:

```text
feature
current implementation
tests
documentation
new implementation
status
```

---

## P0-004 — Test audit

**Dependencies:** P0-002.

### Agent task

Classify all tests and identify coverage gaps.

### Acceptance criteria

Every existing test has a mapped feature/module.

No test is deleted during Phase 0.

---

## P0-005 — Dependency audit

**Dependencies:** P0-001.

### Agent task

Classify dependencies:

```text
runtime
development
optional
platform
unused
duplicate
legacy
```

### Acceptance criteria

`DEPENDENCY_AUDIT.md` identifies every direct dependency and its rewrite disposition.

---

## P0-006 — Architecture audit

**Dependencies:** P0-002, P0-003.

### Agent task

Document actual architecture rather than README architecture.

Identify:

- circular dependencies
- UI/business coupling
- RPC leakage
- global state
- mutable singleton state
- subprocess coupling
- persistence coupling
- threading/event-loop assumptions

### Acceptance criteria

`CURRENT_ARCHITECTURE.md` contains an actual dependency diagram.

---

## P0-007 — Security audit

**Dependencies:** P0-002.

### Agent task

Search for:

- credentials
- tokens
- secrets
- unsafe subprocess calls
- shell invocation
- path traversal
- unsafe URL handling
- insecure temporary files
- logging of secrets
- permissive config files

### Acceptance criteria

Every finding receives:

```text
severity
location
risk
recommendation
rewrite disposition
```

---

## P0-008 — Dead-code audit

**Dependencies:** P0-002.

### Agent task

Identify:

- unused modules
- obsolete views
- abandoned experiments
- archive code
- duplicate implementations
- unreachable branches

### Acceptance criteria

No code is deleted solely based on static analysis.

Each candidate is explicitly classified.

---

## P0-009 — Migration map

**Dependencies:** P0-002 through P0-008.

### Acceptance criteria

Every existing feature maps to:

```text
old location
new location
migration strategy
tests
documentation
```

---

# 7. EPIC 1 — aria2 Specification Baseline

## P1-001 — Build aria2 option registry

**Dependencies:** P0-003.

### Agent task

Create a machine-readable catalogue of all relevant aria2 options.

Each record must include:

```text
name
short_name
category
type
default
minimum
maximum
enum_values
scope
rpc_supported
cli_supported
sensitive
deprecated
experimental
description
documentation_reference
```

### Acceptance criteria

Every option in the supported aria2 manual surface is accounted for.

Unknown options are explicitly recorded as unknown rather than omitted.

---

## P1-002 — Categorize options

**Dependencies:** P1-001.

### Acceptance criteria

Every option belongs to a defined category.

No option belongs to two categories unless explicitly marked multi-category.

---

## P1-003 — Build RPC method registry

**Dependencies:** P1-001.

### Agent task

Catalogue all supported aria2 RPC methods.

### Acceptance criteria

Each method has:

```text
name
parameters
return type
errors
authentication requirements
feature area
tests
```

---

## P1-004 — Build event registry

**Dependencies:** P1-003.

### Acceptance criteria

All relevant aria2 event notifications have typed mappings.

---

## P1-005 — aria2 version policy

**Dependencies:** P1-001, P1-003.

### Acceptance criteria

Document:

- minimum supported aria2 version
- tested versions
- unsupported versions
- capability detection
- version-dependent behavior

---

# 8. EPIC 2 — Domain Model

## P2-001 — Download aggregate

**Dependencies:** P1-001.

Implement:

```text
Download
DownloadId
DownloadStatus
DownloadProgress
DownloadSource
DownloadFile
DownloadError
```

### Acceptance criteria

- no raw aria2 dictionaries
- immutable/value semantics where appropriate
- complete typing
- unit tests
- serialization tests

---

## P2-002 — Torrent domain

**Dependencies:** P2-001.

Implement:

```text
Torrent
TorrentFile
Peer
Tracker
Piece
```

### Acceptance criteria

All fields needed by the application are represented without transport-specific names leaking into the domain.

---

## P2-003 — Metalink domain

**Dependencies:** P2-001.

Implement:

```text
Metalink
MetalinkFile
Mirror
Checksum
```

---

## P2-004 — Statistics domain

**Dependencies:** P2-001.

Implement:

```text
DownloadStatistics
GlobalStatistics
ServerStatistics
SpeedSample
```

---

## P2-005 — Event domain

**Dependencies:** P2-001 through P2-004.

Implement typed application events.

### Acceptance criteria

Events are transport-independent.

---

## P2-006 — Error model

**Dependencies:** P2-001.

Create structured errors for:

```text
connection
authentication
RPC
aria2
filesystem
validation
configuration
persistence
network
daemon
```

### Acceptance criteria

User-facing errors never require parsing arbitrary strings in UI code.

---

# 9. EPIC 3 — aria2 Infrastructure

## P3-001 — RPC transport

**Dependencies:** P1-003, P2-006.

Implement typed JSON-RPC transport.

Required:

- request IDs
- timeouts
- retries where safe
- authentication
- RPC errors
- malformed response handling
- cancellation strategy

### Acceptance criteria

No raw transport response escapes the infrastructure boundary.

---

## P3-002 — RPC models

**Dependencies:** P2-001 through P2-004.

Implement serializers/deserializers.

### Acceptance criteria

Malformed external data produces typed validation errors.

---

## P3-003 — RPC client

**Dependencies:** P3-001, P3-002.

Implement typed client methods.

Example:

```python
await client.tell_status(download_id)
```

not:

```python
await client.call("aria2.tellStatus", ...)
```

outside infrastructure.

---

## P3-004 — Capability detection

**Dependencies:** P3-003.

Detect:

- aria2 version
- methods
- supported options
- optional features

### Acceptance criteria

Unsupported capabilities produce explicit capability errors.

---

## P3-005 — Event transport

**Dependencies:** P3-003, P1-004.

Implement event subscription/translation.

---

# 10. EPIC 4 — Daemon Lifecycle

## P4-001 — Discovery

**Dependencies:** P0-006.

Detect configured/local aria2 executables.

---

## P4-002 — Command builder

**Dependencies:** P1-001.

Build daemon arguments from typed configuration.

Never concatenate shell commands.

---

## P4-003 — Process supervisor

**Dependencies:** P4-002.

States:

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

## P4-004 — Health monitor

**Dependencies:** P3-003, P4-003.

### Acceptance criteria

Daemon failures generate typed events.

---

## P4-005 — Remote daemon support

**Dependencies:** P3-003.

Support connecting to a remote aria2 RPC endpoint.

---

# 11. EPIC 5 — Persistence

## P5-001 — Persistence contracts

**Dependencies:** P2 domain.

Create protocols:

```text
DownloadRepository
SettingsRepository
SessionRepository
CategoryRepository
```

---

## P5-002 — Database implementation

**Dependencies:** P5-001.

Use an implementation appropriate to the application requirements.

Requirements:

- schema version
- migrations
- transactions
- atomic updates
- corruption handling

---

## P5-003 — Configuration persistence

**Dependencies:** P5-001.

Persist:

- application settings
- UI state
- daemon profiles
- categories
- schedules
- preferences

---

## P5-004 — Import/export

**Dependencies:** P5-002, P5-003.

Support safe configuration export/import.

---

# 12. EPIC 6 — Application Layer

## P6-001 — Application composition root

**Dependencies:** P2, P3, P4, P5.

Construct all dependencies explicitly.

No hidden global service locator.

---

## P6-002 — Add download use case

**Dependencies:** P6-001.

---

## P6-003 — Pause/resume use cases

**Dependencies:** P6-001.

---

## P6-004 — Remove/retry use cases

**Dependencies:** P6-001.

---

## P6-005 — Queue operations

**Dependencies:** P6-001.

---

## P6-006 — Change options

**Dependencies:** P1-001, P6-001.

---

## P6-007 — Download inspection

**Dependencies:** P3-003, P2 models.

---

## P6-008 — Statistics queries

**Dependencies:** P2-004, P3-003.

---

## P6-009 — Scheduling service

**Dependencies:** P5-003, P6-005.

---

## P6-010 — Notification service

**Dependencies:** P6 events.

---

# 13. EPIC 7 — ttkbootstrap UI

## P7-001 — Design system

**Dependencies:** P0-006.

Define:

- typography
- spacing
- colors
- icons
- status states
- controls
- tables
- dialogs
- menus
- accessibility conventions

---

## P7-002 — Application shell

**Dependencies:** P7-001, P6-001.

Implement:

```text
menu
toolbar
sidebar
content
status bar
notifications
```

---

## P7-003 — Download table

**Dependencies:** P7-002, P6 queries.

Features:

- sorting
- filtering
- search
- multi-select
- keyboard navigation
- context menu
- status indicators
- progress
- speed
- ETA

---

## P7-004 — Add Download wizard

**Dependencies:** P7-002, P6-002.

Stages:

```text
Source
Destination
Files
Options
Review
Start
```

---

## P7-005 — Download inspector

**Dependencies:** P7-003.

Tabs:

```text
Overview
Files
Connections
Peers
Servers
Options
Logs
Hashes
```

---

## P7-006 — Settings

**Dependencies:** P1 option registry, P7-001.

Support:

```text
Basic
Advanced
Expert
```

All settings must map to aria2 options.

---

## P7-007 — Error and empty states

**Dependencies:** P7-002.

Every major screen must define:

```text
loading
empty
error
offline
disabled
permission denied
```

---

# 14. EPIC 8 — Full aria2 Option UX

## P8-001 — Option editor engine

**Dependencies:** P1-001, P7-006.

Generate UI controls from `OptionDefinition`.

---

## P8-002 — Validation engine

**Dependencies:** P8-001.

Support:

- numeric ranges
- enums
- paths
- URLs
- durations
- sizes
- booleans
- lists
- structured values

---

## P8-003 — Option documentation links

**Dependencies:** P8-001.

Every advanced option exposes its aria2 documentation reference.

---

## P8-004 — Scope handling

**Dependencies:** P8-001.

Distinguish:

```text
global option
download option
daemon option
read-only status
```

---

## P8-005 — Sensitive options

**Dependencies:** P8-001, EPIC 13.

Mask credentials and secrets.

---

# 15. EPIC 9 — Scheduler

## P9-001 — Schedule domain

**Dependencies:** P2-005.

---

## P9-002 — Schedule persistence

**Dependencies:** P5-003, P9-001.

---

## P9-003 — Scheduler engine

**Dependencies:** P9-001, P9-002.

---

## P9-004 — Scheduler UI

**Dependencies:** P7-006, P9-003.

Support:

```text
days
times
start
pause
bandwidth
concurrency
recurrence
```

---

# 16. EPIC 10 — Queue

## P10-001 — Queue model

**Dependencies:** P2-001.

---

## P10-002 — Queue operations

**Dependencies:** P10-001, P6-005.

Support:

```text
move up
move down
move top
move bottom
priority
bulk operations
```

---

## P10-003 — Queue UI

**Dependencies:** P7-003, P10-002.

---

# 17. EPIC 11 — BitTorrent

## P11-001 — Torrent ingestion

**Dependencies:** P6-002, P2-002.

Support:

```text
.torrent
magnet
```

---

## P11-002 — Torrent file selection

**Dependencies:** P11-001, P7-004.

---

## P11-003 — Peer view

**Dependencies:** P2-002, P3-003, P7-005.

---

## P11-004 — Tracker view

**Dependencies:** P2-002, P7-005.

---

## P11-005 — BitTorrent options

**Dependencies:** P8 option engine.

---

# 18. EPIC 12 — Metalink

## P12-001 — Metalink ingestion

**Dependencies:** P6-002, P2-003.

---

## P12-002 — Mirror management

**Dependencies:** P12-001.

---

## P12-003 — Checksum/piece verification

**Dependencies:** P2-003, P2-004.

---

# 19. EPIC 13 — Security

## P13-001 — Secret storage abstraction

**Dependencies:** P5-003.

---

## P13-002 — Credential redaction

**Dependencies:** P13-001, P14-001.

---

## P13-003 — Secure subprocess execution

**Dependencies:** P4-002.

Rules:

- no shell interpolation
- argument arrays
- explicit executable paths
- validated environment
- controlled working directories

---

## P13-004 — Filesystem security

**Dependencies:** P2, P5.

Protect against:

- path traversal
- invalid destinations
- symlink surprises
- unsafe filenames

---

## P13-005 — URI security

**Dependencies:** P6-002.

Validate external URLs and avoid leaking credentials.

---

# 20. EPIC 14 — Observability

## P14-001 — Structured logging

**Dependencies:** P2-006.

Include:

```text
timestamp
level
component
event
download_id
request_id
error
```

---

## P14-002 — Diagnostics bundle

**Dependencies:** P14-001.

Provide a user-exportable diagnostic report without secrets.

---

## P14-003 — aria2 log integration

**Dependencies:** P4, P14-001.

---

# 21. EPIC 15 — OS Integration

## P15-001 — Notifications

**Dependencies:** P6-010.

---

## P15-002 — Clipboard integration

**Dependencies:** P7-002.

Clipboard monitoring must be explicitly opt-in/configurable where appropriate.

---

## P15-003 — File opening

**Dependencies:** P7-005.

---

## P15-004 — System tray

**Dependencies:** P7-002.

---

## P15-005 — Platform abstraction

**Dependencies:** P15-001 through P15-004.

Supported targets:

```text
Windows
Linux
macOS
```

---

# 22. EPIC 16 — Testing

## P16-001 — Test architecture

**Dependencies:** EPIC 2.

Establish:

```text
tests/unit
tests/integration
tests/presentation
tests/e2e
tests/fixtures
```

---

## P16-002 — Domain tests

**Dependencies:** P2.

Target:

```text
>=95%
```

for meaningful domain behavior.

---

## P16-003 — RPC tests

**Dependencies:** P3.

Use deterministic fixtures/mocks.

---

## P16-004 — Daemon tests

**Dependencies:** P4.

Test lifecycle transitions and failures.

---

## P16-005 — Persistence tests

**Dependencies:** P5.

Test migrations, corruption, rollback and recovery.

---

## P16-006 — Application tests

**Dependencies:** P6.

---

## P16-007 — Presentation tests

**Dependencies:** P7.

Focus on behavior rather than meaningless line coverage.

---

## P16-008 — End-to-end tests

**Dependencies:** P3, P4, P6, P7.

Where practical, test against a real aria2 daemon.

---

## P16-009 — Compatibility tests

**Dependencies:** P1, P3, P8.

Every supported aria2 option/method should have either:

```text
automated test
```

or an explicit documented reason why it cannot be automatically tested.

---

# 23. EPIC 17 — Documentation

## P17-001 — README rewrite

**Dependencies:** P7, P19.

README must explain:

- purpose
- screenshots
- installation
- aria2 requirements
- quick start
- supported platforms
- features
- troubleshooting
- development

---

## P17-002 — Architecture documentation

**Dependencies:** EPIC 2–7.

---

## P17-003 — aria2 compatibility documentation

**Dependencies:** EPIC 1, 8, 11, 12.

---

## P17-004 — User guide

**Dependencies:** P7.

---

## P17-005 — Developer guide

**Dependencies:** EPIC 16.

---

## P17-006 — AI agent guide

**Dependencies:** architecture stabilized.

Document repository conventions and safe modification procedures.

---

# 24. EPIC 18 — Consistency Automation

## P18-001 — Option consistency checker

**Dependencies:** P1, P8.

Verify:

```text
registry
implementation
UI
documentation
tests
```

---

## P18-002 — RPC consistency checker

**Dependencies:** P1, P3.

---

## P18-003 — Documentation link checker

**Dependencies:** P17.

---

## P18-004 — Architecture import checker

**Dependencies:** P2–P7.

Fail CI if forbidden dependency directions are introduced.

---

# 25. EPIC 19 — Packaging

## P19-001 — Python package

**Dependencies:** P7.

---

## P19-002 — Build validation

**Dependencies:** P19-001.

Validate:

```bash
uv build
```

and installation from generated artifacts.

---

## P19-003 — Platform packaging

**Dependencies:** P19-002, P15.

Produce/document:

```text
Windows
Linux
macOS
```

release strategy.

---

# 26. EPIC 20 — CI/CD

## P20-001 — Static CI

**Dependencies:** P19.

Required:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

---

## P20-002 — Test CI

**Dependencies:** P16.

Required:

```bash
uv run pytest
```

---

## P20-003 — Build CI

**Dependencies:** P19.

---

## P20-004 — Multi-platform CI

**Dependencies:** P20-001, P20-002.

---

## P20-005 — Documentation CI

**Dependencies:** P18.

---

# 27. EPIC 21 — Legacy Migration and Removal

## P21-001 — Feature parity audit

**Dependencies:** P8–P18.

Create a matrix comparing old and new implementations.

---

## P21-002 — Migration validation

**Dependencies:** P21-001.

Every feature must be:

```text
MIGRATED
REPLACED
INTENTIONALLY REMOVED
```

No `UNKNOWN`.

---

## P21-003 — Remove legacy UI

**Dependencies:** P21-002.

---

## P21-004 — Remove legacy controllers

**Dependencies:** P21-002.

---

## P21-005 — Remove obsolete infrastructure

**Dependencies:** P21-002.

---

## P21-006 — Final dead-code audit

**Dependencies:** P21-003 through P21-005.

---

# 28. Global Definition of Done

No issue is complete unless applicable requirements are satisfied.

```text
[ ] Implementation complete
[ ] Public API typed
[ ] External boundaries typed
[ ] Tests added
[ ] Existing tests preserved or migrated
[ ] Error handling implemented
[ ] Security considered
[ ] Logging considered
[ ] Documentation updated
[ ] aria2 mapping updated
[ ] UI updated if applicable
[ ] No architecture violation
[ ] Ruff clean
[ ] Ruff format clean
[ ] ty clean
[ ] pytest clean
[ ] Build succeeds
```

---

# 29. Global AI Agent Stop Conditions

The agent MUST stop and report rather than guess when:

1. aria2 behavior is ambiguous.
2. The upstream specification contradicts an existing implementation.
3. A destructive migration is required without an approved strategy.
4. A credential/security decision is unclear.
5. An existing feature cannot be mapped.
6. A dependency cannot be removed safely.
7. A test expectation contradicts documented behavior.
8. A platform-specific behavior cannot be verified.
9. The agent would need to invent an aria2 option or RPC method.
10. The agent would need to introduce `Any` to make type checking pass.
11. The agent would need to bypass a failing test without understanding it.
12. A UI behavior cannot be inferred safely from the specification.

When blocked, produce:

```text
BLOCKED:
Question:
Evidence:
Current behavior:
Expected behavior:
Options:
Recommended resolution:
```

---

# 30. Commit Strategy

Prefer small commits.

Examples:

```text
audit: establish phase 0 repository baseline
audit: inventory current features
audit: map aria2 compatibility surface
build: configure Python 3.14 astral toolchain
feat(domain): introduce typed download model
feat(aria2): add typed rpc transport
feat(daemon): implement lifecycle supervisor
feat(app): add download use cases
feat(ui): introduce ttkbootstrap application shell
feat(ui): add download table
feat(options): add aria2 option registry
feat(torrent): add torrent inspection
feat(metalink): add metalink support
test(aria2): add rpc compatibility fixtures
docs: rewrite architecture documentation
ci: add cross-platform validation
refactor: remove legacy controller layer
```

Do not create giant commits containing unrelated architectural changes.

---

# 31. Final Release Gate

The rewrite is not considered complete until:

```text
Phase 0 audit complete
        +
aria2 compatibility matrix complete
        +
typed domain complete
        +
RPC complete
        +
daemon lifecycle complete
        +
persistence complete
        +
application services complete
        +
ttkbootstrap UI complete
        +
full option editor complete
        +
BitTorrent complete
        +
Metalink complete
        +
security review complete
        +
tests passing
        +
documentation complete
        +
CI green
        +
packaging validated
        +
legacy code removed
```

The final criterion is:

> **A new contributor or AI coding agent can understand, build, test, modify and extend Shusha without needing to reverse-engineer undocumented behavior from the old implementation.**