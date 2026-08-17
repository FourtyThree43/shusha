# Shusha Modernization Plan

**Project:** Shusha — aria2 GUI Download Manager
**Modernization goal:** Restore, stabilize, test, type-check, package, and modernize the existing Shusha application without rewriting its architecture or changing intended user-visible behavior.

---

## 1. Executive Summary

Shusha is an existing Python/Tkinter desktop application that communicates with `aria2` through RPC and uses `ttkbootstrap` for its GUI.

The repository has already partially migrated between several Python tooling ecosystems:

* Hatchling build backend
* Hatch environments
* PDM dependency management
* UV dependency management
* Ruff
* legacy mypy configuration

The current project contains both:

```text
uv.lock
pdm.lock
```

The modernization will establish **UV as the authoritative project/dependency manager** and use the **Astral toolchain by default**:

```text
uv       dependency management / environments / builds
ruff     linting / formatting
ty       static type checking
pytest   testing
```

The project should **not** introduce mypy, Black, isort, flake8, Poetry, PDM, or tox unless a specific, documented compatibility requirement makes an exception necessary.

The modernization is explicitly **not a rewrite**.

The existing Tkinter/MVC architecture, aria2 integration, application behavior, and user workflows should be preserved unless a change is explicitly justified and approved.

---

# 2. Current Repository State

Current high-level repository:

```text
shusha/
├── .github/
├── docs/
├── ray/
├── src/
│   └── shusha/
├── tests/
├── .git/
├── .venv/
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.txt
├── README.md
├── SECURITY.md
├── pdm.lock
├── pyproject.toml
└── uv.lock
```

The application uses a `src` layout.

Relevant application areas include:

```text
src/shusha/
├── __about__.py
├── __init__.py
├── __main__.py
├── ShushaDM.py
├── models/
├── views/
├── controller/
├── resources/
└── ...
```

The repository history indicates that the project previously used PDM and has undergone several dependency/configuration changes.

The historical dependency declaration included:

```toml
"ttkbootstrap>=1.10.1"
```

which is too broad to guarantee compatibility with the existing application.

---

# 3. Current Runtime Findings

The application initially failed because Tkinter was unavailable:

```text
ModuleNotFoundError: No module named 'tkinter'
```

The development environment is Fedora Linux.

Tkinter was subsequently installed using:

```bash
sudo dnf install python3-tkinter
```

The installed system components include Python 3.14-compatible Tkinter/Tcl/Tk packages.

The project currently runs under:

```text
Python 3.14.6
```

The current UV environment uses:

```text
/usr/sbin/python3
```

after recreation of `.venv`.

The Tkinter problem is therefore considered resolved pending final cross-platform testing.

---

# 4. Current Known Runtime Blocker

The application currently reaches the GUI code but fails with:

```text
ModuleNotFoundError: No module named 'ttkbootstrap.tableview'
```

The failing import is:

```python
from ttkbootstrap.tableview import TableRow, Tableview
```

The current resolved dependency is:

```text
ttkbootstrap==2.2.1
```

The installed package no longer contains:

```text
ttkbootstrap/tableview.py
```

The current package layout contains, among other things:

```text
ttkbootstrap/
├── widgets/
├── dialogs/
├── style/
├── themes/
├── localization/
├── utils/
├── internal/
├── window.py
├── menu.py
├── utility.py
└── ...
```

The repository history confirms that `Tableview` was part of the application's historical implementation.

Relevant historical commits include:

```text
9362c7e {catch a Bubble Mondays}
1aca07e Updated Status Window
cf3f6b0 Final commit, ready for tagging
ae5ac16 Added api
```

This compatibility problem must be investigated before deciding whether to:

1. pin an older compatible `ttkbootstrap` release,
2. migrate Shusha's `Tableview` integration to the current API,
3. introduce a small compatibility layer,
4. or use another justified solution.

The modernization must not blindly downgrade or upgrade the dependency.

---

# 5. Modernization Principles

## 5.1 Preserve behavior

This is a modernization project, not a rewrite.

Existing user-visible behavior should remain intact unless a deliberate change is approved.

---

## 5.2 Prefer small, reversible changes

Changes should be:

* isolated,
* reviewable,
* testable,
* reversible,
* attributable to a specific modernization objective.

