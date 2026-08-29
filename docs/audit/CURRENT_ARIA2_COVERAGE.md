# Current aria2 Specification Coverage Analysis

> **Issue ID:** `P0-003` / `P1-001`  
> **Status:** `DONE`  
> **Target:** Full practical aria2c RPC, CLI, and Option Coverage

---

## 1. RPC Methods Coverage Breakdown

| aria2 RPC Method | Current Client Status | Implementation Location | Gaps & Limitations in Current Code | Target Support in Shusha 2 |
| :--- | :---: | :--- | :--- | :---: |
| `aria2.addUri` | **SUPPORTED** | `models/client.py:90`, `models/ws_client.py:315` | Options passed as untyped dict; no validation | `SUPPORTED` (Typed options) |
| `aria2.addTorrent` | **SUPPORTED** | `models/client.py:100` | Base64 encodes file directly; untyped options | `SUPPORTED` (Typed options) |
| `aria2.addMetalink` | **SUPPORTED** | `models/client.py:117` | Untyped options | `SUPPORTED` (Typed options) |
| `aria2.remove` | **SUPPORTED** | `models/client.py:123` | Returns raw GID string | `SUPPORTED` (Domain GID) |
| `aria2.forceRemove` | **SUPPORTED** | `models/client.py:128` | None | `SUPPORTED` (Domain GID) |
| `aria2.pause` | **SUPPORTED** | `models/client.py:133` | None | `SUPPORTED` (Domain GID) |
| `aria2.pauseAll` | **SUPPORTED** | `models/client.py:138` | None | `SUPPORTED` |
| `aria2.forcePause` | **SUPPORTED** | `models/client.py:143` | None | `SUPPORTED` (Domain GID) |
| `aria2.forcePauseAll` | **SUPPORTED** | `models/client.py:148` | None | `SUPPORTED` |
| `aria2.unpause` | **SUPPORTED** | `models/client.py:153` | None | `SUPPORTED` (Domain GID) |
| `aria2.unpauseAll` | **SUPPORTED** | `models/client.py:158` | None | `SUPPORTED` |
| `aria2.tellStatus` | **SUPPORTED** | `models/client.py:163` | Queries without field filtering; inefficient | `SUPPORTED` (Field selection + model) |
| `aria2.getUris` | **SUPPORTED** | `models/client.py:190` | Untyped dictionary response | `SUPPORTED` (Typed `DownloadSource`) |
| `aria2.getFiles` | **SUPPORTED** | `models/client.py:208` | Untyped dictionary response | `SUPPORTED` (Typed `DownloadFile`) |
| `aria2.getPeers` | **SUPPORTED** | `models/client.py:238` | Untyped dictionary response | `SUPPORTED` (Typed `Peer`) |
| `aria2.getServers` | **SUPPORTED** | `models/client.py:246` | Untyped dictionary response | `SUPPORTED` (Typed `Server`) |
| `aria2.tellActive` | **SUPPORTED** | `models/client.py:265` | Returns full status payloads | `SUPPORTED` (Batch typed models) |
| `aria2.tellWaiting` | **SUPPORTED** | `models/client.py:280` | Offset/num parameters loosely typed | `SUPPORTED` (Pagination model) |
| `aria2.tellStopped` | **SUPPORTED** | `models/client.py:289` | Offset/num parameters loosely typed | `SUPPORTED` (Pagination model) |
| `aria2.changePosition` | **SUPPORTED** | `models/client.py:295` | Untyped position integer | `SUPPORTED` (Queue command) |
| `aria2.changeUri` | **SUPPORTED** | `models/client.py:310` | Index and URIs loosely checked | `SUPPORTED` (Typed source editor) |
| `aria2.getOption` | **SUPPORTED** | `models/client.py:321` | Untyped key-value strings | `SUPPORTED` (Option registry) |
| `aria2.changeOption` | **SUPPORTED** | `models/client.py:328` | Untyped dictionary; no validation | `SUPPORTED` (Validated option change) |
| `aria2.getGlobalOption` | **SUPPORTED** | `models/client.py:334` | Untyped dictionary | `SUPPORTED` (Global config model) |
| `aria2.changeGlobalOption` | **SUPPORTED** | `models/client.py:340` | Untyped dictionary | `SUPPORTED` (Global config model) |
| `aria2.getGlobalStat` | **SUPPORTED** | `models/client.py:346` | Parsed into `GlobalStat` dataclass | `SUPPORTED` (Typed `Statistics`) |
| `aria2.purgeDownloadResult` | **SUPPORTED** | `models/client.py:362` | None | `SUPPORTED` |
| `aria2.removeDownloadResult` | **SUPPORTED** | `models/client.py:374` | None | `SUPPORTED` |
| `aria2.getVersion` | **SUPPORTED** | `models/client.py:390` | Parsed as dict | `SUPPORTED` (Typed `VersionInfo`) |
| `aria2.getSessionInfo` | **SUPPORTED** | `models/client.py:399` | Parsed as dict | `SUPPORTED` (Typed `SessionInfo`) |
| `aria2.shutdown` | **SUPPORTED** | `models/client.py:409` | None | `SUPPORTED` |
| `aria2.forceShutdown` | **SUPPORTED** | `models/client.py:418` | None | `SUPPORTED` |
| `aria2.saveSession` | **SUPPORTED** | `models/client.py:427` | None | `SUPPORTED` |
| `system.multicall` | **SUPPORTED** | `models/client.py:444` | Basic multicall loop | `SUPPORTED` (Batch pipeline) |
| `system.listMethods` | **MISSING** | Not implemented in client | Missing introspection | `SUPPORTED` |
| `system.listNotifications` | **MISSING** | Not implemented in client | Missing introspection | `SUPPORTED` |

---

## 2. Option Registry Gap Analysis

- **Total aria2 Manual Options:** ~210 options.
- **Current `structs_options.py` Coverage:** 26 options (~12% coverage).
- **Missing Major Option Categories in Current Implementation:**
  - BitTorrent Advanced (`bt-tracker-connect-timeout`, `bt-tracker-interval`, `bt-prioritize-piece`, `bt-max-open-files`, `bt-lpd-interface`, `bt-enable-hook-after-hash-check`, `bt-seed-unverified`, `dht-entry-point6`, `dht-listen-addr6`, `dht-message-timeout`).
  - Metalink Advanced (`metalink-base-uri`, `metalink-language`, `metalink-location`, `metalink-os`, `metalink-version`, `metalink-preferred-protocol`).
  - Network / TLS / Security (`ca-certificate`, `certificate`, `private-key`, `check-certificate`, `http-auth-challenge`, `no-proxy`, `proxy-method`).
  - Disk / File Allocation (`file-allocation`, `falloc`, `trunc`, `prealloc`, `enable-mmap`, `disk-cache`).
  - Dynamic vs Static Classification: Current UI does not know which options can be changed at runtime via `aria2.changeOption` vs only at daemon startup.

*Shusha 2 Requirement:* All ~210 aria2 options will be authoritatively catalogued in `spec/aria2/options.json` and loaded into a typed `OptionRegistry`.
