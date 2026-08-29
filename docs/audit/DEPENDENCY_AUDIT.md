# Dependency Audit & Disposition Report

> **Issue ID:** `P0-005`  
> **Status:** `DONE`  
> **Toolchain:** Astral `uv`  
> **Target Python:** Python 3.14+

---

## 1. Direct Runtime Dependencies

| Package | Current Specifier | Purpose in Legacy Code | Evaluation & Security Assessment | Rewrite Disposition | Target Layer |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `ttkbootstrap` | `>=1.10.1` | Visual theme engine, modern widgets | Stable, pure Python wrapper over Tk/ttk; core GUI requirement | **KEEP** | `src/shusha/presentation/` |
| `platformdirs` | `>=4.1.0` | OS-specific cache, config, data paths | High quality, cross-platform standard library companion | **KEEP** | `src/shusha/infrastructure/os/` |
| `pillow` | `>=10.0.0` | Image loading, SVG bitmap conversion | Well-maintained, essential for image rendering in Tkinter | **KEEP** | `src/shusha/presentation/theme/` |
| `tomli` | `>=2.0.1; python_version < '3.11'` | TOML config parsing | Unneeded on Python 3.14 (Python stdlib includes `tomllib`) | **REMOVE** | Replaced by stdlib `tomllib` |

---

## 2. Development & Test Dependencies

| Package | Current Specifier | Purpose | Evaluation | Rewrite Disposition |
| :--- | :--- | :--- | :--- | :---: |
| `pytest` | `>=8.3.5` | Test framework | Standard Astral test toolchain | **KEEP** |
| `pytest-cov` | `>=5.0.0` | Code coverage reporting | Standard Astral test toolchain | **KEEP** |
| `coverage[toml]` | `>=7.6.1` | Coverage engine | Standard coverage backend | **KEEP** |
| `ruff` | `>=0.16.3` | Linter and code formatter | Fast Astral linter / formatter | **KEEP** |
| `ty` | `>=0.0.72` | Static type checker | Fast Astral type checker | **KEEP** |

---

## 3. Potential New Dependencies for Evaluation

- **`websockets` / `httpx`:** Evaluate whether stdlib `urllib.request` + `asyncio` or a lightweight typed client is preferred for aria2 JSON-RPC / WebSocket. (Note: `AGENTS.md` and `PLAN.md` require stdlib first where possible).
