# Shusha Rewrite — Master Architecture & AI Execution Plan

**Status:** LOCKED ARCHITECTURE CONTRACT  
**Target:** Python 3.14+  
**Package/toolchain:** Astral `uv`, Ruff, ty, pytest  
**Desktop:** ttkbootstrap  
**TUI/diagnostics:** Textual  
**CLI:** Python CLI sharing the application layer  
**Reference backend:** aria2c  
**Secondary backend:** yt-dlp  
**Architecture:** multi-backend + multi-frontend + acquisition platform + plugin ecosystem

---

# 1. Mission

Rewrite Shusha into a modern, strongly typed, extensible download acquisition and orchestration platform.

Shusha MUST NOT become an aria2 GUI with additional integrations bolted on.

The target product is:

> **A multi-backend download acquisition and orchestration platform with a shared typed application core, ttkbootstrap desktop UI, Textual operator/diagnostics UI, CLI automation interface, browser integration, clipboard capture, media acquisition, and a versioned plugin architecture.**

aria2c is the first reference execution backend.

yt-dlp is the first major secondary backend.

The existing 132-screen desktop catalogue is the **initial aria2 feature-completeness baseline**, not a permanent restriction on the application's information architecture.

---

# 2. Current Repository Baseline

The current repository already contains:

- `src/shusha`
- ttkbootstrap/Tkinter GUI
- MVC-oriented organization
- aria2 client integration
- daemon/process supervision
- settings persistence
- download models
- statistics
- tests
- documentation
- `uv.lock`
- Astral `uv`
- Ruff
- ty

The repository currently describes Shusha as an aria2 wrapper with ttkbootstrap and local daemon orchestration. The rewrite changes the architectural center from "aria2 GUI" to "multi-backend orchestration platform." [SOURCE: current repository dev branch]

The existing aria2 functionality MUST be preserved or intentionally superseded only where the new architecture provides an explicit replacement.

---

# 3. Locked Architectural Principles

## AP-001 — Multi-backend is fundamental

Backend implementations are replaceable execution engines.

Initial:

```text
aria2
yt-dlp
```

Future:

```text
third-party plugins
additional media engines
future download engines
```

No application service may depend directly on a concrete backend.

---

## AP-002 — aria2 is not the domain model

Core MUST NOT contain aria2-specific concepts as fundamental domain primitives.

Forbidden core coupling:

```text
Aria2Download
Aria2Peer
Aria2RpcClient
Aria2Option
```

as domain-level concepts.

Instead:

```text
Job
Artifact
Source
File
Peer
Tracker
Server
Capability
BackendOption
```

aria2 adapters map those concepts into the backend.

---

## AP-003 — Acquisition is independent of execution

All inputs converge through the acquisition pipeline.

Supported acquisition sources:

```text
manual URL
clipboard
browser extension
drag/drop
torrent file
magnet URI
Metalink file
local file
CLI
future integrations
```

All produce:

```text
AcquisitionRequest
```

---

## AP-004 — Detection, inspection, resolution and execution are separate

The pipeline is:

```text
Acquisition
    ↓
Detection
    ↓
Inspection
    ↓
Resolution
    ↓
Policy
    ↓
Backend Selection
    ↓
Job Creation
    ↓
Execution
    ↓
Artifact
```

These stages MUST NOT be collapsed into one giant `download_url()` operation.

---

## AP-005 — User intent overrides automation

Backend selection precedence:

```text
1. Explicit user backend choice
2. Explicit user workflow
3. Saved acquisition rule
4. Backend recommendation
5. Capability-based automatic routing
6. Application default
```

---

## AP-006 — Capability-driven UI

Frontends MUST query backend capabilities.

Forbidden:

```python
if backend == "aria2":
    show_peers()
```

Preferred:

```python
if capabilities.peers:
    show_peers()
```

---

## AP-007 — Frontends are independent

Three first-class interfaces:

```text
ttkbootstrap Desktop
Textual TUI / Diagnostics
CLI
```

No frontend may call a backend implementation directly.

Correct:

```text
Frontend
  ↓
Application
  ↓
Backend Contract
  ↓
Backend Adapter
```

Forbidden:

```text
ttkbootstrap → aria2 RPC
Textual → aria2 RPC
CLI → yt-dlp subprocess
```

---

## AP-008 — Events are first-class

Core operations MUST emit typed events.

Examples:

```text
AcquisitionDetected
ResolutionStarted
ResolutionCompleted
JobCreated
JobStarted
JobProgressChanged
JobPaused
JobResumed
JobFailed
JobCompleted
JobCancelled
BackendConnected
BackendDisconnected
PluginLoaded
PluginFailed
SchedulerTriggered
```

Frontends consume application state/events rather than polling concrete backends unnecessarily.

---

## AP-009 — Artifact is the execution output

A job may produce:

```text
file
directory
playlist
media collection
torrent payload
generated/post-processed output
```

The generic result is:

```text
Artifact
```

---

## AP-010 — Job groups are first-class

Support:

```text
Job
JobGroup
Batch
Playlist
Collection
```

A playlist resolved by yt-dlp MUST NOT be forced into the semantic model of a single file download.

---

## AP-011 — Secrets never belong in ordinary domain objects

Credentials are represented by references:

```text
CredentialReference
```

and resolved through a credential store.

Plugins MUST receive only the secrets required for their operation.

---

## AP-012 — Plugins are versioned contracts

The plugin platform MUST define:

```text
identity
version
compatibility
capabilities
configuration
lifecycle
execution
events
diagnostics
security/trust
```