---

## 5.3 Astral-first tooling

Preferred tooling:

```text
uv
ruff
ty
```

Testing:

```text
pytest
pytest-cov
coverage.py
```

Build backend:

```text
Hatchling
```

Hatchling may remain because it is the build backend rather than the project/environment manager.

---

## 5.4 No unnecessary tool proliferation

Do not introduce:

```text
PDM
Poetry
Pipenv
tox
mypy
Black
isort
flake8
pyright
```

unless a concrete compatibility problem requires one.

If an exception is required, document:

* why,
* where,
* for how long,
* why Astral tooling cannot reasonably solve it.

---

## 5.5 No architecture rewrite

Do not replace:

* Tkinter,
* ttkbootstrap,
* aria2,
* the existing MVC-style architecture,
* the RPC model,
* persistence,
* the controller architecture,

merely because a newer architecture is fashionable.

No:

* async rewrite,
* web frontend,
* dependency injection framework,
* GUI framework migration,
* database rewrite,

without explicit architectural approval.

---

# 6. Target Developer Experience

The final development experience should be simple.

## Setup

```bash
git clone <repository>
cd shusha
uv sync
```

## Run

Prefer:

```bash
uv run shusha
```

or, if a console entry point is not appropriate:

```bash
uv run python -m shusha
```

## Lint

```bash
uv run ruff check .
```

## Format

```bash
uv run ruff format .
```

## Formatting verification

```bash
uv run ruff format --check .
```

## Type checking

```bash
uv run ty check
```

## Tests

```bash
uv run pytest
```

## Coverage

```bash
uv run pytest --cov=shusha --cov-report=term-missing
```

## Build

```bash
uv build
```

---

# 7. Target Architecture

The existing architecture should be retained initially.

Conceptually:

```text
                    ┌─────────────────┐
                    │      View       │
                    │    Tkinter      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Controller    │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
          ┌──────────────┐       ┌──────────────┐
          │    Models    │       │   aria2 RPC  │
          └──────────────┘       └──────────────┘
                 │
                 ▼
          ┌──────────────┐
          │ Persistence   │
          └──────────────┘
```

The modernization should clarify these boundaries rather than replace them.

The GUI should not become the owner of business logic.

The model layer should not depend directly on Tkinter.

The RPC boundary should be isolated from application state.

---

# 8. Multi-Agent Engineering Team

The modernization will use eight specialized agents.

## Agent 1 — Codebase Archaeologist

**Purpose:** Understand the existing application and historical intent before changes are made.

Responsibilities:

* repository mapping,
* architecture analysis,
* Git history analysis,
* dependency history,
* runtime requirements,
* entry points,
* external dependencies,
* existing tests,
* known bugs,
* compatibility assumptions,
* modernization risk register.

This agent should be primarily research-oriented and should not perform broad refactoring.

---

## Agent 2 — UV/Packaging Architect

**Purpose:** Establish clean modern Python packaging and dependency management.

Responsibilities:

* `pyproject.toml`,
* UV dependency groups,
* runtime dependencies,
* development dependencies,
* Python version policy,
* lockfile,
* package discovery,
* package data,
* console scripts,
* wheel building,
* removal of PDM environment configuration,
* removal of obsolete Hatch environment configuration.

UV is authoritative for dependency/environment management.

Hatchling may remain as the build backend.

---

## Agent 3 — Runtime Compatibility Engineer

**Purpose:** Make the historical application run correctly on modern Python and modern supported dependencies.

Responsibilities:

* Python compatibility,
* Tkinter,
* ttkbootstrap,
* Pillow,
* platformdirs,
* aria2,
* RPC,
* filesystem behavior,
* subprocesses,
* clipboard,
* platform-specific behavior,
* application startup.

The current `ttkbootstrap.tableview` failure is the first major target.

---

## Agent 4 — Ruff Code Quality Engineer

**Purpose:** Establish consistent linting and formatting.

Responsibilities:

* Ruff configuration,
* lint rule selection,
* formatting,
* import sorting,
* safe code modernization,
* dead/unused code discovery,
* safe Ruff fixes.

Ruff replaces the need for:

```text
Black
isort
flake8
autoflake
pyupgrade
```

where appropriate.

