# Shusha 2 Architecture Overview

Shusha 2 is designed following strict **Clean Architecture (Hexagonal Architecture)** principles, ensuring high maintainability, testability, and decoupling between business domain logic, external dependencies, and GUI presentation.

---

## 1. Architectural Layers & Boundaries

```text
┌─────────────────────────────────────────────────────────────┐
│                       Presentation                          │
│   (ttkbootstrap UI, ViewModels, BaseDialog, UiDispatcher)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ (calls use cases / observes state)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Application                          │
│   (Use Cases, SyncCoordinator, Scheduler, PostActions)      │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│            Domain            │ │       Infrastructure        │
│  (Entities, Aggregates,      │ │  (Aria2Client, Transports,  │
│   Value Objects, States)     │ │   Daemon, SQLite, Secrets)  │
└──────────────────────────────┘ └─────────────────────────────┘
```

---

## 2. Layer Responsibilities

### Domain (`src/shusha/domain/`)
- Pure Python 3.14 domain entities (`Download`, `DownloadFile`, `Category`).
- Strongly typed value objects (`ByteSize`, `BitRate`, `Duration`, `Percentage`, `Gid`, `DownloadId`).
- Finite state transition graphs with validation guards (`DownloadState`).
- Domain events and domain-level errors.
- Zero dependencies on external libraries (no GUI, no SQLite, no subprocess, no network).

### Application (`src/shusha/application/`)
- Orchestrates application use cases (`AddDownloadUseCase`, `PauseDownloadUseCase`, `ResumeDownloadUseCase`, `RemoveDownloadUseCase`, `InspectDownloadUseCase`, `ChangeDownloadOptionsUseCase`, `CreateCategoryUseCase`, `ReorderQueueUseCase`, `SetQueueLimitsUseCase`).
- Application services:
  - `SyncCoordinator`: Combines low-latency WebSocket push notifications and fallback polling.
  - `SchedulerService`: Time-windowed bandwidth throttling.
  - `ClipboardWatcherService`: Real-time clipboard pattern detection.
  - `PostActionService`: Cryptographic hash calculation and safe command execution.

### Infrastructure (`src/shusha/infrastructure/`)
- `aria2`: Authoritative Option Registry (198 options), wire parsers, typed `JsonRpcTransport`, `XmlRpcTransport`, `Aria2WebSocketClient`, and unified `Aria2Client`.
- `daemon`: Process supervisor, argument builder with secret redaction, binary discovery, and health probing.
- `persistence`: Versioned SQLite migrations, atomic transaction context managers, repository implementations.
- `configuration`: SQLite-backed typed settings store.
- `security`: `SecretStore` with `0600` file permissions and automated secret redaction utilities.
- `diagnostics`: System diagnostics bundle generator.
- `os_integration`: Linux FreeDesktop `.desktop` entry and MIME association installer.

### Presentation (`src/shusha/presentation/`)
- Built with `ttkbootstrap` (modern themes, responsive widgets).
- `UiDispatcher`: Thread-safe executor scheduling background tasks and returning results to Tk mainloop.
- `DownloadTable`: Virtualized, multi-column sortable table with context menus.
- Modals: `AddDownloadDialog`, `InspectorDialog`, `SettingsDialog`, `BatchAddDialog`, `CreateTorrentDialog`.
- `MainWindow`: Top-level window coordinating sidebar filters, toolbar, menu bar, and live status bar.
