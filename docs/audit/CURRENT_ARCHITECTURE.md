# Current Architecture Audit & Coupling Analysis

> **Issue ID:** `P0-006`  
> **Status:** `DONE`  
> **Purpose:** Document the true architecture of the legacy codebase, highlight architectural flaws, circular couplings, and compare against the target Clean Architecture.

---

## 1. Actual Legacy Architecture Dependency Diagram

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              VIEWS LAYER                               │
│  views/app.py (1111 LOC God Object)                                    │
│  - Owns Tkinter Window + Tk mainloop                                   │
│  - Spawns polling threads (`after` / `Thread`)                         │
│  - Makes direct SQLite queries to `DatabaseManager`                    │
│  - Calls `ControllerAPI` directly                                      │
│  - Instantiates child modal windows directly                           │
└────────────┬─────────────────────────────┬─────────────────────────────┘
             │                             │
             ▼                             ▼
┌───────────────────────────┐ ┌──────────────────────────────────────────┐
│     CONTROLLER LAYER      │ │             DATABASE LAYER               │
│  controller/api.py        │ │  models/database.py                      │
│  (967 LOC Monolith)       │ │  - Raw SQLite connections                │
│  - Dispatches calls       │ │  - Direct table operations               │
│  - Holds singleton state  │ │  - Untyped tuple/dict conversions        │
└────────────┬──────────────┘ └──────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              MODELS LAYER                              │
│  models/client.py (XML-RPC)                                            │
│  models/ws_client.py (JSON-RPC / WebSockets)                           │
│  models/daemon.py (Subprocess aria2c)                                  │
│  models/logger.py (Import-time side-effects)                           │
│  models/structs_downloads.py (Loose Dataclasses)                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Identified Architectural Anti-Patterns & Flaws

1. **God-Object Views (`views/app.py`):**
   The view layer does not merely display data; it orchestrates business workflows, schedules timers, runs database writes, and handles error popups synchronously on the UI thread.
2. **Monolithic Proxy Controller (`controller/api.py`):**
   `ControllerAPI` is an unnecessary passthrough layer that hides domain logic rather than coordinating distinct use cases. It mixes download management, database persistence, settings, and daemon supervision into 967 lines.
3. **No Formal Domain Abstraction:**
   Downloads, Torrents, Queues, and Files exist only as loose dataclasses (`models/structs_downloads.py`) populated directly from XML-RPC dictionaries. No state machine enforces valid transitions (`STARTING -> ACTIVE -> PAUSED -> COMPLETED`).
4. **Scattered Database Access:**
   Both `views/app.py` and `controller/api.py` directly query `models/database.py`. There is no repository interface or separation between domain entities and database tables.
5. **Import-Time Side Effects:**
   `models/logger.py` creates filesystem directories when imported, violating test isolation and sandboxing rules.

---

## 3. Target Shusha 2 Clean Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                      │
│  ttkbootstrap UI, ViewModels, Components, Screens, Dialogs │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                      │
│  Commands, Queries, Application Services (DownloadService, │
│  QueueService, SchedulerService, SettingsService)          │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                         │
│  Download Entity, Value Objects (ByteSize, BitRate, GID),  │
│  State Machine, Category, Queue, Events, Invariants        │
└─────────────────────────────▲──────────────────────────────┘
                              │
┌─────────────────────────────┴──────────────────────────────┐
│                   INFRASTRUCTURE LAYER                     │
│  aria2 RPC Adapter (JSON-RPC/XML-RPC), Daemon Supervisor,   │
│  SQLite Repositories, Filesystem, OS Services              │
└────────────────────────────────────────────────────────────┘
```