---

## AP-013 — Fake implementations validate the architecture

Before completing aria2 integration, the system MUST have:

```text
FakeBackend
FakeAcquisitionProvider
FakeResolver
```

These are mandatory architecture tests.

---

## AP-014 — 132 screens are feature coverage

The 132-screen catalogue represents the initial aria2 desktop feature-completeness baseline.

It MUST NOT dictate permanent navigation.

A catalogue item may become:

```text
screen
tab
panel
drawer
dialog
wizard
inspector
overlay
contextual view
```

provided the underlying feature and states remain covered.

---

# 4. Target Architecture

```text
                              SHUSHA
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
         ACQUISITION        ORCHESTRATION        OUTPUT
              │                  │                  │
     ┌────────┼─────────┐        │              Artifact
     │        │         │        │
 Clipboard Browser   Drag/Drop   Jobs
 Capture   Bridge                │
     │        │                  │
     └────────┴───────┐          │
                      ▼          ▼
                Acquisition   Policy
                   Request    Engine
                      │          │
                      └────┬─────┘
                           ▼
                       Resolver
                           │
                           ▼
                    Backend Selection
                           │
              ┌────────────┼────────────┐
              │            │            │
            aria2        yt-dlp      Plugins
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                          Job
                           │
                           ▼
                      Event System
                           │
             ┌─────────────┼─────────────┐
             │             │             │
          Desktop        Textual        CLI
        ttkbootstrap    TUI/Diag
```

---

# 5. Dependency Architecture

```text
                     ┌─────────────────┐
                     │      CORE       │
                     │ Domain + Events │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │   APPLICATION   │
                     │ Commands/Query  │
                     │ Services/Rules  │
                     └────────┬────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
       ┌─────▼─────┐    ┌─────▼─────┐    ┌────▼────┐
       │ Acquisition│    │ Backend   │    │ Persist │
       │ Platform   │    │ Contracts │    │ence     │
       └─────┬──────┘    └─────┬─────┘    └─────────┘
             │                 │
       ┌─────┼──────┐    ┌─────┼─────────┐
       │     │      │    │     │         │
    Clip  Browser  Drop aria2 yt-dlp  Plugins
       │     │      │
       └─────┴──────┘
             │
             ▼
       Application Layer
             │
       ┌─────┼─────────┐
       │     │         │
   Desktop Textual    CLI
```

### Dependency rules

```text
core → depends on nothing application-specific

application → core

infrastructure → core/application contracts

backend adapters → core/application/backend contracts

acquisition adapters → core/application

desktop → application contracts

textual → application contracts

cli → application contracts

browser extension → acquisition gateway only

plugins → plugin SDK/contracts

core NEVER → frontend
core NEVER → concrete backend
frontend NEVER → concrete backend
backend NEVER → frontend
```

---

# 6. Target Directory Tree

```text
.
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── aria2/
│   ├── backends/
│   ├── plugins/
│   ├── acquisition/
│   ├── browser/
│   ├── desktop/
│   ├── textual/
│   ├── cli/
│   ├── security/
│   ├── operations/
│   └── adr/
│
├── extensions/
│   ├── browser/
│   │   ├── chromium/
│   │   └── firefox/
│   └── native-host/
│
├── src/
│   └── shusha/
│       ├── __main__.py
│       ├── version.py
│       │
│       ├── core/
│       │   ├── domain/
│       │   │   ├── jobs/
│       │   │   ├── artifacts/
│       │   │   ├── sources/
│       │   │   ├── files/
│       │   │   ├── queues/
│       │   │   ├── schedules/
│       │   │   ├── capabilities/
│       │   │   ├── credentials/
│       │   │   └── errors/
│       │   │
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   ├── queries/
│       │   │   ├── services/
│       │   │   ├── policies/
│       │   │   └── workflows/
│       │   │
│       │   ├── events/
│       │   └── contracts/
│       │
│       ├── acquisition/
│       │   ├── detection/
│       │   ├── inspection/
│       │   ├── resolution/
│       │   ├── policies/
│       │   ├── clipboard/
│       │   ├── browser/
│       │   ├── dragdrop/
│       │   └── inbox/
│       │
│       ├── backends/
│       │   ├── contracts/
│       │   ├── registry/
│       │   ├── discovery/
│       │   ├── aria2/
│       │   └── yt_dlp/
│       │
│       ├── plugins/
│       │   ├── api/
│       │   ├── manifest/
│       │   ├── discovery/
│       │   ├── registry/
│       │   └── security/
│       │
│       ├── infrastructure/
│       │   ├── persistence/
│       │   ├── filesystem/
│       │   ├── process/
│       │   ├── networking/
│       │   ├── credentials/
│       │   ├── logging/
│       │   └── platform/
│       │
│       └── frontends/
│           ├── desktop/
│           │   └── ttkbootstrap/
│           │       ├── app.py
│           │       ├── router.py
│           │       ├── state/
│           │       ├── theme/
│           │       ├── design/
│           │       ├── widgets/
│           │       ├── components/
│           │       ├── layouts/
│           │       ├── dialogs/
│           │       └── screens/
│           │
│           ├── textual/
│           │   ├── app.py
│           │   ├── screens/
│           │   ├── widgets/
│           │   ├── diagnostics/
│           │   └── styles/
│           │
│           └── cli/
│               ├── app.py
│               ├── commands/
│               ├── formatters/
│               └── output/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── architecture/
│   ├── frontend/
│   ├── acquisition/
│   ├── backends/
│   ├── plugins/
│   ├── e2e/
│   └── fixtures/
│
├── PLAN.md
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml
└── uv.lock
```

