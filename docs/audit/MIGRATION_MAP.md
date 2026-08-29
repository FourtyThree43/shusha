# Shusha 2 — Migration Map & Component Traceability

> **Issue ID:** `P0-009`  
> **Status:** `DONE`  
> **Dependencies:** `P0-002` through `P0-008`  
> **Target Architecture:** Layered Clean Architecture

---

## 1. Architectural Component Migration Map

| Legacy Component / Module | Target Layer | New Shusha 2 Module | Migration Strategy | Key Improvements & Testing Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `src/shusha/models/structs_downloads.py` | **Domain** | `src/shusha/domain/download.py`<br>`src/shusha/domain/download_file.py`<br>`src/shusha/domain/states.py` | Re-architect into immutable domain entities with explicit state machine transitions. | Unit test all valid and invalid state transitions (`STARTING -> ACTIVE -> PAUSED -> COMPLETED`). |
| `src/shusha/models/structs_options.py` | **Infrastructure / Domain** | `src/shusha/domain/options.py`<br>`src/shusha/infrastructure/aria2/options/` | Replace partial dataclass with full `OptionRegistry` generated from authoritative `spec/aria2/options.json`. | Automated validation tests against all ~210 aria2 options. |
| `src/shusha/models/category_manager.py` | **Domain / Application** | `src/shusha/domain/category.py`<br>`src/shusha/application/services/categories.py` | Decouple category domain entity and matching rules from SQLite persistence. | Unit test rule evaluation and priority ordering in memory. |
| `src/shusha/models/scheduler.py` | **Domain / Application** | `src/shusha/domain/scheduler.py`<br>`src/shusha/application/services/scheduler.py` | Formalize schedule time windows as value objects; implement cron-like scheduler service. | Unit test time window intersections and schedule triggers. |
| `src/shusha/models/client.py` | **Infrastructure** | `src/shusha/infrastructure/aria2/xmlrpc/` | Pure XML-RPC transport adapter translating RPC responses into typed domain entities. | Integration tests against mock server and live aria2 daemon. |
| `src/shusha/models/ws_client.py` | **Infrastructure** | `src/shusha/infrastructure/aria2/jsonrpc/` | Robust JSON-RPC / WebSocket adapter with automatic reconnection and heartbeat. | Unit test protocol serialization, event dispatching, and error handling. |
| `src/shusha/models/daemon.py` | **Infrastructure** | `src/shusha/infrastructure/daemon/` | Supervised daemon lifecycle with health checks, PID tracking, and graceful shutdown. | Integration test process supervision, crash recovery, and restart. |
| `src/shusha/models/database.py` | **Infrastructure** | `src/shusha/infrastructure/persistence/` | Repository pattern (`DownloadRepository`, `HistoryRepository`) with versioned SQLite migrations. | Integration test migration sequence and SQL query correctness. |
| `src/shusha/models/logger.py` | **Telemetry / Security** | `src/shusha/telemetry/logging.py`<br>`src/shusha/security/redaction.py` | Structured logging with mandatory secret redaction (tokens, passwords) and lazy directory creation. | Unit test secret redaction on sensitive strings and URLs. |
| `src/shusha/controller/api.py` | **Application** | `src/shusha/application/services/downloads.py`<br>`src/shusha/application/services/queue.py`<br>`src/shusha/application/services/reconciliation.py` | Split 967-line god object into focused application use-case services. | Unit test each service independently with mocked repositories. |
| `src/shusha/views/app.py` | **Presentation** | `src/shusha/presentation/app.py`<br>`src/shusha/presentation/screens/dashboard/`<br>`src/shusha/presentation/screens/downloads/` | Break monolithic view into `ShushaApplication` root, `ScreenHost`, and dedicated ViewModels. | Headless ViewModel unit testing with zero Tkinter GUI dependencies. |
| `src/shusha/views/inspector_win.py` | **Presentation** | `src/shusha/presentation/screens/inspector/` | Modular inspector with tabs (Overview, Files, Peers, Servers, Trackers, Options, Hashes, Logs). | Test inspector state binding and live refresh. |
| `src/shusha/views/settings_win.py` | **Presentation** | `src/shusha/presentation/screens/settings/` | Multi-category settings screen with Basic / Advanced / Expert progressive disclosure. | Test settings validation, option search, and dirty state tracking. |
