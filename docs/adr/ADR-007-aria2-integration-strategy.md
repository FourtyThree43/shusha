# ADR-007: 198-Option aria2 Integration Strategy & RPC Matrix

## Status
Accepted

## Context
`aria2c` has a rich feature set comprising 198 CLI options and 22 JSON-RPC/WebSocket methods. Previous implementations only exposed a small subset of aria2 flags, leading to dropped options or incomplete configuration control.

## Decision
1. Compile an authoritative machine-readable specification in `spec/aria2/options.json` and `docs/aria2/option-matrix.md` capturing all 198 options (type, default, scope, mutability, protocol applicability, security implications).
2. Implement `Aria2Backend(BackendProtocol)` in `src/shusha/backends/aria2/`:
   - `adapter.py`: Translates backend-neutral commands into JSON-RPC / WebSocket payloads.
   - `supervisor.py`: Automates binary discovery, daemon lifecycle management, and RPC secret generation.
   - `options.py`: Validates and binds options against the 198-option catalogue.

## Consequences
- **Positive**: Complete compliance with official aria2c contract without dropped or unvalidated options.
- **Positive**: Safe secret handling without storing unencrypted RPC tokens in plain text.