---

# 7. Core Domain Contract

## Job

```text
Job
├── id
├── group_id
├── backend_id
├── source
├── request
├── state
├── progress
├── timestamps
├── outputs
├── capabilities
├── metadata
└── backend_data
```

Backend-specific state MUST remain namespaced.

---

## AcquisitionRequest

```text
AcquisitionRequest
├── id
├── source_kind
├── raw_input
├── detected_kind
├── metadata
├── preferred_backend
├── selection_policy
├── created_at
└── provenance
```

---

## Capability

Capabilities MUST be typed and machine-readable.

Minimum capability vocabulary:

```text
basic_download
pause_resume
cancel
retry
queue
scheduling
multiple_sources
segmentation
http
https
ftp
sftp
torrent
magnet
metalink
torrent_files
torrent_peers
torrent_trackers
server_status
piece_status
checksum
cookies
authentication
proxy
rate_limit
file_selection
input_file
session_save
remote_rpc
media_extraction
format_selection
playlist
subtitles
metadata
post_processing
```

---

# 8. Acquisition Architecture

## Sources

```text
manual
clipboard
browser
drag_drop
cli
torrent_file
magnet
metalink
local_file
api
```

## Pipeline

```text
Acquisition Source
       ↓
AcquisitionDetected
       ↓
Detector
       ↓
Inspector
       ↓
Resolver
       ↓
Policy Engine
       ↓
Backend Recommendation
       ↓
User/Rule Selection
       ↓
JobRequest
```

## Acquisition Inbox

The desktop MUST expose a persistent/ephemeral acquisition inbox.

States:

```text
detected
inspecting
resolved
awaiting_user
accepted
ignored
expired
failed
```

---

# 9. Clipboard Contract

Clipboard capture MUST support:

```text
single URL
multiple URLs
text containing URLs
magnet URI
torrent URL
media URL
```

Features:

```text
enable/disable
source filtering
duplicate suppression
notification policy
automatic enqueue
automatic start
ignore rules
privacy mode
```

Clipboard monitoring MUST never silently upload clipboard contents.

---

# 10. Browser Integration Contract

Browser extension is an acquisition client.

Supported operations:

```text
send URL
send page
send selected link
send media candidate
send multiple links
context menu
download interception
```

The extension MUST communicate through an authenticated local acquisition gateway/native host.

The extension MUST NOT contain:

```text
aria2 RPC logic
yt-dlp execution logic
download database
scheduler
business rules
```

---

# 11. Media Grabber Contract

Media Grabber is backend-neutral.

```text
MediaGrabber
      ↓
MediaResolver
      ↓
yt-dlp adapter
```

Capabilities:

```text
site detection
title
duration
thumbnail
formats
video streams
audio streams
subtitles
chapters
playlist
metadata
post-processing
```

Required workflow:

```text
Inspect
 ↓
Show metadata
 ↓
Show formats
 ↓
User selection
 ↓
Create Job
```

---

# 12. aria2 Reference Backend Contract

aria2 support MUST cover the official aria2c command/RPC surface rather than only the existing application's current feature subset.

The official manual defines HTTP(S), FTP, SFTP, BitTorrent and Metalink support and multi-source downloading, with integrity validation and extensive options. [SOURCE: aria2c manual]

## Protocol coverage

```text
HTTP
HTTPS
FTP
SFTP
BitTorrent
BitTorrent Magnet
Metalink
```

## Transfer features

```text
segmentation
multiple connections
multiple mirrors
URI selection
resume
retry
timeouts
speed limits
connection limits
server statistics
piece selection
file allocation
integrity checking
checksum validation
remote timestamp
```

## BitTorrent

```text
torrent files
magnet links
DHT
DHT IPv4
DHT IPv6
PEX
peer limits
peer exchange
seed ratio
seed time
tracker configuration
tracker discovery
listen ports
local peer discovery
piece selection
torrent metadata
torrent file selection
```

## Metalink

```text
Metalink v3/v4
mirrors
preferred protocol
language
location
OS
version
checksums
piece checksums
file selection
URI selection
```

## HTTP/HTTPS

```text
headers
cookies
referer
user agent
authentication
proxy
HTTPS certificate configuration
server authentication
redirects
compression
keep-alive
pipelining where supported
conditional/request behavior
```

## FTP

```text
FTP authentication
anonymous FTP
active/passive configuration
proxy
directory behavior
resume
timestamp
```

## SFTP

```text
SSH host verification
known-host style validation
public-key authentication
password authentication
key files
host key checksums
```

## File/output

```text
output directory
output filename
file allocation
preallocation
falloc
truncation
existing-file behavior
overwrite
auto-renaming
control files
resume
disk allocation limits
```

## Queue/session

```text
input file
deferred input
save session
load session
queue ordering
concurrency
pause
resume
remove
force save
```

## RPC

Support both aria2 JSON-RPC and XML-RPC semantics exposed by the backend.

