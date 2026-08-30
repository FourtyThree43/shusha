# ADR-010: WebExtensions Native Messaging Bridge & Security Boundary

## Status
Accepted

## Context
Browser extensions (Chrome, Firefox, Brave, Edge) intercept download clicks and pass URLs/cookies to Shusha. Browser input is fundamentally untrusted.

## Decision
1. Standard WebExtensions Native Messaging: Communication runs over standard stdio using 32-bit length-prefixed JSON frames (`src/shusha/acquisition/browser/bridge.py`).
2. Security Validation:
   - Origin validation against registered extension IDs.
   - Strict request schema and payload sanitization.
   - Disallow direct download execution; all browser inputs are ingested into `AcquisitionRequest` and staged in `AcquisitionInbox`.
3. Dedicated manifest installer (`shusha install-host`) registers manifests in standard user configuration paths across Linux, macOS, and Windows.

## Consequences
- **Positive**: Zero exposure of internal RPC ports to web pages or malicious scripts.
- **Positive**: Seamless one-click capture of multi-part browser downloads.
