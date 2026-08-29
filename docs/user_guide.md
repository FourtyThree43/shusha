# Shusha 2 User Guide

Shusha is a high-performance desktop download manager built on top of `aria2c`.

---

## 1. Graphical User Interface (GUI)

### Starting the GUI
Launch Shusha from your application launcher or run:

```bash
shusha
# or explicitly:
shusha gui
```

### Adding Downloads
- **Single URL / Magnet Link:** Click `+ Add URL` (or `Ctrl+N`), enter the link, select download directory and category.
- **Torrent / Metalink File:** Click `+ Add Torrent` (or `Ctrl+O`) to load `.torrent` / `.metalink` files.
- **Batch URLs:** From the menu select `File -> Batch Add URLs...` (or `Ctrl+B`). Supports range patterns such as:
  - `https://example.com/files/archive_[01-10].zip`
  - `ftp://mirror.org/chunk_[a-d].iso`

### Inspecting Downloads
Double-click any download or right-click and choose **Inspect** to open the multi-tab inspector:
- **General:** Progress, size, speeds, ETA, file paths.
- **Files:** Individual file completion and priority selection.
- **Piece Map:** Visual bitfield canvas displaying downloaded vs. missing pieces.
- **Peers:** Live BitTorrent peer IP, choking state, throughput.
- **Servers:** Mirror connections and speeds.
- **Options:** Download-scoped aria2 option modifier.

### Creating BitTorrent Files
From the menu select `File -> Create Torrent...` to generate `.torrent` files with custom piece sizes, tracker lists, and comments.

---

## 2. Command-Line Interface (CLI)

Shusha includes a full-featured CLI:

```bash
# Daemon Management
shusha daemon start
shusha daemon status
shusha daemon stop

# Adding Downloads
shusha add https://example.com/file.zip --dir ~/Downloads --split 8
shusha add -t /path/to/archive.torrent

# Listing Downloads
shusha list
shusha list --state active --format json

# Controlling Tasks
shusha pause dl-123
shusha pause --all
shusha resume dl-123
shusha remove dl-123 --delete-files

# Computing Hashes
shusha hash ~/Downloads/ubuntu.iso

# System Diagnostics
shusha doctor
shusha doctor --json

# Desktop Integration
shusha install-desktop
```
