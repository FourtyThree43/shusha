# ADR-009: Sandboxed Plugin Architecture & Permission Grants

## Status
Accepted

## Context
Extending Shusha with third-party extractors, notification handlers, and storage integrations must not compromise user system security, credentials, or filesystem integrity.

## Decision
1. Plugins declare a structured `PluginManifest` with `id`, `version`, `api_version`, `capabilities`, and required `permissions` (`NETWORK`, `STORAGE`, `NOTIFICATIONS`, `CLIPBOARD`, `UI_EXTENSION`, `TRANSFORM`).
2. Implement sandboxed execution boundary (`src/shusha/plugins/sandbox.py`) and permission validator (`PluginPermissionValidator`).
3. Plugins access isolated storage directories and hook into extension points (`on_acquisition_detected`, `on_job_created`, `on_job_completed`, `transform_url`) through `PluginHookManager`. Unrestricted process or raw filesystem access is denied.

## Consequences
- **Positive**: Strict permission auditing and clear security boundaries for community extensions.
- **Positive**: Isolated plugin crashes cannot crash the main orchestrator process.
