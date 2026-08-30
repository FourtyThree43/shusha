# Shusha 2 — Multi-Backend Download Acquisition & Orchestration Platform

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: ty](https://img.shields.io/badge/type%20checked-ty-brightgreen.svg)](https://github.com/astral-sh/ty)
[![Test Suite: pytest](https://img.shields.io/badge/tests-438%20passed-brightgreen.svg)](https://github.com/astral-sh/pytest)

**Shusha 2** is a multi-backend download acquisition and orchestration platform built in typed modern **Python 3.14**, featuring a **ttkbootstrap Desktop GUI**, a **Textual TUI / Operator Console**, a machine-readable **CLI**, an **Acquisition Platform & Browser Bridge**, and a **Sandboxed Plugin Architecture**.

---

## 🚀 Key Highlights

- **Multi-Backend Orchestration:**
  - **aria2 Reference Backend:** Multi-source BitTorrent, Magnet, Metalink, HTTP(S), FTP, SFTP, segmented downloads, local process supervision, and authoritative 198-option catalogue binding.
  - **yt-dlp Media Backend:** Non-destructive stream inspection, video/audio quality & format selection, playlist extraction, and subtitles.
  - **Pluggable Backend SDK:** Backend-neutral domain contracts, lifecycle state machine, and deterministic fake backend simulator.

- **Unified Acquisition Platform:**
  - Multi-input classification: Direct URLs, Magnet URIs, Torrent files, Metalink XML, Media streams, and batch ranges.
  - Safe payload inspector (HTTP HEAD, MIME, BitTorrent info-hash, Metalink mirrors).
  - Rule-based policy engine matching requests to backends based on capabilities.
  - Acquisition Inbox for reviewing, inspecting, accepting, and ignoring items.
  - Secure WebExtensions Native Messaging browser bridge for Chrome & Firefox.

- **Multiple Presentation Surfaces:**
  - **ttkbootstrap Desktop:** Theme-aware responsive UI (Compact, Standard, Wide, UltraWide), Dashboard cards, Download Workspace, Acquisition Inbox, Media Grabber dialog, and deep inspectors (Piece Map, Peers, Trackers, Servers, Speed Graphs).
  - **Textual TUI & Diagnostics (`shusha tui`):** Zero-flicker live job monitor, backend diagnostics dashboard, and system environment doctor (`shusha doctor`).
  - **CLI & Automation (`shusha ...`):** Tabular, structured `--json`, and streaming `--jsonl` outputs routing through typed `CommandBus` and `QueryBus`.

- **Sandboxed Plugin Architecture:**
  - Versioned plugin manifests with declared capabilities and permissions (`NETWORK`, `STORAGE`, `NOTIFICATIONS`, `CLIPBOARD`, `UI_EXTENSION`, `TRANSFORM`).
  - Isolated file & key-value storage with path traversal protection.
  - Typed extension points: `on_acquisition_detected`, `on_job_created`, `on_job_completed`, `on_job_failed`, `transform_url`, `filter_request`.

- **Strict Software Architecture & Quality:**
  - 100% Type-Safe Python 3.14 with `ty check` and Ruff.
  - Hexagonal / Clean architecture enforcing `Frontend -> Application -> Backend Contract -> Adapter` with architecture dependency validation tests.

---

## 🏛️ System Architecture

```text
       ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
       │   Desktop GUI (ttk)   │   │  Textual TUI (`tui`)  │   │  CLI / Automation     │
       └───────────┬───────────┘   └───────────┬───────────┘   └───────────┬───────────┘
                   │                           │                           │
                   └───────────────────┬───────┴───────────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Application Layer            │
                       │  • CommandBus & QueryBus      │
                       │  • JobLifecycleService        │
                       │  • Publish/Subscribe EventBus │
                       │  • Acquisition Inbox & Policy │
                       └───────────────┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ aria2 Reference       │  │ yt-dlp Backend        │  │ Plugin Architecture   │
│ • Process Supervisor  │  │ • Process Adapter     │  │ • Manifest & Sandbox  │
│ • JSON-RPC & XML-RPC  │  │ • Media Inspector     │  │ • Isolated Storage    │
│ • 198 Options Matrix  │  │ • Format Selection    │  │ • Typed Hook Manager  │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Domain Core (Neutral Models) │
                       │  • Job, Artifact, JobGroup    │
                       │  • AcquisitionRequest         │
                       │  • Capabilities & Events      │
                       └───────────────────────────────┘
```

---

## 📦 Installation & Setup

### ⚡ Quick One-Liner (Recommended)

**Linux & macOS**:
```bash
curl -fsSL https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.sh | bash
```

**Windows (PowerShell)**:
```powershell
irm https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.ps1 | iex
```

### Manual Development Setup
```bash
# Clone repository
git clone https://github.com/FourtyThree43/shusha.git
cd shusha

# Synchronize dependencies
uv sync
```

---

## 💻 Usage

| Target | Command | Description |
| :--- | :--- | :--- |
| **Default Invocation** | `shusha` | Launches **Desktop GUI** if display is present, else **Textual TUI** |
| **Explicit Desktop GUI** | `shusha --gui` (or `shusha gui`, `shusha-gui`) | Forces launch of the ttkbootstrap desktop UI |
| **Explicit Terminal TUI** | `shusha --tui` (or `shusha tui`, `shusha-tui`) | Forces launch of the Textual terminal interface |
| **System Diagnostics** | `shusha doctor` | Runs automated environment and backend health probes |
| **Add Download** | `shusha add <URL_OR_MAGNET>` | Enqueues URL/magnet via CommandBus |
| **List Downloads** | `shusha list` (or `shusha --json list`) | Displays active/completed jobs |
| **Browser Integration** | `shusha install-host` | Registers WebExtensions native messaging manifests |
| **Self-Update** | `shusha update` | Checks for latest GitHub release and shows upgrade commands |

# Add with custom options
uv run python -m shusha.main add https://example.com/file.zip --option dir=/tmp/downloads --option max-connection-per-server=8

# List active/queued jobs (tabular format)
uv run python -m shusha.main list

# List in machine-readable JSON
uv run python -m shusha.main list --json

# Stream in JSONL
uv run python -m shusha.main list --jsonl

# Inspect URL without starting download
uv run python -m shusha.main resolve https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Inspect system environment and backend diagnostics
uv run python -m shusha.main doctor
uv run python -m shusha.main diagnostics
```

---

## 🧪 Quality & Verification

Run the full validation suite:

```bash
# 1. Linting
uv run ruff check .

# 2. Code formatting
uv run ruff format --check .

# 3. Type checking
uv run ty check

# 4. Comprehensive tests
uv run pytest
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