---

## Agent 5 — ty Type-System Engineer

**Purpose:** Introduce comprehensive static typing.

Responsibilities:

* `ty check`,
* public API annotations,
* model typing,
* RPC response types,
* controller interfaces,
* persistence interfaces,
* typed dictionaries,
* protocols,
* state typing,
* reduction of accidental `Any`,
* type-checking CI.

**mypy must not be introduced.**

---

## Agent 6 — Testing and QA Engineer

**Purpose:** Establish a serious automated test suite.

Responsibilities:

* unit tests,
* component tests,
* integration tests,
* RPC fakes,
* persistence tests,
* filesystem tests,
* controller tests,
* regression tests,
* GUI smoke tests,
* coverage,
* test fixtures,
* CI test organization.

The objective is not merely high coverage.

Tests must protect meaningful behavior.

---

## Agent 7 — Security Engineer

**Purpose:** Audit security-sensitive application boundaries.

Responsibilities:

* URL input,
* filesystem paths,
* download paths,
* path traversal,
* subprocess execution,
* aria2 RPC exposure,
* RPC credentials,
* configuration files,
* secrets,
* temporary files,
* logging,
* untrusted responses.

Confirmed security issues must receive regression tests.

---

## Agent 8 — CI/Release/Integration Guardian

**Purpose:** Act as final integration and release gate.

Responsibilities:

* integrate agent changes,
* validate the full toolchain,
* validate CI,
* validate lockfiles,
* build distributions,
* test clean installation,
* verify package resources,
* verify documentation,
* verify supported Python versions,
* enforce final quality gates.

This agent should not introduce broad new features.

---

# 9. Agent 1 Specification — Codebase Archaeologist

## Mission

Reconstruct what Shusha is, how it works, and what historical assumptions must be preserved.

## Required investigation

Inspect:

```text
src/
tests/
.github/
docs/
pyproject.toml
uv.lock
pdm.lock
README.md
SECURITY.md
CONTRIBUTING.md
```

Investigate:

```text
src/shusha/__main__.py
src/shusha/ShushaDM.py
src/shusha/models/
src/shusha/views/
src/shusha/controller/
```

Search Git history for:

```text
ttkbootstrap
Tableview
TableRow
aria2
platformdirs
pyperclip
Pillow
tomli
```

Useful commands:

```bash
git log --all -S'Tableview'
git log --all -S'ttkbootstrap'
git log --all -S'aria2'
git log --all -S'platformdirs'
git log --all -S'pyperclip'
```

## Deliverable

Produce:

* architecture report,
* dependency matrix,
* historical compatibility matrix,
* runtime requirements,
* test inventory,
* obsolete tooling inventory,
* risk register,
* recommended modernization order.

No broad implementation work.

---

# 10. Agent 2 Specification — UV/Packaging

## Target

Move completely toward:

```text
UV + Hatchling
```

Remove obsolete project management configuration.

Potentially remove:

```toml
[tool.hatch.envs.default]
[tool.hatch.envs.types]
[tool.pdm.dev-dependencies]
```

if no longer required.

## Dependency groups

Use:

```toml
[dependency-groups]
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
    "ty",
]
```

Runtime dependencies remain under:

```toml
[project]
dependencies = [
    ...
]
```

Do not move runtime packages into development groups.

## Lockfile

`uv.lock` is authoritative.

If PDM is fully removed:

```text
pdm.lock
```

should be deleted.

Never manually edit `uv.lock`.

Use:

```bash
uv lock
uv sync
```

---

# 11. Python Version Policy

The original project declared:

```toml
requires-python = ">=3.8"
```

Historical Git history indicates that the project later used:

```toml
requires-python = ">=3.10"
```

The final Python support policy must be determined from:

* current source,
* ttkbootstrap,
* Pillow,
* platformdirs,
* Tkinter,
* build tooling,
* CI availability,
* actual project requirements.

Python 3.14 should not be rejected merely because the project is old.

The current development environment is:

```text
Python 3.14.6
Fedora 43
```

The final supported range must be deliberate and documented.

---

# 12. Agent 3 Specification — Runtime Compatibility

## Immediate target

Resolve:

```text
ModuleNotFoundError: No module named 'ttkbootstrap.tableview'
```

