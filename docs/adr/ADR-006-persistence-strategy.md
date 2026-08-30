# ADR-006: SQLite Persistence Strategy with WAL Mode & Repository Interfaces

## Status
Accepted

## Context
User job history, categories, credentials, and settings must persist across application restarts with zero risk of database corruption during concurrent operations or crashes.

## Decision
1. Use SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and synchronous normal mode for high-throughput persistence.
2. Abstract all database access behind typed repository protocols:
   - `JobRepository`
   - `ArtifactRepository`
   - `JobGroupRepository`
   - `CategoryRepository`
   - `SettingsRepository`
   - `CredentialRepository`
3. Manage schema evolution through versioned migrations (`v1 -> v2`) in `src/shusha/infrastructure/persistence/migrations.py`. Domain entities never execute raw SQL directly.

## Consequences
- **Positive**: Atomic transactions and crash-resilient storage.
- **Positive**: Deterministic testability through in-memory SQLite instances (`:memory:`).
