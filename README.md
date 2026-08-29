# Shusha 2 — Modern Desktop Download Manager

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: ty](https://img.shields.io/badge/type%20checked-ty-brightgreen.svg)](https://github.com/astral-sh/ty)

**Shusha 2** is a high-performance, modern desktop download manager powered by the [`aria2c`](https://aria2.github.io/) download engine and built with modern **Python 3.14** and **ttkbootstrap**.

---

## Key Features

- **Multi-Protocol Acceleration:** Blazing fast multi-connection downloads across HTTP, HTTPS, FTP, SFTP, BitTorrent, and Metalink.
- **Modern Clean Architecture:** Strict decoupling between Pure Domain, Application Use Cases, Infrastructure Adapters, and Presentation UI.
- **100% Type-Safe & Zero-`Any`:** Fully verified with `ty check` and modern Python 3.14 syntax.
- **Comprehensive aria2 Option Registry:** Complete machine-readable coverage for 198 aria2 options with progressive disclosure (Basic, Advanced, Expert).
- **Responsive ttkbootstrap GUI:** Theme-aware desktop UI with dark/light themes, virtualized download table, and deep inspection tabs (Files, Piece Map, Peers, Servers, Trackers, Options).
- **Integrated BitTorrent Engine:** Native `.torrent` file creator with pure Python piece hashing and bencoding.
- **Multi-URL Batch Ingestion:** Expressive range patterns (`[01-10]`, `[a-z]`) for queuing batch downloads.
- **Automation & Scheduling:** Clipboard link monitoring, bandwidth scheduling windows, and streaming cryptographic hash validation (MD5, SHA1, SHA256).
- **Process Supervision:** Robust local `aria2c` lifecycle management, health probing, and orphan adoption.
- **Full CLI:** Complete command-line interface for headless servers and automation.

---

## Architecture

```text
ttkbootstrap UI
      │
      ▼
Presentation (Views, Modals, Virtualized Tables, UiDispatcher)
      │
      ▼
Application (Use Cases, SyncCoordinator, Scheduler, PostActions)
      │
      ▼
Domain (Entities, Value Objects, States, Events)
      ▲
      │
Infrastructure (aria2 RPC, Process Supervisor, SQLite Migrations, Security)
```

---

## Installation & Quick Start

### Prerequisites
- Python 3.14+
- `aria2c` installed and on your system `PATH`
- `uv` (recommended)

```bash
# Clone repository
git clone https://github.com/FourtyThree43/shusha.git
cd shusha

# Synchronize environment
uv sync

# Run desktop GUI
uv run shusha

# Or run CLI commands
uv run shusha doctor
uv run shusha add https://example.com/file.zip
```

---

## Command Line Interface (CLI)

```bash
# Start desktop GUI
shusha gui

# Daemon management
shusha daemon start
shusha daemon status
shusha daemon stop

# Download management
shusha add https://example.com/file.iso --split 8
shusha add -t file.torrent
shusha list --state active
shusha pause <download-id>
shusha resume <download-id>
shusha remove <download-id> --delete-files

# Verify checksums
shusha hash file.iso

# System diagnostics
shusha doctor
```

---

## Testing & Quality Assurance

```bash
# Run linter & formatter
uv run ruff check .
uv run ruff format --check .

# Run static type checker
uv run ty check

# Run full test suite
uv run pytest

# Build release package
uv build
```

---

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [User Guide](docs/user_guide.md)
- [Contributing Guidelines](docs/development/contributing.md)
- [aria2 Specification Matrix](docs/aria2/01_options_matrix.md)
- [Legacy Parity Report](docs/audit/14_legacy_parity_report.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
