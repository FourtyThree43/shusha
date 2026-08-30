# ADR-005: Typed Event Architecture & Zero-Polling Updates

## Status
Accepted

## Context
High-frequency UI polling of backend daemons causes UI stuttering, high CPU usage, and network overhead. Frontends require instant notification of lifecycle changes (job started, progress changed, completed, failed).

## Decision
1. Implement a thread-safe, strongly typed `EventBus` in `src/shusha/application/event_bus.py`.
2. Define domain events (`JobCreatedEvent`, `JobStartedEvent`, `JobProgressChangedEvent`, `JobCompletedEvent`, `JobFailedEvent`, `AcquisitionDetectedEvent`, `PluginEvent`) in `src/shusha/domain/events.py`.
3. Frontends (`MainWindow`, `ShushaTUIApp`, `EventStream`) subscribe to the `EventBus` and update widgets incrementally without full-table destruction.

## Consequences
- **Positive**: Zero-flicker UI updates and low CPU overhead.
- **Positive**: Decoupled, testable event flows verifiable via `FakeBackend` and mock subscribers.
