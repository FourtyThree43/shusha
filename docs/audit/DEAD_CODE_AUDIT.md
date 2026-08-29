# Dead Code & Obsolete Artifacts Audit

> **Issue ID:** `P0-008`  
> **Status:** `DONE`  
> **Purpose:** Identify unused modules, obsolete drafts, duplicate files, and experimental code without premature deletion.

---

## 1. Dead Code & Obsolete Files Inventory

| Path | LOC / Size | Category | Evidence of Dead / Obsolete Status | Rewrite Action / Recommendation |
| :--- | :---: | :--- | :--- | :--- |
| `archive/drafts/` (20 files) | ~3,500 LOC | Legacy Drafts | Old experimental Tkinter scripts (`test.py`, `chat.py`, `tkbs_main_win.py`) preserved during initial prototyping. | Keep in `archive/` for reference; do not import. |
| `archive/ray/` (26+ files) | ~2,000 LOC | Legacy UI Experiment | Early CustomTkinter / Tkinter experiment with custom PNG assets. | Keep in `archive/` for reference. |
| `src/shusha/models/db.py` | 31 LOC | Duplicate Module | Superseded by `src/shusha/models/database.py`. Contains obsolete dummy `Database` class. | Marked for **REMOVAL** during legacy transition. |
| `src/shusha/views/status_win.py` | 400 LOC | Obsolete View | Superseded by `views/inspector_win.py`. | Marked for **REMOVAL** once Inspector parity is verified. |
| `src/shusha/views/uri_win.py` | 142 LOC | Obsolete View | Simple URI display window superseded by inspector sources tab. | Marked for **REMOVAL** once Inspector parity is verified. |
| `src/shusha/TODO.md` | 10 LOC | Legacy Scratchpad | Outdated notes replaced by formal `PLAN.md`. | Keep or archive. |