Required operation families:

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
tellStatus
getUris
getFiles
getPeers
getServers
tellActive
tellWaiting
tellStopped
changePosition
changeUri
changeOption
changeGlobalOption
getOption
getGlobalOption
getVersion
getSessionInfo
shutdown
forceShutdown
getGlobalStat
purgeDownloadResult
saveSession
```

The RPC implementation MUST be tested against the official method/parameter semantics.

## Dynamic options

Every supported aria2 option MUST have metadata:

```text
name
short_name
type
default
allowed_values
scope
mutable
protocols
description
security_class
```

Options MUST be categorized in the UI.

The system MUST NOT hard-code a partial handwritten option list and claim complete coverage.

The option catalogue MUST be generated/validated against the reference manual and/or aria2 runtime capabilities.

---

# 13. aria2 Option Coverage Matrix

The rewrite MUST maintain:

```text
docs/aria2/option-matrix.md
```

Each option:

```text
aria2 option
short form
domain category
typed representation
default
frontend exposure
runtime mutability
RPC support
backend adapter mapping
tests
documentation
```

Coverage states:

```text
SUPPORTED
SUPPORTED_WITH_LIMITATION
READ_ONLY
BACKEND_ONLY
UNSUPPORTED_WITH_REASON
DEPRECATED
```

No option may silently disappear.

---

# 14. Frontend Contract

## Desktop

Technology:

```text
ttkbootstrap
Tkinter
```

Desktop owns:

```text
complete aria2 baseline
full configuration
visual job management
advanced inspectors
acquisition workflows
media workflows
settings
diagnostics
```

---

## Textual

Textual owns:

```text
operator workflows
SSH/headless workflows
diagnostics
live monitoring
backend inspection
logs/events
doctor
advanced administration
```

Textual does not need 132-screen parity.

---

## CLI

The CLI owns:

```text
automation
scripting
CI
cron
shell integration
administration
machine output
```

Required output modes:

```text
table
json
jsonl
```

---

# 15. Desktop Design System

Required system:

```text
Application shell
navigation
toolbar
status bar
command palette
dialogs
drawers
inspectors
tables
trees
cards
charts
forms
property grids
notifications
empty states
loading states
error states
offline states
confirmation states
```

Responsive classes:

```text
Compact
Standard
Wide
UltraWide
```

The layout system MUST define deterministic behavior for each class.

---

# 16. 132-Screen Baseline

The desktop implementation MUST map the existing 132-screen catalogue to:

```text
screen ID
feature
route
component
state model
required capabilities
backend dependencies
acceptance test
responsive behavior
accessibility behavior
```

Each catalogue entry MUST have:

```text
default state
loading
empty
error
offline
disabled
permission/security
busy
success
```

where applicable.

---

# 17. Plugin Contract

Plugin manifest:

```text
id
name
version
api_version
description
author
license
backend_type
capabilities
entrypoint
configuration_schema
permissions
```

Plugin lifecycle:

```text
discover
validate
load
initialize
start
stop
unload
```

Plugins MUST declare permissions.

Examples:

```text
network
filesystem
process
credentials
browser
clipboard
```

Third-party plugins MUST NOT receive unrestricted application privileges.

---

# 18. Persistence

Persistence MUST support:

```text
jobs
job groups
artifacts
history
queue state
schedules
settings
backend configuration
acquisition rules
plugin configuration
diagnostic records where appropriate
```

The persistence abstraction MUST allow migration between storage implementations.

Do not expose SQLite/shelve/etc. directly to domain objects.

---

# 19. Daemon/Service Mode

Target commands:

```text
shusha
shusha desktop
shusha tui
shusha daemon
shusha add
shusha list
shusha status
shusha pause
shusha resume
shusha remove
shusha resolve
shusha doctor
shusha diagnostics
```

The first implementation may run application services in-process.

The architecture MUST leave a clean boundary for a long-running service.

---

# 20. Security

Security architecture MUST cover:

```text
plugin trust
credential storage
browser bridge authentication
local service authentication
filesystem boundaries
command execution
URL validation
SSRF-sensitive workflows
cookie handling
proxy credentials
TLS certificate validation
aria2 RPC secret handling
logs containing secrets
temporary files
```

Never log:

```text
passwords
API tokens
cookies
authorization headers
private keys
credential material
```

---

# 21. Observability

Standardize:

```text
structured logs
correlation IDs
job IDs
backend IDs
plugin IDs
event IDs
health checks
diagnostics
timing
error categories
```

Required diagnostic commands:

```text
shusha doctor
shusha diagnostics
```

---

# 22. Python 3.14 / Astral Toolchain

Required baseline:

```text
Python >= 3.14
uv
ruff
ty
pytest
coverage
```

Quality commands:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest --cov=shusha
uv build
```

Typing policy:

```text
strict
no Any unless justified
no untyped public APIs
Protocols for contracts
Typed models for domain data
```

---

# 23. Epic Dependency Graph

```text
E00 Repository Audit
 │
 ├── E01 Toolchain/Foundation
 │
 ├── E02 Domain/Core
 │      │
 │      ├── E03 Events/Application
 │      │
 │      ├── E04 Persistence
 │      │
 │      └── E05 Backend SDK
 │             │
 │             ├── E06 Fake Backend
 │             │
 │             ├── E07 aria2
 │             │
 │             └── E08 yt-dlp
 │
 ├── E09 Acquisition
 │      ├── Clipboard
 │      ├── Drag/Drop
 │      ├── Resolution
 │      └── Policy
 │
 │      └── E10 Browser
 │
 ├── E11 Desktop
 │      └── 132-screen baseline
 │
 ├── E12 Textual
 │
 ├── E13 CLI
 │
 ├── E14 Plugins
 │
 ├── E15 Security
 │
 ├── E16 Testing/QA
 │
 ├── E17 Documentation
 │
 └── E18 Release/Packaging
```

Critical path:

