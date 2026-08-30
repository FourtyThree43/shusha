# AGENTS.md

# Shusha AI Coding Agent Operating Contract

This file is authoritative for AI coding agents working in the Shusha repository.

`PLAN.md` defines WHAT is being built.

`AGENTS.md` defines HOW an agent must work.

When the two conflict, stop and report the conflict rather than guessing.

---

# 1. Mission

Shusha is being rewritten as:

> A multi-backend download acquisition and orchestration platform with a typed Python 3.14+ core, ttkbootstrap Desktop, Textual TUI/Diagnostics, CLI, acquisition services, browser integration and a versioned plugin architecture.

The first complete backend is aria2.

The second backend is yt-dlp.

---

# 2. Non-Negotiable Rules

## RULE-001 — Inspect before editing

Before changing code:

1. inspect the relevant repository tree;
2. inspect existing implementation;
3. inspect tests;
4. inspect related documentation;
5. identify architectural dependencies;
6. identify existing behavior that must be preserved.

Never rewrite a module based only on its filename.

---

## RULE-002 — One ticket at a time

An agent MUST work against one explicit issue/ticket.

If additional work is discovered:

- complete the current ticket only if necessary;
- otherwise create/report a follow-up ticket;
- do not silently expand scope.

---

## RULE-003 — Do not bypass architecture

Never implement:

```text
Desktop → aria2
Textual → aria2
CLI → aria2
Desktop → yt-dlp
```

Use:

```text
Frontend
 ↓
Application
 ↓
Backend Contract
 ↓
Adapter
```

---

# 3. Dependency Rules

Allowed:

```text
core
  ↑
application
  ↑
frontends

backend adapters
  ↑
backend contracts

acquisition adapters
  ↑
application/core
```

Forbidden:

```text
core → ttkbootstrap
core → Textual
core → CLI
core → aria2
core → yt-dlp

frontend → concrete backend

backend → frontend
```

If a dependency is genuinely required, create an ADR before implementing it.

---

# 4. Coding Standards

Target:

```text
Python >= 3.14
```

Use:

```text
uv
ruff
ty
pytest
```

Commands:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

Before completion:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

---

# 5. Typing Rules

Public APIs MUST be typed.

Prefer:

```python
Protocol
TypedDict
dataclass
enum.StrEnum
type aliases
generic types
```

Avoid:

```python
Any
dict[str, Any]
untyped callbacks
dynamic attribute access
```

`Any` requires a local justification.

Do not use type ignores without explanation.

---

# 6. Domain Rules

Core models MUST be backend-neutral.

Good:

```text
Job
Artifact
Source
Capability
Peer
Tracker
Server
BackendOption
```

Bad:

```text
Aria2Job
Aria2Artifact
YtDlpJob
TtkJob
```

Backend-specific data may exist behind a namespaced extension boundary.

---

# 7. Acquisition Rules

All acquisition mechanisms MUST converge on:

```text
AcquisitionRequest
```

Supported inputs include:

```text
URL
clipboard
browser
drag/drop
magnet
torrent
Metalink
CLI
```

Pipeline:

```text
Acquisition
→ Detection
→ Inspection
→ Resolution
→ Policy
→ Backend Selection
→ Job
```

Never create a direct:

```python
clipboard_url → aria2.add_uri()
```

workflow.

---

# 8. Backend Rules

Every backend MUST implement the shared backend contract.

Every backend MUST expose:

```text
identity
capabilities
lifecycle
configuration
job operations
status
events
diagnostics
```

Backend-specific features are capabilities.

Never assume all backends support:

```text
peers
trackers
torrent
subtitles
media formats
```

Check capabilities.

---

# 9. aria2 Rules

aria2 support MUST be implemented against the documented aria2c contract.

Do not assume the existing Shusha implementation represents complete aria2 support.

When implementing an aria2 feature:

1. identify the official option/RPC definition;
2. record it in the option/RPC matrix;
3. map it to a typed model;
4. implement backend behavior;
5. add contract/integration tests;
6. document it;
7. expose it in Desktop if applicable;
8. expose it through CLI/TUI where applicable.

Never silently drop an aria2 option.

Unsupported behavior MUST be classified:

```text
unsupported
not applicable
backend limitation
platform limitation
security restriction
deprecated
```

---

# 10. aria2 Option Implementation

Every option should have:

```text
name
short name
type
default
allowed values
scope
mutability
protocol applicability
description
security implications
```

Do not hand-copy large option lists without validation.

Prefer generating or validating the catalogue from authoritative source data.

---

# 11. yt-dlp Rules

yt-dlp MUST remain an adapter/backend.

Core MUST NOT contain:

