# AGENTS.md

# Shusha AI Coding Agent Instructions

> This file is authoritative for AI coding agents working in this repository.

---

# 1. Mission

You are working on the Shusha rewrite.

Shusha is a desktop download manager using aria2c as its download engine.

The target architecture is:

```text
ttkbootstrap UI
      │
      ▼
presentation
      │
      ▼
application
      │
      ▼
domain
      ▲
      │
infrastructure
      │
      ├── aria2
      ├── daemon
      ├── persistence
      ├── filesystem
      ├── networking
      └── OS integration
```

The project must remain maintainable as aria2's feature surface grows.

---

# 2. Mandatory Technology Choices

## Python

Use:

```text
Python 3.14+
```

Do not add compatibility shims for old Python versions unless explicitly required.

---

## GUI

Use:

```text
Tkinter
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

unless the project owner explicitly changes the architecture.

---

## Toolchain

Use Astral tooling:

```text
uv
ruff
ty
```

Tests:

```text
pytest
pytest-cov
```

Run:

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

# 3. First Rule: Read Before Editing

Before modifying code:

1. Read `PLAN.md`.
2. Read this file.
3. Inspect the relevant source.
4. Inspect relevant tests.
5. Inspect relevant documentation.
6. Determine the architectural boundary.
7. Identify the issue being implemented.
8. Check issue dependencies.
9. Only then edit.

Do not immediately start coding based on a filename or function name.

---

# 4. Never Guess aria2 Behavior

aria2 is an external specification.

When implementing aria2 behavior:

```text
documented behavior > assumption
existing test > assumption
actual protocol response > assumption
```

Never invent:

- options
- RPC methods
- parameter names
- status values
- event names
- defaults
- error codes

If behavior is unclear, stop and report the ambiguity.

---

# 5. Architecture Rules

## 5.1 Domain

`domain/` contains application concepts.

It may contain:

```text
entities
value objects
enums
domain errors
domain events
validation
business rules
```

It must NOT import:

```text
tkinter
ttkbootstrap
aria2 RPC implementation
subprocess
sqlite implementation
platform APIs
```

---

## 5.2 Application

`application/` coordinates use cases.

Examples:

```text
AddDownload
PauseDownload
ResumeDownload
RetryDownload
RemoveDownload
ChangeDownloadOptions
ReorderQueue
ScheduleDownload
InspectDownload
```

Application code may depend on domain abstractions.

Application code must not contain Tkinter widget manipulation.

---

## 5.3 Infrastructure

`infrastructure/` implements external systems.

Examples:

```text
aria2 RPC
aria2 daemon
filesystem
database
networking
notifications
OS integration
```

Infrastructure may translate external representations into domain representations.

---

## 5.4 Presentation

`presentation/` contains the desktop UI.

Views/widgets must not:

```text
call aria2 directly
open database connections
spawn subprocesses
parse JSON-RPC responses
implement business rules
```

Views consume typed state and dispatch application commands.

---

# 6. Dependency Direction

Allowed:

```text
presentation → application
presentation → domain

application → domain

infrastructure → domain
infrastructure → application contracts

platform → infrastructure/shared
```

Forbidden:

```text
domain → presentation
domain → infrastructure

application → tkinter
application → ttkbootstrap

presentation → aria2 RPC

presentation → sqlite
```

If an implementation requires a forbidden dependency, redesign the boundary.

Do not suppress the type checker to make it work.

---

# 7. Python Style

Prefer modern Python.

Use:

```python
str | None
list[str]
dict[str, str]
type DownloadId = str
```

where appropriate.

Prefer:

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
```

over obsolete patterns.

Use explicit return types.

Example:

```python
def calculate_eta(
    completed: int,
    total: int,
    speed: int,
) -> float | None:
    ...
```

---

# 8. `Any` Policy

`Any` is prohibited by default.

Do not use:

```python
dict[str, Any]
```

as a convenient escape hatch for untyped external data.

Instead:

1. Parse the external data.
2. Validate it.
3. Convert it to a typed structure.
4. Pass the typed structure inward.

If `Any` is genuinely unavoidable, document why at the point of use.

---

# 9. External Data Rule

The following are untrusted/untyped boundaries:

```text
aria2 RPC
JSON
WebSocket messages
TOML/config files
database rows
filesystem metadata
environment variables
CLI arguments
URLs
subprocess output
OS APIs
```

Never pass raw external dictionaries throughout the application.

Required pattern:

```text
external data
    ↓
transport/schema parser
    ↓
validated typed object
    ↓
domain/application
```

---

