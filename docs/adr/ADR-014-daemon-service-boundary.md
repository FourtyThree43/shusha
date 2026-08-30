# ADR-014: Local Daemon Process Supervision & Discovery

## Status
Accepted

## Context
Running `aria2c` requires process supervision, port binding, RPC secret tokens, process lifecycle management (start, stop, restart, crash recovery), and health probing.

## Decision
1. Implement `Aria2Supervisor` and `Aria2Discovery` in `src/shusha/infrastructure/daemon/`.
2. Automatic binary discovery on system PATH, environment variables, or bundled paths.
3. Cryptographically random ephemeral RPC token generation (`secrets.token_urlsafe(32)`).
4. Process health probe: Periodic RPC version ping with exponential backoff on connection retry.

## Consequences
- **Positive**: Zero manual configuration required from the user to start accelerated downloads.
- **Positive**: Clean shutdown of subprocesses on application exit without orphaned daemon processes.
