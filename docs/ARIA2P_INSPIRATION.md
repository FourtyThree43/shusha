# Architectural Patterns & Inspiration from aria2p

This document outlines key design patterns and insights derived from [aria2p](https://github.com/pawamoy/aria2p) to inform the continuous evolution and architectural refinement of **Shusha-DM**.

---

## 1. Clean RPC Client Abstraction

In `aria2p`, client operations are split cleanly between low-level JSON-RPC protocol execution and high-level domain models (`Download`, `File`, `Option`, `Stats`).

### Key Insights:
- **Separation of Raw RPC from Domain Objects**: Raw RPC responses return string maps; converting these immediately into strongly-typed dataclasses with parsing logic for byte sizes, time deltas, and state flags simplifies presentation layers.
- **Fail-Safe Client Calls**: Network RPC calls can fail due to temporary network blips or daemon restarts. Encapsulating RPC calls with clear fallback defaults prevents GUI crashes.

---

## 2. Dynamic Option Management

Options in aria2 have different scopes:
1. **Daemon-wide / Global Options** (`getGlobalOption` / `changeGlobalOption`): e.g. `max-overall-download-limit`, `max-concurrent-downloads`.
2. **Download-specific Options** (`getOption` / `changeOption`): e.g. `max-download-limit`, `dir`, `select-file`.
3. **Startup-only Options**: Options that cannot be modified after daemon boot (e.g. `rpc-listen-port`, `enable-rpc`).

### Shusha Architecture Alignment:
- Shusha stores user configuration in TOML via `AppSettings`.
- Live options are dynamically pushed to the running aria2 daemon via `ShushaAPI.set_options()` and `ShushaAPI.set_global_options()`, ensuring instant reactivity without requiring restart.

---

## 3. Event-Driven Lifecycle vs Polling

While standard XML-RPC requires client-side interval polling (e.g. every 1 second), aria2's WebSocket protocol supports asynchronous notifications:
- `aria2.onDownloadStart(event)`
- `aria2.onDownloadPause(event)`
- `aria2.onDownloadStop(event)`
- `aria2.onDownloadComplete(event)`
- `aria2.onDownloadError(event)`
- `aria2.onBtDownloadComplete(event)`

### Recommendation:
For the upcoming Phase 3 architecture, implementing an optional `WebSocketListener` thread that listens for these events will allow instant UI updates and OS notifications with zero polling overhead.