## Required investigation

Determine:

1. Historical ttkbootstrap version.
2. Whether the old version provides `Tableview`.
3. Which version the project actually used.
4. When the API changed.
5. Whether pinning is sufficient.
6. Whether migration is preferable.
7. Whether an adapter is appropriate.

Test old versions without unnecessarily modifying the project.

For example:

```bash
uv run --with 'ttkbootstrap==1.10.1' python -c \
'import ttkbootstrap; print(ttkbootstrap.__version__)'
```

and verify:

```bash
uv run --with 'ttkbootstrap==1.10.1' python -c \
'import ttkbootstrap.tableview as t; print(t.Tableview, t.TableRow)'
```

The exact compatible version must be established through evidence.

## Compatibility policy

Prefer:

1. dependency/configuration correction,
2. small compatibility adapter,
3. targeted source migration,
4. dependency replacement as a last resort.

---

# 13. Agent 4 Specification — Ruff

## Baseline

Run before major source modification:

```bash
uv run ruff check .
uv run ruff format --check .
```

Record the baseline.

## Configuration

Evaluate:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",
    "F",
    "I",
    "UP",
    "B",
    "SIM",
]

[tool.ruff.format]
quote-style = "double"
```

The final configuration must be based on the actual codebase.

Do not blindly enable every rule.

## Safe fixes

Use:

```bash
uv run ruff check . --fix
uv run ruff format .
```

Review semantic-looking changes.

Do not solve problems by dumping:

```python
# noqa
```

throughout the code.

---

# 14. Agent 5 Specification — ty

## Tool

Use:

```bash
uv run ty check
```

No mypy.

## Initial pass

Record the baseline diagnostics.

Classify them:

* real defect,
* missing annotation,
* third-party typing issue,
* Tkinter limitation,
* dynamic code,
* false positive,
* intentional dynamic behavior.

## Priority

Type in this order:

1. aria2 RPC client,
2. models,
3. download state,
4. options,
5. persistence/database,
6. controller,
7. utilities,
8. public APIs,
9. GUI callbacks,
10. miscellaneous UI code.

## RPC typing

RPC data should not allow `Any` to propagate through the application.

Use appropriate:

```text
TypedDict
type aliases
dataclasses
Protocols
enums
```

where they improve correctness.

Do not replace every `Any` with `object`.

Do not use suppression simply to make CI green.

---

# 15. Agent 6 Specification — Testing

## Test pyramid

The test suite should include:

```text
                    GUI smoke
                       ▲
                 integration
                       ▲
               component tests
                       ▲
                    unit tests
                       ▲
             static validation
