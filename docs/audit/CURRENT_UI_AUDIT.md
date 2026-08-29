# Current UI Audit & Screen Analysis

> **Issue ID:** `P0-006`  
> **Status:** `DONE`  
> **UI Stack:** Tkinter + ttk + ttkbootstrap  
> **Total View Modules:** 11 files (2,401 LOC)

---

## 1. View Inventory & State Analysis

| View Module | LOC | UI Role / Responsibility | Key Widgets Used | Handled States | Missing States | Target Replacement |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `views/app.py` | 1,111 | Main application window | `ttk.Treeview`, `ttk.Notebook`, Toolbar, Menus | Ready, Busy | Loading, Empty, Offline, Error, No Selection | `presentation/app.py` & `screens/` |
| `views/add_win.py` | 250 | Single URL download dialog | `ttk.Entry`, `ttk.Combobox`, `ttk.Checkbutton` | Ready | Input Validation Errors, Testing Connection | `presentation/dialogs/add_download.py` |
| `views/batch_add_win.py` | 160 | Batch URL text input dialog | `tk.Text`, `ttk.Button` | Ready | Parse Progress, Empty Text, URL Error Preview | `presentation/dialogs/batch_add.py` |
| `views/checksum_win.py` | 167 | Hash verifier dialog | `ttk.Entry`, `ttk.Combobox`, `ttk.Progressbar` | Ready, Calculating | File Read Permission Denied, Corrupted File | `presentation/dialogs/checksum.py` |
| `views/create_torrent_win.py` | 165 | Torrent creator dialog | `ttk.Entry`, `ttk.Treeview`, `ttk.Progressbar` | Ready, Building | Out of Disk Space, Path Traversal Error | `presentation/dialogs/torrent.py` |
| `views/inspector_win.py` | 303 | Download details inspector | `ttk.Notebook`, `ttk.Treeview`, `tk.Canvas` | Ready | Download Removed Concurrently, Loading Tabs | `presentation/screens/inspector/` |
| `views/piece_map.py` | 126 | Torrent piece bitfield visualizer | `tk.Canvas` | Ready | Zero Pieces, Huge Bitfield Scaling | `presentation/widgets/piece_map.py` |
| `views/settings_win.py` | 657 | Multi-tab settings dialog | `ttk.Notebook`, `ttk.Entry`, `ttk.Spinbox` | Ready | Invalid Option Warning, Unsaved Changes Prompt | `presentation/screens/settings/` |
| `views/speed_graph.py` | 140 | Real-time transfer speed graph | `tk.Canvas` | Ready | Zero Throughput Flatline, High-DPI Rescaling | `presentation/widgets/speed_graph.py` |
| `views/status_win.py` | 400 | Legacy status window | `ttk.Treeview`, `ttk.Label` | Ready | Obsolete | Merged into Inspector |
| `views/torrent_win.py` | 216 | Torrent file inspector & file selector | `ttk.Treeview`, `ttk.Checkbutton` | Ready | Corrupted .torrent metadata | `presentation/dialogs/torrent.py` |
| `views/uri_win.py` | 142 | Legacy URI editor dialog | `ttk.Entry`, `ttk.Listbox` | Ready | Obsolete | Merged into Source Editor |

---

## 2. Key UI Deficiencies & UX Gaps

1. **Absence of Standard UI States:**
   Virtually every current screen only implements the "Happy Path / Ready" state. There are no consistent Empty States (e.g. "No downloads in queue"), Loading Spinners, or Inline Error Banners.
2. **No Centralized Design Token System:**
   Spacing, padding, font sizes, and borders are hardcoded numbers (`padx=5, pady=5`) throughout widget definitions.
3. **Color-Only State Indicators:**
   Some statuses rely purely on text colors without complementary icons, violating accessibility guidelines.
