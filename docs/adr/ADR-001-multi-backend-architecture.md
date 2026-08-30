# ADR-001: Multi-Backend Architecture & Backend Protocol

## Status
Accepted

## Context
Shusha was originally constructed as a direct wrapper around `aria2c`. To accommodate modern acquisition workflows (video streaming via `yt-dlp`, BitTorrent acceleration via `aria2c`, direct HTTP mirrors, and future third-party engine plugins), the core architecture must decouple execution backends from application logic.

## Decision
1. Define a backend-neutral `BackendProtocol` in `src/shusha/domain/capability.py` and `src/shusha/backends/contract.py`.
2. Every execution engine implements `identity`, `capabilities`, `submit_job`, `pause_job`, `resume_job`, `cancel_job`, `remove_job`, `get_job_status`, `get_diagnostics`, and `get_supported_options`.
3. Application services interact with backends exclusively through `BackendRegistry` and backend-neutral protocols. Direct frontend-to-backend RPC or process invocations are strictly forbidden.

## Consequences
- **Positive**: New download engines (e.g., yt-dlp, IPFS, curl) can be integrated without modifying the domain model or UI layers.
- **Positive**: Frontends can be thoroughly tested against deterministic `FakeBackend` without external daemon dependencies.
- **Trade-off**: Backend-specific features must be modeled as capabilities or extension option dictionaries.