# 10. aria2 RPC Rule

Only:

```text
src/shusha/infrastructure/aria2/
```

may know RPC method names and wire-format details.

Bad:

```python
response["result"][0]["completedLength"]
```

inside application/UI code.

Good:

```python
status = await aria2.tell_status(download_id)
status.completed_length
```

---

# 11. aria2 Option Registry

Every aria2 option must have one authoritative definition.

Required conceptual structure:

```text
OptionDefinition
├── name
├── short_name
├── category
├── type
├── default
├── minimum
├── maximum
├── enum_values
├── scope
├── rpc_supported
├── cli_supported
├── sensitive
├── deprecated
├── experimental
└── documentation_reference
```

Do not duplicate option definitions independently in:

```text
UI
CLI
RPC
validation
documentation
tests
```

Generate or derive these surfaces from the authoritative registry where practical.

---

# 12. UI Rules

The GUI is `ttkbootstrap`.

## Main shell

Maintain consistent:

```text
menu
toolbar
sidebar
content
status bar
notifications
```

---

## Tables

Download tables must support appropriate:

```text
sorting
filtering
search
multi-selection
context menus
keyboard navigation
progress
speed
ETA
status
```

Avoid excessive visual noise.

---

## Dialogs

Dialogs must:

- have clear titles
- have explicit primary/secondary actions
- support Escape where appropriate
- validate before submission
- display actionable errors
- avoid blocking the entire application unnecessarily

---

## States

Every significant UI surface must consider:

```text
loading
empty
error
offline
disabled
busy
permission denied
no selection
partial selection
```

Do not implement only the happy path.

---

# 13. aria2 Option UX

Full aria2 coverage does not mean displaying hundreds of fields simultaneously.

Use progressive disclosure:

```text
Basic
Advanced
Expert
```

Each control must have:

```text
human-readable label
description
validation
aria2 option name
documentation reference
```

---

# 14. Secrets

Never log:

```text
passwords
tokens
RPC secrets
proxy credentials
authentication headers
private URLs containing credentials
```

Sensitive values must be redacted in:

```text
logs
diagnostic bundles
exceptions
screenshots
debug output
configuration previews
```

---

# 15. Subprocess Security

Never construct shell commands from user-controlled strings.

Do not use:

```python
subprocess.run(command, shell=True)
```

for normal application functionality.

Prefer explicit argument arrays:

```python
subprocess.Popen(
    [executable, *arguments],
    ...
)
```

Validate:

```text
executable
arguments
working directory
environment
paths
```

---

# 16. Filesystem Security

Treat all download destinations and filenames as potentially unsafe.

Consider:

```text
path traversal
absolute/relative paths
invalid filenames
reserved filenames
symlinks
permissions
existing files
directory creation
partial downloads
```

Never blindly concatenate paths.

---

# 17. Networking

Network failures are expected behavior.

Handle:

```text
timeout
connection refused
DNS failure
TLS failure
authentication failure
remote disconnect
malformed response
rate limiting
temporary unavailable
```

Do not turn network failures into generic `Exception`.

---

# 18. Error Handling

Use typed exceptions/results where appropriate.

Errors should preserve:

```text
operation
component
error code
human-readable explanation
recoverability
underlying cause
```

The UI should not parse exception strings to determine behavior.

---

# 19. Async / Threading

Tkinter has a single UI thread.

Do not block the UI thread with:

```text
RPC calls
network operations
subprocess waits
large filesystem scans
database operations
long calculations
```

Use a controlled application concurrency strategy.

Do not create arbitrary threads from widgets.

All background work must have:

```text
lifecycle
cancellation behavior
error propagation
UI update mechanism
shutdown behavior
```

---

# 20. State Management

Avoid mutable global state.

Prefer explicit application state and events.

The UI should react to state changes rather than repeatedly querying infrastructure itself.

---

# 21. Persistence

Persistence implementations belong under infrastructure.

Do not embed database logic in:

```text
domain
widgets
application commands
```

Use repository interfaces.

Migrations must be:

```text
versioned
repeatable
tested
safe
```

Never silently destroy existing data.

---

# 22. Testing Requirements

Every new behavior requires tests.

## Unit tests

Use for:

```text
domain
validation
option registry
parsers
application services
state transitions
```

---

## Integration tests

Use for:

```text
aria2 RPC
daemon lifecycle
database
filesystem
networking
```

---

## Presentation tests

Test:

```text
commands
state transitions
important widget behavior
validation
empty/error states
```

Do not chase meaningless line coverage.

---

## E2E

Where practical:

