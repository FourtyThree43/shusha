# Phase 0 Audit — Baseline Findings & Reproducibility Report

> **Issue ID:** `P0-001`  
> **Status:** `DONE`  
> **Date:** 2026-08-29  
> **Target Architecture:** Layered Clean Architecture (Domain / Application / Infrastructure / Presentation)  
> **Authoritative Guides:** `AGENTS.md`, `PLAN.md`

---

## 1. System & Environment Baseline

| Attribute | Measured Value |
| :--- | :--- |
| **Git Branch** | `feature/epic-0-audit` (branched from `dev`) |
| **Base Commit** | `eb403dd` (*docs: overhaul website, documentation, and web UI in Ruby-lang aesthetic*) |
| **Python Version** | `Python 3.14.7` (CPython Linux x86_64) |
| **Astral uv Version** | `uv 0.6.5` |
| **aria2c Engine** | `aria2c version 1.37.0` (Features: Async DNS, BitTorrent, Firefox3 Cookie, GZip, HTTPS, Message Digest, Metalink, XML-RPC, SFTP) |
| **Operating System** | Linux (Fedora / generic Linux kernel 6.6+) |
| **Dependency Lock State** | `uv.lock` is up-to-date and consistent with `pyproject.toml` |

---

## 2. Toolchain Baseline Commands & Results

| Toolchain Command | Exit Code | Result Status | Detailed Findings |
| :--- | :---: | :---: | :--- |
| `uv sync` | `0` | **PASS** | Dependencies resolved cleanly into virtual environment. |
| `uv run ruff check .` | `0` | **PASS** | Linting passes with 0 rule violations under current rules (`E, F, I, UP, B, SIM, RUF`). |
| `uv run ruff format --check .` | `1` | **FAIL** | 41 files require formatting; 58 files formatted. |
| `uv run ty check` | `0` | **PASS** | Type checker reports zero diagnostics under current type rules. |
| `uv run pytest` (Headless CI) | `1` | **PARTIAL PASS / EXPECTED FAIL** | 157 passed, 9 skipped, 1 failed (`test_gui_smoke.py` fails when `$DISPLAY` is absent). |
| `uv run pytest --cov=shusha` | `1` | **MEASURED** | Overall project statement coverage: **56%** (2072 missed out of 5033 statements). |
| `uv build` | `0` | **PASS** | Wheel (`shusha-0.0.1-py3-none-any.whl`) and sdist successfully built. |

---

## 3. Test & Coverage Baseline Breakdown

| Package / Module Group | Total Statements | Missed Statements | Branch Coverage | Total Coverage |
| :--- | :---: | :---: | :---: | :---: |
| `src/shusha/models/` (Services/Models) | 2,058 | 519 | 74% | **75%** |
| `src/shusha/controller/` (API proxy) | 398 | 72 | 81% | **81%** |
| `src/shusha/views/` (Tkinter UI) | 2,401 | 1,457 | 18% | **22%** |
| `src/shusha/cli.py` (CLI interface) | 170 | 52 | 65% | **65%** |
| **Total Codebase** | **5,033** | **2,072** | **56%** | **56%** |

---

## 4. Key Phase 0 Baseline Observations & Risks

1. **Import-Time Side Effects (`models/logger.py`):**
   `LoggerService` automatically attempted to create `~/.local/state/shusha/log` during module import time (`logger = LoggerService(__name__)` at top-level). In isolated or read-only test environments, this caused collection errors unless `XDG_STATE_HOME` / `TMPDIR` were explicitly redirected.
   *Resolution for Shusha 2:* Decouple logging configuration from module import; inject logger or configure handlers at application startup.

2. **Headless Execution Failure (`views/app.py` & `tests/test_gui_smoke.py`):**
   Tkinter UI widgets directly invoke `tk.Tk()` or `ttkbootstrap.Window()` during instantiation, causing tests to fail when no X11/Wayland display server is available.
   *Resolution for Shusha 2:* Decouple presentation state (ViewModels) from Tkinter widget trees so view models can be 100% unit-tested headlessly.

3. **High UI / Business Logic Coupling:**
   `views/app.py` contains 1,111 lines of code managing downloads, background polling threads, SQLite transactions, notifications, and menu handling in a single monolithic class.
   *Resolution for Shusha 2:* Move all business logic, queue management, and persistence into `application/` and `domain/`.

4. **Codebase Size Summary:**
   - Source Code: 42 modules, 10,182 Lines of Code.
   - Tests: 37 test files, 167 test cases, 2,841 Lines of Code.
   - Archive Code: 76 files (legacy Ray GUI and Tkinter drafts in `archive/`).
