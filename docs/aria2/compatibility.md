# aria2 Compatibility & Protocol Compliance

> **Issue ID:** `P1-005`  
> **Status:** `DONE`

---

## 1. Protocol Transports

1. **JSON-RPC over HTTP (Port 6800 / default):**
   Used for standard stateless RPC queries (`tellActive`, `addUri`, `changeOption`).
2. **JSON-RPC over WebSocket:**
   Used for real-time bi-directional notifications (`aria2.onDownloadComplete`, `aria2.onDownloadStart`) with instant UI reactivity.
3. **XML-RPC (Compatibility fallback):**
   Supported for backwards compatibility with legacy local aria2 instances.

---

## 2. Security & Redaction Protocol

- All RPC tokens passed via `--rpc-secret` or `token:<secret>` authentication parameter are classified as sensitive.
- Sensitive option definitions in `spec/aria2/options.json` automatically trigger redaction filters before logging or diagnostic export.