```text
yt-dlp format IDs
yt-dlp command flags
yt-dlp extractor names
```

Media Grabber works through:

```text
MediaResolver
→ yt-dlp adapter
```

A media inspection operation MUST be distinguishable from an execution operation.

---

# 12. Plugin Rules

Plugins MUST declare:

```text
id
version
API version
capabilities
permissions
entrypoint
configuration
```

Plugins MUST NOT receive unrestricted:

```text
filesystem
process
credential
browser
network
```

access.

Any new plugin capability requires:

1. contract;
2. permission declaration;
3. test fixture;
4. documentation.

---

# 13. Browser Rules

Browser extensions are acquisition clients.

They MUST NOT contain:

```text
download scheduler
database
aria2 RPC implementation
yt-dlp execution
business rules
```

Browser communication goes through the acquisition gateway/native host.

Never trust browser input.

Validate:

```text
origin
request type
payload
URL
permissions
authentication
```

---

# 14. Clipboard Rules

Clipboard capture MUST be configurable.

Never silently exfiltrate clipboard contents.

Default behavior should favor:

```text
detect
notify
ask
```

unless the user explicitly enables automatic behavior.

Deduplicate repeated inputs.

---

# 15. Security Rules

Never log:

```text
passwords
tokens
cookies
authorization headers
private keys
proxy passwords
RPC secrets
```

Never interpolate untrusted input into shell commands.

Prefer argument arrays/subprocess APIs.

Validate paths before filesystem operations.

Treat browser, clipboard and plugin inputs as untrusted.

---

# 16. Event Rules

Important state changes MUST emit typed events.

Events MUST be:

```text
typed
serializable where appropriate
correlatable
documented
testable
```

Frontends should subscribe to application events rather than implement backend polling logic independently.

---

# 17. Persistence Rules

Domain objects MUST NOT directly access:

```text
SQLite
shelve
JSON files
TOML files
filesystem
```

Use persistence interfaces.

Persistence changes require migration tests.

Never destroy existing user data during migration.

---

# 18. Desktop Rules

Technology:

```text
ttkbootstrap
Tkinter
```

Desktop must consume application contracts.

Widgets MUST NOT call backend RPC clients directly.

Use:

```text
screen
view model/state
command/query
event
```

Do not put business logic inside widgets.

---

# 19. Desktop Design Rules

Use the shared design system.

Standardize:

```text
spacing
typography
colors
states
icons
buttons
tables
dialogs
forms
navigation
notifications
empty states
loading states
error states
```

Responsive classes:

```text
Compact
Standard
Wide
UltraWide
```

Do not solve every screen independently.

---

# 20. 132-Screen Rules

The 132-screen catalogue is an acceptance baseline.

For each screen:

```text
catalogue ID
feature
route
state
capabilities
backend
layout
controls
interaction
error states
responsive behavior
tests
```

An agent may merge a screen into another screen if:

- the feature remains accessible;
- all required states remain covered;
- the acceptance criteria remain satisfied;
- the catalogue mapping is updated.

Do not preserve obsolete UI purely to preserve screen count.

---

# 21. Textual Rules

Textual is a first-class product surface.

It is intended for:

```text
TUI
diagnostics
doctor
operator console
live monitoring
SSH/headless administration
```

Do not attempt to clone all Desktop screens.

Use terminal-native interaction patterns.

---

# 22. CLI Rules

CLI commands invoke application commands/queries.

Never:

```python
cli_command → aria2_client
```

Use:

```text
CLI
→ Application Command
→ Backend Contract
```

Support:

```text
human-readable
JSON
JSONL
```

Machine-readable output MUST remain stable.

---

# 23. Testing Rules

Every behavior change requires tests.

Test levels:

```text
unit
contract
integration
architecture
frontend
end-to-end
```

A backend implementation must pass the common backend contract tests.

A frontend must be testable against the fake backend.

---

# 24. Fake Backend Requirement

The fake backend MUST be used to validate frontend behavior.

It should simulate:

```text
queued
active
paused
failed
completed
cancelled
```

and:

```text
progress
speed
ETA
files
events
capabilities
```

If a frontend cannot be tested without a real aria2 installation, its coupling is suspect.

---

# 25. Fake Acquisition Requirement

Provide fake acquisition providers for:

```text
clipboard
browser
drag/drop
URL resolution
media inspection
```

Use them for deterministic application tests.

---

# 26. Documentation Rules

Every architectural feature MUST have documentation.

At minimum:

```text
what it does
why it exists
public contract
configuration
failure modes
security implications
tests
```

Update documentation in the same ticket as implementation whenever feasible.

Never leave documentation intentionally stale until "later."

---

# 27. ADR Rules