```

## Unit tests

Cover:

* models,
* utilities,
* options,
* parsers,
* statistics,
* state transitions,
* database logic,
* path handling.

## Component tests

Cover:

* aria2 client,
* controller,
* download manager logic,
* persistence.

## RPC tests

Do not require a real aria2 daemon for normal tests.

Create a fake/mock RPC boundary.

Test:

* successful calls,
* RPC failures,
* malformed responses,
* missing fields,
* connection failures,
* timeouts,
* unexpected statuses.

## Integration tests

Test:

* controller/model interactions,
* model/persistence interactions,
* RPC/application boundary,
* platformdirs configuration.

## Filesystem tests

Use temporary directories.

Test:

* configuration,
* sessions,
* persistence,
* invalid paths,
* missing files,
* error handling.

Never rely on the developer's real home directory.

## GUI tests

Avoid brittle pixel tests.

Separate GUI behavior from application logic.

Use:

* controller tests,
* model tests,
* widget smoke tests,
* headless CI where practical.

## Regression tests

Every significant modernization bug should receive a regression test.

Especially:

* ttkbootstrap compatibility,
* startup,
* RPC failures,
* session handling,
* download state transitions.

---

# 16. Coverage Strategy

Use:

```bash
uv run pytest --cov=shusha --cov-report=term-missing
```

Measure:

* line coverage,
* branch coverage.

Do not require 100% blindly.

Prioritize high coverage for:

```text
RPC
models
state transitions
persistence
controller
utilities
```

Lower coverage is acceptable for:

```text
Tkinter glue
GUI presentation
platform-specific display code
```

Coverage is a diagnostic tool, not the primary definition of quality.

---

# 17. Optional Property-Based Testing

The testing agent should evaluate whether Hypothesis provides meaningful value.

Good candidates:

* URL/path handling,
* parsers,
* statistics,
* state transitions,
* RPC conversion.

Do not add Hypothesis merely to increase dependency count.

---

# 18. Agent 7 Specification — Security

## Audit

Review:

* arbitrary URLs,
* filenames,
* download directories,
* path traversal,
* symlinks,
* subprocess calls,
* shell execution,
* aria2 RPC,
* RPC authentication,
* RPC exposure,
* credentials,
* temporary files,
* configuration files,
* logging,
* clipboard input,
* environment variables.

## Important questions

Determine whether:

1. URLs can cause unintended local file access.
2. filenames escape the configured download directory.
3. subprocesses invoke a shell unnecessarily.
4. aria2 RPC can be exposed without authentication.
5. RPC credentials are logged.
6. secrets appear in exceptions.
7. untrusted responses are trusted without validation.
8. downloaded files can overwrite arbitrary paths.
9. symlinks bypass intended directory restrictions.
10. configuration files have unsafe permissions.

Confirmed vulnerabilities require regression tests.

---

# 19. Agent 8 Specification — CI/Release

## Required validation

At minimum:

```bash
uv lock
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest --cov=shusha --cov-report=term-missing
uv build
```

## Clean wheel validation

Do not trust only the editable development environment.

Build:

```bash
uv build
```

Inspect the resulting wheel.

Create a clean environment and install the built wheel.

Verify:

```bash
python -m shusha
```

where system GUI dependencies are available.

## Package data

Verify that the distribution contains:

* icons,
* resources,
* assets,
* required Python modules,
* metadata,
* version information.

---

# 20. CI Strategy

CI should enforce:

```text
Ruff
ty
pytest
coverage
build
```

The matrix should match the declared Python support policy.

Potential jobs:

```text
lint
format
typecheck
unit-tests
integration-tests
build
package-smoke-test
gui-smoke-test
aria2-integration-test
```

GUI and aria2 jobs should be isolated if they require special infrastructure.

---

# 21. Security and Runtime Integration

Security review and runtime testing should interact.

For example:

```text
URL input
   ↓
validation
   ↓
controller
   ↓
aria2 RPC
   ↓
download path
   ↓
filesystem
```

Each boundary should have explicit tests.

The goal is to avoid having a type-safe, well-formatted application that nevertheless trusts dangerous runtime data.

---

# 22. Agent Orchestration

Agents should not all work simultaneously.

Recommended sequence:

```text
                    ┌──────────────────────┐
                    │ 1. Archaeologist     │
                    │      READ/RESEARCH    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
       │ 2. UV /     │  │ 3. Runtime   │  │ 6. Testing  │
       │ Packaging   │  │ Compatibility│  │ Architecture │
       └──────┬──────┘  └──────┬───────┘  └──────┬───────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                       ┌───────▼────────┐
                       │ 4. Ruff        │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │ 5. ty          │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │ 7. Security    │
                       └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │ 8. CI/Release  │
                       └────────────────┘
```

Testing architecture can begin after Archaeologist analysis, but broad test implementation should wait until major runtime/API decisions are known.

---

# 23. Agent Communication Contract

Every agent must report:

```text
STATUS
FILES CHANGED
FILES NOT TOUCHED
DECISIONS
ASSUMPTIONS
TESTS ADDED
COMMANDS RUN
COMMANDS PASSING
COMMANDS FAILING
KNOWN RISKS
FOLLOW-UP REQUIRED
```

## Cross-agent conflicts

Agents must never silently resolve conflicting architectural decisions.

Example:

Agent 2:

```text
ttkbootstrap==1.x
```

Agent 3:

```text
migrate to ttkbootstrap 2.x
```

This must become an explicit orchestrator decision.

Neither agent should overwrite the other decision without coordination.

---

# 24. Change Ownership

| Area                        | Owner             |
| --------------------------- | ----------------- |
| Repository archaeology      | Archaeologist     |
| Python dependency policy    | UV/Packaging      |
| pyproject.toml              | UV/Packaging      |
| uv.lock                     | UV/Packaging      |
| Runtime compatibility       | Runtime Engineer  |
| ttkbootstrap                | Runtime Engineer  |
| Ruff configuration          | Ruff Engineer     |
| Formatting                  | Ruff Engineer     |
| Static typing               | ty Engineer       |
| Tests                       | QA Engineer       |
| Coverage                    | QA Engineer       |
| Security                    | Security Engineer |
| CI                          | Release Guardian  |
| Packaging validation        | Release Guardian  |
| README development workflow | Release Guardian  |
| Architecture changes        | Orchestrator      |

No agent should make large changes outside its ownership.

---

# 25. Modernization Phases

## Phase 0 — Baseline

Before modifications:

```bash
uv sync
uv run python --version
uv run python -m shusha
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