```text
E00
 ↓
E01
 ↓
E02
 ↓
E03
 ↓
E05
 ↓
E06
 ↓
E07
 ↓
E11
```

Parallel paths after core contracts:

```text
E07 aria2
E08 yt-dlp
E09 acquisition
E12 Textual
E13 CLI
E14 plugins
E15 security
```

---

# 24. AI-Agent Ticket Contract

Every ticket below is executable.

An agent MUST:

1. inspect existing code before editing;
2. identify impacted modules;
3. implement the smallest coherent change;
4. add/update tests;
5. run relevant checks;
6. update documentation;
7. report files changed;
8. report tests run;
9. report unresolved issues;
10. never silently weaken typing or acceptance criteria.

A ticket is complete only when all acceptance criteria pass.

---

# 25. Epic E00 — Repository Audit

## E00-I01 — Inventory Repository

**Depends:** none

**Task**

Inventory source, tests, docs, resources, workflows, packaging and archive material.

**Acceptance**

- complete tree recorded;
- existing modules mapped;
- legacy/archive code identified;
- entry points identified;
- dependencies identified;
- test suite identified;
- migration risks documented.

---

## E00-I02 — Map Existing Features

**Depends:** E00-I01

**Task**

Map existing functionality to the new architecture.

**Acceptance**

Every existing feature is marked:

```text
retain
rewrite
replace
deprecate
remove
```

No existing user-visible capability is unclassified.

---

## E00-I03 — aria2 Gap Matrix

**Depends:** E00-I01

**Task**

Compare current implementation against official aria2c documentation.

**Acceptance**

- all option families catalogued;
- RPC methods catalogued;
- protocol coverage catalogued;
- gaps classified;
- tests required for each gap;
- `docs/aria2/option-matrix.md` created.

---

# 26. Epic E01 — Foundation

## E01-I01 — Python 3.14 Baseline

**Depends:** E00

**Acceptance**

- pyproject requires Python 3.14+;
- obsolete compatibility code removed;
- CI tests Python 3.14;
- package builds.

## E01-I02 — uv Toolchain

**Depends:** E01-I01

**Acceptance**

- uv lockfile valid;
- reproducible `uv sync`;
- development commands documented.

## E01-I03 — Ruff and ty

**Depends:** E01-I01

**Acceptance**

- Ruff configured;
- ty configured;
- CI fails on violations;
- public APIs typed.

## E01-I04 — Test Infrastructure

**Depends:** E01-I01

**Acceptance**

- unit/integration/contract/e2e layout;
- fixtures;
- coverage;
- deterministic test commands.

---

# 27. Epic E02 — Domain Core

## E02-I01 — Job Model

**Depends:** E01

**Acceptance**

Typed Job model supports lifecycle, backend, source, progress and outputs.

## E02-I02 — Artifact Model

**Depends:** E02-I01

**Acceptance**

Files, directories and collections can be represented without backend-specific types.

## E02-I03 — JobGroup Model

**Depends:** E02-I01

**Acceptance**

Batch/playlist/group jobs supported.

## E02-I04 — AcquisitionRequest

**Depends:** E01

**Acceptance**

All acquisition sources map to a typed request.

## E02-I05 — Capability Model

**Depends:** E01

**Acceptance**

Capabilities are typed, serializable and queryable.

## E02-I06 — CredentialReference

**Depends:** E01

**Acceptance**

Domain objects contain references rather than secrets.

---

# 28. Epic E03 — Application and Events

## E03-I01 — Command Bus

**Depends:** E02

**Acceptance**

Frontend-independent commands execute application operations.

## E03-I02 — Query Layer

**Depends:** E02

**Acceptance**

Frontends can retrieve jobs, status, capabilities and diagnostics without backend coupling.

## E03-I03 — Event Bus

**Depends:** E02

**Acceptance**

Typed events can be emitted/subscribed to and tested.

## E03-I04 — Job Lifecycle Service

**Depends:** E03-I01, E03-I03

**Acceptance**

Create/start/pause/resume/cancel/remove/retry workflows are backend-neutral.

---

# 29. Epic E04 — Persistence

## E04-I01 — Persistence Contracts

**Depends:** E02

**Acceptance**

Repositories/interfaces exist for jobs, artifacts, history, settings and schedules.

## E04-I02 — Initial Storage

**Depends:** E04-I01

**Acceptance**

Initial storage implementation supports restart recovery.

## E04-I03 — Migrations

**Depends:** E04-I02

**Acceptance**

Schema versioning and migration tests exist.

---

# 30. Epic E05 — Backend SDK

## E05-I01 — Backend Protocol

**Depends:** E02

**Acceptance**

Backend contract supports discovery, lifecycle, capabilities, job execution and events.

## E05-I02 — Backend Registry

**Depends:** E05-I01

**Acceptance**

Backends can be registered, discovered and selected.

## E05-I03 — Backend Error Model

**Depends:** E05-I01

**Acceptance**

Backend errors map into stable application errors.

## E05-I04 — Backend Option Model

**Depends:** E05-I01

**Acceptance**

Backend-specific options have typed metadata.

---

# 31. Epic E06 — Fake Backend

## E06-I01 — FakeBackend

**Depends:** E05

**Acceptance**

Fake backend simulates:

```text
queued
active
paused
failed
completed
cancelled
progress
speed
ETA
files
events
capabilities
```

## E06-I02 — Contract Test Suite

**Depends:** E06-I01

**Acceptance**

Every backend implementation must pass the common contract suite.

---

# 32. Epic E07 — aria2 Backend

