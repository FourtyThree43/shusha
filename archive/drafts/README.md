# Archive: UI Drafts & Early Iterations

This directory preserves early exploratory scripts and experimental Tkinter UI layouts developed during the initial design phase of Shusha.

---

## File Manifest

| File | Historical Purpose / Context |
| :--- | :--- |
| `main_window.py`, `main_window_2.py` | Early single-window Tkinter layouts exploring toolbar placement and basic table listings. |
| `status_window.py`, `status_window_2.py` | Prototypes of the download inspector and progress gauge windows (superseded by `src/shusha/views/status_win.py`). |
| `downloadlist_window.py` | Early experiments with Tkinter Treeview column bindings and sorting. |
| `tkbs_main_win.py`, `tkbs_add_win.py` | Initial exploration of `ttkbootstrap` themes and widgets (superseded by `src/shusha/views/app.py` and `src/shusha/views/add_win.py`). |
| `test_ii.py` – `test_vii.py` | Incremental sandboxes exploring event loops, background threads, and socket connections. |
| `test-gui_pack.py`, `test.py` | Monolithic sandbox scripts used for ad-hoc manual testing of layout geometry managers. |
| `chat.py` | Minimal experimental scratch script. |

---

> [!NOTE]
> All files in this directory are preserved strictly for historical reference. None of them are imported or used in the production `shusha` package or test suite.
