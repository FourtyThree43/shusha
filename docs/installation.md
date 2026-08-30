# Shusha 2 — Installation & Distribution Guide

## 1. Quick One-Liner Installers (Recommended)

### Linux & macOS (bash / curl)
```bash
curl -fsSL https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/FourtyThree43/shusha/main/scripts/install.ps1 | iex
```

The installer will:
1. Ensure the Astral `uv` toolchain is ready.
2. Install Shusha as a global tool.
3. Detect or install `aria2c` and `yt-dlp` acceleration engines.
4. Register the browser extension native messaging bridge and desktop launchers.

---

## 2. Python Package Installation (via `uv` or `pip`)

With Python 3.14+ installed:

```bash
# Using Astral uv (recommended)
uv tool install git+https://github.com/FourtyThree43/shusha.git

# Or standard pip
pip install git+https://github.com/FourtyThree43/shusha.git
```

---

## 3. Running Shusha

| Mode | Command | Behavior |
| :--- | :--- | :--- |
| **Default Invocation** | `shusha` | Launches **Desktop GUI** if graphical display is detected, otherwise falls back to **Textual TUI** |
| **Explicit Desktop GUI** | `shusha --gui` (or `shusha gui`, `shusha-gui`) | Forces launch of the ttkbootstrap desktop graphical interface |
| **Explicit Terminal TUI** | `shusha --tui` (or `shusha tui`, `shusha-tui`) | Forces launch of the Textual terminal user interface |
| **System Doctor Probes** | `shusha doctor` | Runs automated environment, backend, and health diagnostic checks |
| **Add Download** | `shusha add <URL_OR_MAGNET>` | Enqueues URL/magnet via the application CommandBus |
| **List Downloads** | `shusha list` (or `shusha --json list`) | Displays active/completed downloads in tabular or JSON format |
| **Browser Bridge Registration** | `shusha install-host` | Registers native messaging manifests for Chrome/Firefox/Edge/Brave |
| **Self-Update Check** | `shusha update` | Checks for updates and displays one-liner upgrade commands |

---

## 4. Standalone Binaries (PyInstaller Bundles)

You can package Shusha into standalone binaries (without requiring Python to be installed on target machines):

```bash
# Build single-file executables (dist/binaries/shusha, dist/binaries/shusha-gui)
python scripts/package_binaries.py --mode onefile

# Build standalone folder distributions
python scripts/package_binaries.py --mode onedir

# Build both
python scripts/package_binaries.py --mode both
```

Helper binaries (`aria2c` and `yt-dlp`) found in PATH are automatically bundled into the distribution directory.