## E07-I01 — RPC Transport

**Depends:** E05, E06

**Acceptance**

JSON-RPC transport implemented with typed request/response handling, timeouts, retries and structured errors.

## E07-I02 — XML-RPC Compatibility

**Depends:** E07-I01

**Acceptance**

Required XML-RPC operations supported/tested.

## E07-I03 — Session/Daemon Lifecycle

**Depends:** E07-I01

**Acceptance**

Local aria2 process can be discovered, started, monitored and stopped safely.

## E07-I04 — Download Lifecycle

**Depends:** E07-I01

**Acceptance**

Add/pause/resume/cancel/remove/retry operations work.

## E07-I05 — Status/Files/Peers/Servers

**Depends:** E07-I04

**Acceptance**

Status, files, peers and servers are represented through backend-neutral models.

## E07-I06 — Global Statistics

**Depends:** E07-I04

**Acceptance**

Global statistics are exposed through application queries.

## E07-I07 — Option Catalogue

**Depends:** E07-I04

**Acceptance**

Full documented option catalogue generated/validated and exposed through typed metadata.

## E07-I08 — Protocol Features

**Depends:** E07-I04

**Acceptance**

HTTP(S), FTP, SFTP, BitTorrent, Magnet and Metalink are covered.

## E07-I09 — Integrity/Checksums

**Depends:** E07-I08

**Acceptance**

Checksum/integrity features are represented and tested.

## E07-I10 — Input/Session Files

**Depends:** E07-I04

**Acceptance**

Input-file and session semantics are documented and implemented where supported.

## E07-I11 — RPC Complete Surface

**Depends:** E07-I01

**Acceptance**

RPC method matrix covers all required aria2 RPC methods and identifies intentionally unsupported methods with reasons.

---

# 33. Epic E08 — yt-dlp Backend

## E08-I01 — Process Adapter

**Depends:** E05, E06

**Acceptance**

yt-dlp is executed through a safe typed adapter.

## E08-I02 — Media Inspection

**Depends:** E08-I01

**Acceptance**

Metadata and format information can be queried without starting a download.

## E08-I03 — Format Selection

**Depends:** E08-I02

**Acceptance**

Video/audio format selection maps into a typed job request.

## E08-I04 — Playlist/Collection

**Depends:** E08-I02, E02-I03

**Acceptance**

Playlists produce job groups.

## E08-I05 — Subtitles/Metadata/Post-processing

**Depends:** E08-I03

**Acceptance**

Supported yt-dlp workflows are represented without contaminating core domain models.

---

# 34. Epic E09 — Acquisition Platform

## E09-I01 — Detector

**Depends:** E02

**Acceptance**

Detects URL, magnet, torrent, Metalink and media candidates.

## E09-I02 — Inspector

**Depends:** E09-I01

**Acceptance**

Inspects source without executing an irreversible download.

## E09-I03 — Resolver

**Depends:** E09-I02, E05

**Acceptance**

Selects compatible backend candidates.

## E09-I04 — Policy Engine

**Depends:** E09-I03

**Acceptance**

Supports source/type/domain/backend rules and precedence.

## E09-I05 — Acquisition Inbox

**Depends:** E09-I04, E03

**Acceptance**

Detected items can be accepted, ignored, retried or expired.

## E09-I06 — Clipboard Capture

**Depends:** E09-I01, E09-I05

**Acceptance**

Clipboard capture supports URLs, magnets, multi-URL text, deduplication and configurable action policy.

## E09-I07 — Drag and Drop

**Depends:** E09-I01

**Acceptance**

Desktop can accept URLs, text, torrent files, Metalinks and supported local inputs.

---

# 35. Epic E10 — Browser Integration

## E10-I01 — Acquisition Gateway

**Depends:** E09, E15

**Acceptance**

Authenticated local browser acquisition endpoint exists.

## E10-I02 — Chromium Extension

**Depends:** E10-I01

**Acceptance**

Context menu and send-to-Shusha workflows work.

## E10-I03 — Firefox Extension

**Depends:** E10-I01

**Acceptance**

Equivalent acquisition workflows work.

## E10-I04 — Media Candidate Transfer

**Depends:** E08, E10-I01

**Acceptance**

Browser can send detected media/page candidates for inspection.

## E10-I05 — Browser Security

**Depends:** E10-I01

**Acceptance**

Unauthorized origins/requests are rejected and security behavior is documented.

---

# 36. Epic E11 — ttkbootstrap Desktop

## E11-I01 — Application Shell

**Depends:** E03

**Acceptance**

Shell includes navigation, toolbar, content region, status region and notifications.

## E11-I02 — Design System

**Depends:** E11-I01

**Acceptance**

Typography, spacing, states, controls, tables, dialogs and theme tokens are standardized.

## E11-I03 — Responsive Layout Engine

**Depends:** E11-I01

**Acceptance**

Compact/Standard/Wide/UltraWide behavior is deterministic.

## E11-I04 — Dashboard

**Depends:** E03, E07

**Acceptance**

Dashboard displays backend-neutral jobs/statistics/events.

## E11-I05 — Download Workspace

**Depends:** E11-I04

**Acceptance**

Queue, filtering, sorting, bulk actions, context actions and inspectors work.

## E11-I06 — Add Download Workflow

**Depends:** E09, E07

**Acceptance**

URL/torrent/magnet/Metalink workflows are available.

## E11-I07 — Acquisition Inbox UI

**Depends:** E09-I05

**Acceptance**

