# Shusha (Shusha-DM)

![Repo size](https://img.shields.io/github/repo-size/FourtyThree43/shusha)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![License](https://img.shields.io/badge/license-MIT-blue)

**Shusha** (*Swahili for "Download"*) is a fast, modern download manager that wraps around [aria2](https://aria2.github.io/), a high-performance multi-protocol and multi-source download utility. Shusha provides a modern graphical user interface built with Tkinter and ttkbootstrap, coupled with a robust Model-View-Controller (MVC) engine and automatic local aria2 daemon lifecycle orchestration.

---

## Features

- **Multi-Protocol Power**: HTTP/HTTPS, FTP, SFTP, BitTorrent (`.torrent`), and Metalink (`.metalink`).
- **Segmented Acceleration**: Multi-connection downloads with configurable chunk splitting and speed throttles.
- **Selective File Downloads**: Inspect files inside multi-file torrents and toggle individual file downloads.
- **Queue & Task Control**: Start Queue, Pause Queue, Clear Queue, reorder tasks, and filter by status (*All*, *Active*, *Completed*, *Paused*, *Waiting*, *Error*, *Inactive*).
- **Table Context Menu**: Right-click actions to Resume, Pause, Remove, Delete files, Open containing directory, and copy download info.
- **Desktop Notifications & Tray**: Native OS notifications on download completion/failure and background tray minimization.
- **Graphical Settings Modal**: Configure download folders, connection limits, speed caps, themes, and aria2 RPC options with native TOML persistence.
- **Integrated Daemon Supervision**: Automatic discovery, startup, health monitoring, and shutdown of local `aria2c` processes.
- **Modern Tooling & Zero-Bloat**: Built with Astral `uv`, `ruff`, and `ty` type checking.

---

## Quick Start

### Prerequisites

1. **Python 3.10+**
2. **aria2** (`aria2c` binary installed on system PATH, e.g. via `apt install aria2`, `dnf install aria2`, or `brew install aria2`).
3. **Tkinter** (`python3-tk` or `python3-tkinter`).
4. **uv** package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/)).

### Installation & Execution

Clone the repository and run using `uv`:

```bash
# Clone the repository
git clone https://github.com/FourtyThree43/shusha.git
cd shusha

# Sync virtual environment and dependencies
uv sync

# Launch Shusha GUI
uv run shusha
# Or launch as module:
uv run python -m shusha
```

---

## Development & Quality Assurance

Shusha uses the Astral toolchain for blazing-fast development, linting, typechecking, and testing:

```bash
# Run complete test suite with coverage report
uv run pytest --cov=shusha --cov-report=term-missing

# Lint codebase with Ruff
uv run ruff check .

# Check code formatting with Ruff
uv run ruff format --check .

# Run static type checking with ty
uv run ty check

# Build distribution wheel and sdist
uv build
```

---

## Releasing & Publishing

Automated GitHub Releases and PyPI publication run via GitHub Actions on Git tag push:

```bash
# Create and push a release tag
git tag v0.1.0
git push origin v0.1.0
```

The workflow automatically validates the codebase across Python versions, builds distribution packages (`.whl` and `.tar.gz`), generates GitHub Release notes, and publishes to PyPI.

---

## Architecture & Project Layout

```
shusha
├── src
│   └── shusha
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point (python -m shusha)
│       ├── ShushaDM.py          # GUI application launcher
│       ├── models               # Model Layer
│       │   ├── client.py        # XML-RPC client for aria2
│       │   ├── daemon.py        # Process supervision & daemon lifecycle
│       │   ├── database.py      # Shelve-based NoSQL persistence
│       │   ├── logger.py        # Rotating file & console logging service
│       │   ├── settings.py      # TOML configuration manager
│       │   ├── structs_downloads.py # Typed Download & BitTorrent models
│       │   ├── structs_options.py   # Dynamic aria2 option mapping
│       │   ├── structs_stats.py     # Download stats & speed models
│       │   └── utilities.py     # Unit formatters, paths, & notifications
│       ├── views                # View Layer (Tkinter / ttkbootstrap)
│       │   ├── app.py           # Main window with download table & toolbar
│       │   ├── add_win.py       # Add URIs / Torrents modal dialog
│       │   ├── settings_win.py  # Graphical Settings modal
│       │   ├── status_win.py    # Download status meter dialog
│       │   └── torrent_win.py   # Multi-file selective download inspector
│       ├── controller           # Controller Layer
│       │   └── api.py           # ShushaAPI high-level orchestrator
│       └── resources            # UI Assets & icons
├── archive                      # Archived legacy drafts & sandbox experiments
├── tests                        # Comprehensive unit test suite (64 tests)
└── pyproject.toml               # PEP 621 packaging metadata
```

---

## License

This project is licensed under the MIT License — see the [LICENSE.txt](LICENSE.txt) file for details.
