# ADR-004: Backend-Neutral Job and Artifact Domain Model

## Status
Accepted

## Context
Core entities in Shusha v1 were tightly coupled to aria2 data structures (e.g., GID, aria2 status strings). To serve as a universal download manager, domain primitives must be independent of any single backend.

## Decision
1. Introduce domain entities in `src/shusha/domain/`:
   - `Job`: Represents an execution unit with unique `JobId`, assigned `BackendId`, state (`QUEUED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `REMOVED`), progress, and options.
   - `Artifact`: Represents files, parts, or media streams produced by a job.
   - `JobGroup`: Aggregates related jobs (e.g., batch downloads, multi-format grabs).
2. Domain state transitions are immutable and validated via pure methods (e.g., `job.transition_to(DownloadState.ACTIVE)`).

## Consequences
- **Positive**: Strict type safety and complete isolation of core business rules from external RPC formats.
- **Positive**: Enables unified reporting across multi-backend transfers in UI and CLI.