```text
Shusha
    ↓
real aria2c
    ↓
controlled test server
    ↓
download
```

---

# 23. Test Isolation

Tests must not depend on:

```text
developer's home directory
developer's aria2 configuration
developer's credentials
internet availability
existing downloads
global system state
```

Use fixtures and temporary directories.

---

# 24. Mocking Rule

Do not mock everything.

Prefer:

```text
real domain
real application
fake infrastructure
```

for most tests.

Use real aria2 integration tests for protocol compatibility.

---

# 25. Documentation Rule

When behavior changes, update documentation in the same issue.

Potential locations:

```text
README.md
docs/architecture/
docs/aria2/
docs/api/
docs/ui/
docs/development/
```

Do not leave documentation updates as unspecified future work.

---

# 26. Issue Execution Protocol

For every issue:

## Step 1 — Read

Read:

```text
PLAN.md
this file
relevant issue
dependencies
relevant tests
```

## Step 2 — Inspect

Identify:

```text
existing implementation
target implementation
affected tests
affected docs
affected APIs
```

## Step 3 — Plan

Before editing, identify:

```text
files to create
files to modify
files to delete
tests to add
docs to update
```

## Step 4 — Implement

Make the smallest coherent change.

## Step 5 — Test

Run the narrowest relevant tests first.

Then run the full suite.

## Step 6 — Type/lint

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

## Step 7 — Review

Check:

```text
architecture
security
typing
tests
documentation
backwards/migration behavior
```

## Step 8 — Report

Report:

```text
Implemented:
Tests:
Validation:
Files changed:
Known limitations:
Follow-up:
```

---

# 27. Issue Dependencies

Never implement an issue whose dependencies are incomplete unless the dependency is explicitly overridden.

If blocked:

```text
BLOCKED

Issue:
Dependency:
Why blocked:
Evidence:
Required decision:
```

Do not silently bypass dependencies.

---

# 28. Phase 0 Rules

During Phase 0:

**DO:**

- inspect
- document
- measure
- classify
- test
- map
- identify risk

**DO NOT:**

- perform broad rewrites
- delete legacy code
- replace the UI
- change persistence schema
- change public behavior
- silently fix unrelated bugs

Phase 0 establishes facts.

---

# 29. Legacy Code

Legacy code may remain temporarily.

Do not delete it because:

> “The new architecture is cleaner.”

Deletion requires:

```text
feature parity
tests
migration mapping
documentation
explicit disposition
```

---

# 30. Compatibility

The rewrite should preserve user-visible behavior unless the new behavior is intentionally documented.

For changed behavior, document:

```text
old behavior
new behavior
reason
migration impact
```

---

# 31. aria2 Coverage Requirement

The rewrite aims for comprehensive aria2 coverage.

Every supported aria2 feature must eventually have a status:

```text
SUPPORTED
PARTIALLY_SUPPORTED
NOT_APPLICABLE
UNSUPPORTED
DEPRECATED
VERSION_DEPENDENT
```

Never leave a feature as an undocumented omission.

---

# 32. aria2 Feature Categories

The agent must consider at minimum:

```text
Basic
HTTP/HTTPS
FTP/SFTP
BitTorrent
Metalink
File Allocation
Console
RPC
Cookies
Checksum
Hooks
Advanced
Experimental
Deprecated
```

Feature coverage must include both:

```text
configuration
runtime/status inspection
```

where aria2 provides both.

---

# 33. RPC Coverage

The agent must account for all relevant aria2 RPC functionality.

Do not implement only:

```text
add
pause
resume
remove
status
```

The broader RPC surface includes operations for:

```text
adding downloads
torrent/metalink ingestion
status
active/waiting/stopped downloads
files
peers
servers
options
global options
position
URI manipulation
statistics
session information
version
result cleanup
shutdown
```

Exact methods and signatures must come from the authoritative aria2 specification used by the project.

---

# 34. UI Coverage

The application should ultimately expose appropriate UI for:

```text
Dashboard
Downloads
Add Download
Download Inspector
Files
Peers
Servers
Trackers
Options
Hashes
Logs
Statistics
Queue
Scheduler
Settings
Daemon/Connection
Categories
Diagnostics
About
```

Not every aria2 field needs a dedicated top-level screen.

Use contextual inspectors and advanced panels.

---

# 35. Accessibility

UI work should consider:

```text
keyboard navigation
focus order
visible focus
readable labels
tooltips/help
status without color alone
sufficient contrast
resizable windows
usable dialogs
```

Do not encode important state only through color.

---

# 36. Performance

Avoid:

