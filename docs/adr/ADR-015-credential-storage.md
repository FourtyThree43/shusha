# ADR-015: Credential Storage, Reference Boundary & Secret Redaction

## Status
Accepted

## Context
Downloads often require authentication (HTTP basic/bearer tokens, FTP credentials, proxy passwords, private tracker passkeys, RPC secrets). Storing or logging secrets in plain text creates critical security vulnerabilities.

## Decision
1. Introduce `CredentialReference` and `CredentialVault` protocol in `src/shusha/domain/credentials.py`.
2. Logging Redactor: Automated secret filter intercepts strings matching patterns (passwords, tokens, RPC secrets, authorization headers) and replaces them with `[REDACTED]`.
3. Process argument protection: Command strings pass credentials via argument arrays or stdin, avoiding shell history leakage.

## Consequences
- **Positive**: Complete protection against credential leakage in logs, diagnostics, and process lists.
- **Positive**: Strict security gate compliance.
