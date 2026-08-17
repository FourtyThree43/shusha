# Shusha (Shusha-DM)

![Repo size](https://img.shields.io/github/repo-size/FourtyThree43/shusha)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![License](https://img.shields.io/badge/license-MIT-blue)

**Shusha** (*Swahili for "Download"*) is a fast, modern download manager that wraps around [aria2](https://aria2.github.io/), a high-performance multi-protocol and multi-source download utility. Shusha provides a graphical user interface (GUI) built with Tkinter and ttkbootstrap, coupled with a robust Model-View-Controller (MVC) engine and automatic local aria2 daemon lifecycle orchestration.

---

## Features

- **Multi-Protocol Power**: HTTP/HTTPS, FTP, SFTP, BitTorrent, and Metalink.
- **Segmented Acceleration**: Multi-connection downloads with configurable chunk splitting.
- **Queue & Task Control**: Pause, resume, retry, reorder, and remove download tasks.
- **Live Metrics**: Real-time download/upload speed meters, progress bars, and ETA calculations.
- **Integrated Daemon Supervision**: Automatic discovery, startup, health monitoring, and shutdown of local `aria2c` processes.
- **Modern Packaging & Tooling**: Built with Astral `uv`, `ruff`, and `ty` type checking.

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
│       │   ├── db.py            # SQLite relational task history
│       │   ├── logger.py        # Rotating file & console logging service
│       │   ├── settings.py      # TOML configuration manager
│       │   ├── structs_downloads.py # Typed Download & BitTorrent models
│       │   ├── structs_options.py   # Strongly typed aria2 option structs
│       │   ├── structs_stats.py     # Download stats & speed models
│       │   └── utilities.py     # Unit formatters & path resolution
│       ├── views                # View Layer (Tkinter / ttkbootstrap)
│       │   ├── app.py           # Main window with download table & toolbar
│       │   ├── add_win.py       # Add URIs / Torrents modal dialog
│       │   └── status_win.py    # Download status meter dialog
│       ├── controller           # Controller Layer
│       │   └── api.py           # ShushaAPI high-level orchestrator
│       └── resources            # Assets, icons, and themes
├── tests                        # Comprehensive Pytest suite
│   ├── test_client.py
│   ├── test_controller_api.py
│   ├── test_daemon.py
│   ├── test_database.py
│   ├── test_db.py
│   ├── test_gui_smoke.py
│   ├── test_logger.py
│   ├── test_query_syntax.py
│   ├── test_security.py
│   ├── test_settings.py
│   ├── test_structs.py
│   └── test_utilities.py
├── .github/workflows/ci.yml     # Multi-platform GitHub Actions CI
├── pyproject.toml               # PEP 621 / UV configuration
└── README.md
```

---

## License

`shusha` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

---

## About Shusha

Shusha (*Swahili for "download"*) was created to celebrate the beauty and vibrancy of East Africa while providing a powerful, reliable download manager for everyone.

*Asante sana! (Thank you very much!)*
