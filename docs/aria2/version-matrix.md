# aria2 Version Support & Compatibility Policy

> **Issue ID:** `P1-005`  
> **Status:** `DONE`

---

## 1. Version Support Matrix

| aria2c Version | Support Level | Feature Status | Notes |
| :--- | :---: | :--- | :--- |
| `< 1.35.0` | **UNSUPPORTED** | Missing WebSocket notifications and multicall features. | Will raise `UnsupportedAria2VersionError` on connection. |
| `1.35.0` | **SUPPORTED** | Baseline XML-RPC & JSON-RPC supported. | Fully operational. |
| `1.36.0` | **SUPPORTED** | Full support. | Tested in CI. |
| `1.37.0+` | **SUPPORTED (PRIMARY)** | Full support with all compile-time extensions. | Default installed engine. |

---

## 2. Compile-Time Capability Detection

On connection initialization, Shusha invokes `aria2.getVersion` to inspect `enabledFeatures`:
- `BitTorrent`: Enables Torrent/Magnet inspectors and torrent creator.
- `Metalink`: Enables Metalink file ingestion.
- `HTTPS`: Enables TLS options (`--ca-certificate`, `--check-certificate`).
- `SFTP`: Enables SSH key authentication and SFTP URIs.
- `GZip`: Enables `http-accept-gzip` options.
