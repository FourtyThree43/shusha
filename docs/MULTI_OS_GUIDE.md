# Shusha Multi-OS Platform Integration Guide

Shusha is designed to feel native and behave consistently across **Linux**, **macOS**, and **Windows**.

---

## Platform-Specific Integrations

| Feature | Linux (Wayland / X11) | macOS (Darwin) | Windows 10 / 11 |
| :--- | :--- | :--- | :--- |
| **System Notifications** | `notify-send` / Freedesktop D-Bus | `osascript` Notification Center | Windows Toast API / PowerShell |
| **File Manager Reveal** | `xdg-open` / `gio open` | `open -R <file>` (Finder reveal) | `explorer.exe /select,<path>` |
| **System Tray** | AppIndicator / SNI Tray | macOS Menu Bar Extra | System Notification Area Tray |
| **High-DPI Scaling** | Dynamic Wayland scaling | Retina `@2x` vector scaling | Windows Per-Monitor DPI Aware |
| **Default Download Dir** | `~/Downloads` | `~/Downloads` | `%USERPROFILE%\Downloads` |
| **Configuration Path** | `~/.config/shusha/config.toml` | `~/Library/Application Support/shusha/config.toml` | `%APPDATA%\shusha\config.toml` |

---

## Verifying Desktop Integration

### Linux
```bash
# Test desktop notification
notify-send "Shusha" "Download Finished"
# Test file manager reveal
xdg-open /home/$USER/Downloads
```

### macOS
```bash
# Test notification
osascript -e 'display notification "Download Finished" with title "Shusha"'
# Test Finder reveal
open -R ~/Downloads
```

### Windows (PowerShell)
```powershell
explorer.exe /select,"$HOME\Downloads"
```