Record all failures.

---

## Phase 1 — Archaeology

Complete Agent 1.

Produce:

* architecture map,
* dependency map,
* historical compatibility report,
* risk register.

No major source modernization yet.

---

## Phase 2 — Runtime Recovery

Fix:

* Tkinter environment,
* ttkbootstrap compatibility,
* startup path,
* external runtime dependencies.

Goal:

```bash
uv run python -m shusha
```

starts successfully.

---

## Phase 3 — Packaging Migration

Clean:

```text
PDM
Hatch environments
legacy dependency declarations
obsolete scripts
```

Keep Hatchling if useful as build backend.

Establish:

```text
uv.lock
dependency-groups
```

Goal:

```bash
uv sync --locked
```

works reproducibly.

---

## Phase 4 — Ruff

Establish:

```bash
uv run ruff check .
uv run ruff format --check .
```

Then apply safe fixes.

Avoid mixing formatting with major semantic refactors.

---

## Phase 5 — Testing Foundation

Build:

* fixtures,
* fakes,
* unit tests,
* RPC tests,
* persistence tests,
* controller tests,
* regression tests.

Get meaningful baseline coverage.

---

## Phase 6 — ty

Run:

```bash
uv run ty check
```

Type the most important boundaries first.

Fix actual defects exposed by type checking.

---

## Phase 7 — Security

Audit:

* URL input,
* RPC,
* filesystem,
* subprocesses,
* configuration,
* downloads.

Add security regression tests.

---

## Phase 8 — CI

Enforce:

```text
Ruff
format
ty
pytest
coverage
build
package smoke test
```

---

## Phase 9 — Release Validation

Verify:

```bash
uv sync --locked
uv build
```

Install the resulting artifact into a clean environment.

Run the application.

Verify resources.

---

# 26. Final Quality Gates

The modernization cannot be considered complete until all of the following pass.

## Runtime

* [ ] Application starts.
* [ ] Tkinter works.
* [ ] ttkbootstrap compatibility is intentional.
* [ ] aria2 RPC works.
* [ ] Configuration works.
* [ ] Sessions work.
* [ ] Resources load correctly.
* [ ] Icons/assets work.

## UV

* [ ] `uv sync --locked` works.
* [ ] `uv.lock` is authoritative.
* [ ] PDM is removed.
* [ ] `pdm.lock` is removed if PDM is abandoned.
* [ ] Development dependencies use UV dependency groups.
* [ ] Runtime dependencies remain runtime dependencies.

## Ruff

* [ ] `uv run ruff check .` passes.
* [ ] `uv run ruff format --check .` passes.
* [ ] Suppressions are justified.
* [ ] No broad `noqa` abuse.
* [ ] No unnecessary formatter/linter tools remain.

## ty

* [ ] `uv run ty check` passes.
* [ ] No unexplained type errors.
* [ ] Dynamic RPC boundaries are typed.
* [ ] Important public interfaces are typed.
* [ ] Any/suppression usage is justified.
* [ ] mypy is not required.

## Testing

* [ ] Unit tests.
* [ ] Component tests.
* [ ] RPC tests.
* [ ] Controller tests.
* [ ] Persistence tests.
* [ ] Filesystem tests.
* [ ] Regression tests.
* [ ] Integration tests.
* [ ] GUI smoke tests where practical.
* [ ] Coverage reporting.
* [ ] No accidental dependence on developer environment.

## Security

