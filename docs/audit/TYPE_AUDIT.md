# Type System & Static Typing Audit

> **Issue ID:** `P0-001` / `P0-002`  
> **Status:** `DONE`  
> **Type Checker:** `ty 0.0.72`  
> **Target Python:** Python 3.14+

---

## 1. Static Typing Findings & Diagnostics

- **`ty check` Status:** `0 errors` (All checks passed).
- **Modern Syntax Adoption:**
  - Codebase uses `|` union syntax (e.g. `str | None`).
  - Codebase uses built-in generic collections (`list[str]`, `dict[str, Any]`).
- **Typing Gaps & `Any` Policy Violations:**
  1. `dict[str, Any]` is heavily used as an escape hatch across `client.py`, `ws_client.py`, `api.py`, and `database.py`.
  2. Untyped dictionary payloads flow directly from aria2 RPC responses into UI widgets.
  3. No distinct `NewType` or typed identifiers for `GID`, `DownloadId`, `CategoryId`, `ProfileId`.
  4. Return types are missing or loosely annotated as `tuple` or `dict` in several helper methods in `utilities.py`.

---

## 2. Type System Goals for Shusha 2

- **Zero `Any` Policy:** All RPC responses and database rows must parse immediately into validated, typed dataclasses.
- **Dedicated Type Identifiers:** Introduce `type Gid = str`, `type DownloadId = str`, `type CategoryId = str`.
- **Value Objects:** `ByteSize`, `BitRate`, `Duration`, `Percentage`, `Checksum`.