Users can inspect and accept acquisition candidates.

## E11-I08 — Media Grabber UI

**Depends:** E08-I02, E08-I03

**Acceptance**

Media metadata and format selection workflow works.

## E11-I09 — aria2 Advanced Inspectors

**Depends:** E07-I05

**Acceptance**

Files, peers, trackers, servers, pieces, options and statistics are covered.

## E11-I10 — Settings

**Depends:** E07-I07, E04

**Acceptance**

Backend, application, acquisition, browser, appearance, storage and security settings are represented.

## E11-I11 — 132-Screen Baseline

**Depends:** E11-I01 through E11-I10

**Acceptance**

Every catalogue feature is implemented or explicitly mapped to a replacement UI with equivalent functionality.

---

# 37. Epic E12 — Textual

## E12-I01 — TUI Shell

**Depends:** E03

**Acceptance**

Textual application starts and displays backend-neutral state.

## E12-I02 — Live Job Monitor

**Depends:** E03

**Acceptance**

Jobs update without full-screen refresh artifacts.

## E12-I03 — Acquisition Monitor

**Depends:** E09

**Acceptance**

Acquisition events and inbox are visible.

## E12-I04 — Diagnostics

**Depends:** E03

**Acceptance**

Backend/plugin/system diagnostics are inspectable.

## E12-I05 — Doctor

**Depends:** E15

**Acceptance**

`shusha doctor`/TUI doctor identifies actionable environment problems.

## E12-I06 — Headless Administration

**Depends:** E12-I02

**Acceptance**

Pause/resume/remove/retry and configuration inspection work over terminal workflows.

---

# 38. Epic E13 — CLI

## E13-I01 — CLI Framework

**Depends:** E03

**Acceptance**

CLI dispatches application commands, not backend calls.

## E13-I02 — Job Commands

**Depends:** E13-I01

**Acceptance**

Implement:

```text
add
list
status
pause
resume
cancel
remove
retry
```

## E13-I03 — Resolution

**Depends:** E09

**Acceptance**

`shusha resolve URL` performs inspection without execution.

## E13-I04 — JSON/JSONL Output

**Depends:** E13-I02

**Acceptance**

Machine-readable output is stable and documented.

## E13-I05 — Diagnostics

**Depends:** E12-I05

**Acceptance**

`doctor` and diagnostics work without Desktop.

---

# 39. Epic E14 — Plugin Platform

## E14-I01 — Manifest

**Depends:** E05

**Acceptance**

Manifest schema versioned and validated.

## E14-I02 — Discovery

**Depends:** E14-I01

**Acceptance**

Installed plugins are discovered deterministically.

## E14-I03 — Lifecycle

**Depends:** E14-I02

**Acceptance**

Plugin lifecycle and failures are isolated.

## E14-I04 — Permissions

**Depends:** E15

**Acceptance**

Plugins declare and receive only required permissions.

## E14-I05 — SDK

**Depends:** E14-I01 through E14-I04

**Acceptance**

Plugin development kit includes contracts, fixtures, fake backend and documentation.

---

# 40. Epic E15 — Security

## E15-I01 — Credential Store

**Depends:** E02

**Acceptance**

Secrets are stored through a dedicated abstraction.

## E15-I02 — Plugin Trust

**Depends:** E14-I01

**Acceptance**

Trust levels and permission enforcement exist.

## E15-I03 — Browser Authentication

**Depends:** E10-I01

**Acceptance**

Browser gateway rejects unauthorized requests.

## E15-I04 — Process Execution

**Depends:** E05

**Acceptance**

Backend subprocess execution avoids unsafe shell interpolation.

## E15-I05 — Secret Redaction

**Depends:** E15-I01

**Acceptance**

Credentials cannot appear in logs/errors/diagnostic dumps.

## E15-I06 — Security Documentation

**Depends:** E15-I01 through E15-I05

**Acceptance**

Threat model and security guidance are published.

---

# 41. Epic E16 — QA

## E16-I01 — Architecture Tests

**Depends:** E02-E05

**Acceptance**

Automated tests fail if forbidden dependency directions appear.

## E16-I02 — Backend Contract Tests

**Depends:** E06

**Acceptance**

Fake backend, aria2 and yt-dlp satisfy shared contracts where applicable.

## E16-I03 — Acquisition Tests

**Depends:** E09

**Acceptance**

Detection, resolution, policy and deduplication have deterministic tests.

## E16-I04 — Frontend Tests

**Depends:** E11-E13

**Acceptance**

Critical workflows have UI/TUI/CLI tests.

## E16-I05 — End-to-End Tests

**Depends:** E07, E08, E09, E11

**Acceptance**

Representative real backend workflows succeed.

## E16-I06 — Compatibility Matrix

**Depends:** E16-I05

**Acceptance**

Supported OS/runtime/backend combinations are documented and tested.

---

# 42. Epic E17 — Documentation

## E17-I01 — README Rewrite

**Depends:** architecture stabilization

**Acceptance**

README explains Shusha as a multi-backend platform.

## E17-I02 — Architecture Documentation

**Depends:** E02-E05

**Acceptance**

Architecture diagrams, dependency rules and ADRs published.

## E17-I03 — aria2 Documentation

**Depends:** E07

**Acceptance**

Complete option/RPC/protocol coverage documented.

## E17-I04 — Plugin Documentation

**Depends:** E14

**Acceptance**

Plugin SDK documentation includes examples and compatibility rules.

## E17-I05 — Acquisition Documentation

**Depends:** E09-E10