Create an ADR when changing:

```text
dependency direction
public domain contract
backend contract
plugin contract
security boundary
persistence strategy
browser bridge
service boundary
screen architecture
```

An ADR must explain:

```text
context
decision
alternatives
consequences
```

---

# 28. AI Agent Workflow

For every ticket:

## Step 1 — Read

Read:

```text
AGENTS.md
PLAN.md
relevant ADRs
relevant source
relevant tests
```

## Step 2 — Inspect

Identify:

```text
current implementation
architectural boundary
dependencies
test coverage
documentation
```

## Step 3 — Plan

Before editing, write an internal implementation plan:

```text
files to modify
files to create
tests
documentation
risks
```

## Step 4 — Implement

Make the smallest coherent change.

Do not refactor unrelated code.

## Step 5 — Test

Run targeted tests first.

Then run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

where feasible.

## Step 6 — Review

Check:

```text
dependency direction
typing
security
error handling
logging
documentation
tests
```

## Step 7 — Report

Final report MUST include:

```text
Implemented
Files changed
Tests run
Checks run
Known limitations
Follow-up tickets
```

---

# 29. Ticket Completion Template

Use:

```text
## Implementation

<summary>

## Files Changed

- path
- path

## Tests

- test name
- test name

## Validation

- ruff: PASS/FAIL
- format: PASS/FAIL
- ty: PASS/FAIL
- pytest: PASS/FAIL

## Acceptance Criteria

- [x] criterion
- [x] criterion

## Limitations

<none or explicit limitations>

## Follow-up

<none or issue IDs>
```

---

# 30. Stop Conditions

An agent MUST stop rather than guess when:

- a required contract is ambiguous;
- a security boundary is unclear;
- a public API would need incompatible change;
- a ticket contradicts PLAN.md;
- required source documentation is unavailable;
- an operation could destroy user data;
- an undocumented credential flow is discovered;
- backend semantics are unclear.

Report the blocker and identify the smallest decision required.

---

# 31. Forbidden Shortcuts

Never:

```text
disable type checking
delete failing tests
weaken acceptance criteria
catch Exception everywhere
silently ignore backend errors
copy backend logic into frontend
duplicate business logic across frontends
hard-code backend detection
hard-code aria2 assumptions into core
store secrets in ordinary configuration
execute shell commands through string concatenation
skip migration handling
skip documentation for public contracts
```

---

# 32. Refactoring Policy

Refactor only when:

```text
required by current ticket
required to enforce architecture
required to remove a proven defect
```

Large refactors require an explicit ticket.

Do not combine:

```text
feature implementation
unrelated cleanup
formatting entire repository
renaming unrelated modules
```

into one change.

---

# 33. Dependency Introduction

Before adding a dependency:

1. identify the problem;
2. determine whether stdlib/current dependencies suffice;
3. check licensing;
4. check Python 3.14 support;
5. check maintenance;
6. assess security;
7. update pyproject/lockfile;
8. document why it exists.

Prefer minimal dependencies.

---

# 34. Frontend Independence Test

Every major frontend feature should be explainable as:

```text
Command
Query
State
Event
```

If the implementation requires:

```text
widget → backend client
```

stop and refactor.

---

# 35. Backend Independence Test

Every backend must be replaceable without changing:

```text
Desktop shell
Textual shell
CLI parser
Persistence
Job model
Artifact model
Acquisition model
```

If replacing a backend requires changes outside its adapter/application integration, investigate the coupling.

---

# 36. Acquisition Independence Test

Adding a new acquisition source should require:

```text
new acquisition adapter
```

rather than changes to:

```text
aria2
yt-dlp
Job domain
Desktop widgets
CLI command implementations
```

---

# 37. Release Gate

No release candidate may be declared until:

```text
[ ] architecture tests pass
[ ] typing passes
[ ] lint passes
[ ] tests pass
[ ] aria2 matrix complete
[ ] RPC matrix complete
[ ] acquisition tests pass
[ ] browser security tests pass
[ ] plugin permission tests pass
[ ] Desktop baseline validated
[ ] Textual diagnostics validated
[ ] CLI JSON output validated
[ ] persistence recovery validated
[ ] documentation synchronized
```

---

# 38. Final Agent Principle

When in doubt, prefer:

```text
small
typed
explicit
testable
backend-neutral
event-driven
capability-driven
secure
documented
```

over:

```text
clever
implicit
duplicated
backend-specific
UI-driven
untyped
global
```

The objective is not merely to make the code work.

The objective is to preserve the architecture so that:

```text
new backend
new frontend
new acquisition source
new plugin
new media capability
new automation interface
```

can be added without destabilizing the existing system.