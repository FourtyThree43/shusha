# Security Audit & Risk Assessment Report

> **Issue ID:** `P0-007`  
> **Status:** `DONE`  
> **Scope:** Secrets handling, subprocess execution, path traversal, networking, webhooks, and permissions.

---

## 1. Security Findings Inventory

| ID | Finding Title | Location | Severity | Risk Description | Remediation & Target Disposition |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **SEC-01** | **Unredacted RPC Secret in Logging** | `src/shusha/models/daemon.py:95`, `models/client.py:45` | **HIGH** | The aria2 RPC secret token (`--rpc-secret=...`) may be logged in plaintext in diagnostic logs. | Implement mandatory secret redaction filter in `telemetry/logging.py`. |
| **SEC-02** | **Unauthenticated Local Webhook Server** | `src/shusha/models/webhook_server.py:55` | **HIGH** | Webhook server binds to `127.0.0.1:6810` accepting POST requests to add downloads without any token/secret authentication. Any local process or webpage via CORS/DNS rebinding could trigger downloads. | Introduce shared token authentication and strict CORS header enforcement in `infrastructure/networking/webhook.py`. |
| **SEC-03** | **Potential Path Traversal in Download Directories** | `src/shusha/models/utilities.py:350`, `models/batch_parser.py:90` | **MEDIUM** | Filenames and destination paths supplied from remote headers or user input are not fully validated against path traversal (`../`) or reserved characters. | Enforce strict defensive path resolution via `security/paths.py`. |
| **SEC-04** | **Arbitrary Script Execution in Post-Actions** | `src/shusha/models/post_actions.py:42` | **MEDIUM** | User-configured shell commands are executed on download completion via `subprocess.Popen(cmd, shell=True)`. | Prohibit `shell=True`; require argument arrays with strict executable verification in `application/services/post_actions.py`. |
| **SEC-05** | **Permissive File Permissions on Credentials / State** | `src/shusha/models/settings.py:50`, `models/database.py:65` | **LOW** | SQLite DB and JSON configuration files containing RPC credentials are created with default umask (`0644` instead of `0600`). | Explicitly set `0600` permissions on sensitive config and database files in `infrastructure/persistence/`. |