```text
full-table rebuilds on every RPC update
unbounded event queues
polling every download independently
blocking filesystem operations in UI
unnecessary serialization
```

Prefer incremental state updates.

---

# 37. Logging

Logs should be structured and useful.

At minimum capture:

```text
timestamp
level
component
event
download ID where applicable
request ID where applicable
exception information
```

Never capture secrets.

---

# 38. Diagnostics

Diagnostic exports must be safe to share.

They may include:

```text
application version
Python version
platform
aria2 version
capabilities
configuration schema
recent error codes
component health
```

They must exclude:

```text
passwords
tokens
RPC secrets
proxy credentials
private authentication data
```

---

# 39. Git Rules

Do not rewrite unrelated files.

Do not modify generated/lock files manually unless the task requires it.

For dependency changes use:

```bash
uv add ...
uv remove ...
```

For development dependencies use the appropriate `uv` development dependency mechanism.

Commit messages should be focused.

Examples:

```text
feat(domain): add typed download model
feat(aria2): add typed rpc client
feat(ui): add download inspector
test(aria2): add tell-status fixtures
docs: document aria2 option mapping
refactor: remove legacy controller dependency
```

---

# 40. Forbidden Shortcuts

Do not:

```text
disable type checking
disable lint rules globally
skip failing tests
delete failing tests
use Any everywhere
catch Exception everywhere
use shell=True casually
put RPC in widgets
put database code in domain
introduce global service locators
duplicate aria2 option definitions
invent aria2 behavior
delete legacy code prematurely
```

---

# 41. Handling Existing Failures

If tests fail before your change:

1. Record the baseline.
2. Determine whether your change affects the failure.
3. Do not hide the failure.
4. Fix it only if within scope.
5. Otherwise report it explicitly.

Never turn:

```text
known failure
```

into:

```text
ignored failure
```

---

# 42. Generated Code/Data

Generated aria2 matrices or documentation should identify their source.

Prefer:

```text
source specification
      ↓
generator
      ↓
generated artefact
```

rather than manually maintaining duplicated data.

Generated files must not become an undocumented source of truth.

---

# 43. PR/Commit Acceptance Checklist

Before considering work complete:

```text
[ ] PLAN.md requirements understood
[ ] Issue dependencies satisfied
[ ] Correct architecture boundary used
[ ] Python 3.14 APIs used appropriately
[ ] All new public functions typed
[ ] No unjustified Any
[ ] External data validated
[ ] aria2 behavior verified
[ ] Security reviewed
[ ] Tests added
[ ] Existing tests pass
[ ] Ruff passes
[ ] Ruff format passes
[ ] ty passes
[ ] Documentation updated
[ ] No unrelated changes
```

---

# 44. Completion Report Template

Every completed issue should produce a concise report:

```text
## Implementation

<what changed>

## Files

<files created/modified/deleted>

## Tests

<tests added/updated>

## Validation

- ruff: PASS/FAIL
- format: PASS/FAIL
- ty: PASS/FAIL
- pytest: PASS/FAIL
- build: PASS/FAIL

## Architecture

<boundary/dependency implications>

## Security

<security considerations>

## Documentation

<docs updated>

## Limitations

<known limitations>

## Follow-up

<remaining work>
```

---

# 45. Blocked Report Template

When unable to proceed:

```text
## BLOCKED

### Issue

<issue ID>

### Blocker

<exact blocker>

### Evidence

<source, test, code or specification evidence>

### Attempted

<what was tried>

### Decision Required

<exact decision required>

### Recommended Resolution

<recommendation>

### Impact

<what work is blocked>
```

---

# 46. Final Principle

Optimize for:

```text
correctness
clarity
type safety
testability
security
maintainability
aria2 compatibility
user experience
```

Do not optimize for:

```text
fewest lines
fewest files
fastest apparent implementation
shortest issue completion
```

The correct implementation is the one that leaves the repository easier for the **next human and next AI agent** to understand.

The desired final dependency relationship is:

```text
                 ┌───────────────┐
                 │ ttkbootstrap  │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Presentation  │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Application   │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    Domain     │
                 └───────┬───────┘
                         ▲
                         │
                 ┌───────┴───────┐
                 │Infrastructure │
                 ├───────────────┤
                 │ aria2 RPC     │
                 │ aria2 daemon  │
                 │ persistence   │
                 │ filesystem    │
                 │ networking    │
                 │ OS services   │
                 └───────────────┘
```

**Keep the domain independent. Keep aria2 behind adapters. Keep the UI dumb. Keep external data typed. Keep the specification authoritative.**