**Acceptance**

Clipboard/browser/media workflows documented.

## E17-I06 — Frontend Documentation

**Depends:** E11-E13

**Acceptance**

Desktop, Textual and CLI architecture documented.

## E17-I07 — Operations Guide

**Depends:** E12-E15

**Acceptance**

Daemon, diagnostics, logs, recovery and security operations documented.

## E17-I08 — Migration Guide

**Depends:** E17-I01

**Acceptance**

Existing Shusha users/developers can understand migration from the old architecture.

---

# 43. Epic E18 — Packaging and Release

## E18-I01 — Package Metadata

**Depends:** E01

**Acceptance**

Correct Python package metadata and entry points.

## E18-I02 — Desktop Packaging

**Depends:** E11

**Acceptance**

Desktop distribution strategy documented/tested.

## E18-I03 — CLI/TUI Packaging

**Depends:** E12, E13

**Acceptance**

CLI/TUI install and invocation documented.

## E18-I04 — CI/CD

**Depends:** E16

**Acceptance**

CI runs lint, format, typing, tests, build and package checks.

## E18-I05 — Release Checklist

**Depends:** E17, E18-I04

**Acceptance**

Release checklist is reproducible and documented.

---

# 44. Definition of Done

A ticket is DONE only if:

- implementation exists;
- types pass;
- tests exist;
- relevant tests pass;
- architecture rules pass;
- docs are updated;
- no unexplained TODO remains;
- no unrelated refactor is introduced;
- error handling is explicit;
- logging is safe;
- public behavior is documented;
- acceptance criteria are satisfied.

---

# 45. Definition of Release Readiness

The rewrite is not release-ready until:

```text
[ ] Python 3.14+
[ ] uv lock reproducible
[ ] Ruff clean
[ ] ty clean
[ ] tests green
[ ] architecture tests green
[ ] fake backend green
[ ] aria2 backend contract green
[ ] aria2 protocol coverage validated
[ ] aria2 RPC matrix complete
[ ] aria2 option matrix complete
[ ] yt-dlp backend functional
[ ] acquisition pipeline functional
[ ] clipboard capture functional
[ ] browser bridge secured
[ ] media grabber functional
[ ] Desktop baseline complete
[ ] Textual diagnostics functional
[ ] CLI functional
[ ] plugin SDK documented
[ ] persistence/recovery tested
[ ] security review complete
[ ] documentation complete
[ ] packaging tested
```

---

# 46. Architectural Non-Goals

Do NOT:

- create separate business logic for each frontend;
- turn core into an aria2 abstraction dump;
- make every backend expose every feature;
- force yt-dlp into an aria2-shaped model;
- reproduce the Desktop UI in Textual;
- make browser extensions execute downloads;
- expose secrets to plugins unnecessarily;
- silently discard unsupported aria2 options;
- treat the 132-screen catalogue as a rigid navigation tree;
- introduce a network service before an actual requirement exists;
- add speculative abstractions without a consumer.

---

# 47. Implementation Order

Recommended order:

```text
Phase 0  Repository audit
Phase 1  Toolchain + architectural skeleton
Phase 2  Core domain
Phase 3  Application commands/queries/events
Phase 4  Persistence
Phase 5  Backend contracts + fake backend
Phase 6  aria2 backend
Phase 7  Acquisition platform
Phase 8  yt-dlp backend
Phase 9  Plugin SDK
Phase 10 Security/browser integration
Phase 11 ttkbootstrap desktop
Phase 12 Textual
Phase 13 CLI
Phase 14 QA/compatibility
Phase 15 Documentation
Phase 16 Packaging/release
```

Parallel work is permitted only when dependency contracts already exist.

---

# 48. Architectural Gate Reviews

The AI agent MUST stop and request review before crossing these gates:

```text
GATE-01 Core contract freeze
GATE-02 Backend contract freeze
GATE-03 Acquisition contract freeze
GATE-04 aria2 compatibility freeze
GATE-05 Plugin security freeze
GATE-06 Desktop navigation freeze
GATE-07 Release candidate freeze
```

No frontend implementation should force changes to core contracts without an ADR.

---

# 49. Required ADRs

Create:

```text
ADR-001 Multi-backend architecture
ADR-002 Acquisition pipeline
ADR-003 Capability model
ADR-004 Job and Artifact model
ADR-005 Event architecture
ADR-006 Persistence strategy
ADR-007 aria2 integration strategy
ADR-008 yt-dlp integration strategy
ADR-009 Plugin security model
ADR-010 Browser bridge architecture
ADR-011 Desktop architecture
ADR-012 Textual architecture
ADR-013 CLI architecture
ADR-014 Daemon/service boundary
ADR-015 Credential storage
ADR-016 132-screen baseline interpretation
```

---

# 50. Final Architectural Contract

The rewrite is successful only if the following statement remains true:

> **Shusha receives work through multiple acquisition mechanisms, resolves that work through typed detection/inspection/policy pipelines, executes it through replaceable backend plugins, persists it through backend-neutral application services, emits typed events, and exposes the same underlying capabilities through ttkbootstrap Desktop, Textual TUI/Diagnostics, and CLI.**

aria2 is the first complete reference backend.

yt-dlp is the first secondary backend.

Clipboard, browser integration, drag/drop, media grabber and future integrations are acquisition mechanisms.

The 132-screen catalogue is the initial aria2 desktop completeness contract.

The architecture MUST remain open for additional backends, acquisition providers, frontends and future remote/service interfaces without rewriting the domain core.