* [ ] URL handling reviewed.
* [ ] Path handling reviewed.
* [ ] Download directory safety reviewed.
* [ ] Subprocess execution reviewed.
* [ ] RPC security reviewed.
* [ ] Secrets reviewed.
* [ ] Configuration permissions reviewed.
* [ ] Confirmed vulnerabilities have regression tests.

## Packaging

* [ ] `uv build` passes.
* [ ] Wheel contains package resources.
* [ ] Wheel installs cleanly.
* [ ] Installed package starts.
* [ ] Version metadata is correct.

## CI

* [ ] Supported Python versions tested.
* [ ] Ruff runs.
* [ ] Ruff format verification runs.
* [ ] ty runs.
* [ ] pytest runs.
* [ ] coverage runs.
* [ ] build runs.
* [ ] package smoke test runs.

## Documentation

* [ ] README uses current project structure.
* [ ] README no longer instructs users to run `main.py`.
* [ ] UV setup documented.
* [ ] Python support documented.
* [ ] Tkinter system dependency documented.
* [ ] aria2 setup documented.
* [ ] test commands documented.
* [ ] Ruff commands documented.
* [ ] ty commands documented.
* [ ] build commands documented.
* [ ] Linux instructions are accurate.
* [ ] Windows/macOS limitations are documented where applicable.

---

# 27. Final Project Toolchain

The desired final stack is:

```text
                    ┌────────────────────┐
                    │       Python       │
                    └─────────┬──────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
             Tkinter     ttkbootstrap      aria2
               │              │              │
               └──────────────┼──────────────┘
                              │
                         Shusha app
                              │
                  ┌───────────┼───────────┐
                  │           │           │
                  ▼           ▼           ▼
               Models     Controller     Views
                  │           │
                  └─────┬─────┘
                        ▼
                   Persistence


Development Toolchain:

                 ┌──────────────────────┐
                 │          uv          │
                 │ dependencies/build  │
                 └──────────┬───────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           Ruff            ty            pytest
        lint/format       types           tests
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                         CI/CD
```

---

# 28. Definition of Success

The modernization succeeds when a new developer can clone Shusha, install its documented system dependencies, run:

```bash
uv sync
```

and immediately understand how to:

```bash
uv run shusha
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
uv run pytest --cov=shusha
uv build
```

The application should remain recognizably the same Shusha application.

The codebase should instead become:

* reproducible,
* typed,
* tested,
* linted,
* formatted,
* packaged,
* documented,
* CI-validated,
* security-reviewed,
* dependency-aware,
* easier to maintain.

The objective is **modern Shusha**, not **a different application called Shusha**.

---

# 29. Explicit Non-Goals

The following are explicitly outside the modernization scope unless separately approved:

* replacing Tkinter,
* replacing ttkbootstrap solely for aesthetic reasons,
* replacing aria2,
* rewriting the GUI,
* converting the project to async,
* introducing a web frontend,
* introducing a dependency injection framework,
* replacing the MVC-style architecture,
* rewriting persistence,
* rewriting the RPC protocol,
* adding unrelated features,
* redesigning the product,
* changing user workflows,
* gratuitous dependency replacement,
* optimizing code before correctness and tests are established.

---

# 30. Recommended First Execution

The first agent should be the Archaeologist.

After its report, the orchestrator should resolve the first concrete runtime decision:

```text
Which ttkbootstrap version/API should Shusha target?
```

Then establish the runtime baseline.

Only after that should the project undergo broad Ruff/ty modernization.

The safest sequence is:

```text
ARCHAEOLOGY
    ↓
RUNTIME RECOVERY
    ↓
PACKAGING/UV
    ↓
TEST FOUNDATION
    ↓
RUFF
    ↓
ty
    ↓
SECURITY
    ↓
CI/RELEASE
```

The project should remain runnable throughout the process whenever practical.

Every major change should have a corresponding test or explicit explanation for why a test is not practical.

---

# 31. Core Modernization Rule

> **Modernize the engineering system before modernizing the application architecture.**

The first objective is to make Shusha:

```text
installable
      ↓
runnable
      ↓
testable
      ↓
lintable
      ↓
type-checkable
      ↓
secure
      ↓
packagable
      ↓
reproducible
      ↓
CI-verifiable
```

Only after these foundations are stable should future feature development or architectural refactoring begin.
