# aria2 RPC Protocol & Feature Analysis for Shusha-DM

This document provides a comprehensive technical review of the **aria2c (v1.37+)** RPC interface, compares feature parity between aria2, the **aria2p** Python reference library, and **Shusha-DM**, and defines the modernization roadmap for Shusha.

---

## 1. Overview of aria2 RPC Interface

aria2 provides an XML-RPC and JSON-RPC over HTTP/WebSocket interface allowing external frontends to control downloads, query daemon status, manage options, and persist sessions.

### Protocol Comparison: XML-RPC vs JSON-RPC / WebSocket

| Protocol | Transport | Serialization | Bi-directional Notifications | Shusha Status |
| :--- | :--- | :--- | :--- | :--- |
| **XML-RPC** | HTTP POST | XML payload | No (client polling required) | **Active Primary Engine** |
| **JSON-RPC (HTTP)** | HTTP POST | JSON payload | No (client polling required) | Supported by Client |
| **JSON-RPC (WS)** | WebSocket | JSON payload | Yes (`aria2.onDownloadStart`, etc.) | Planned for Future Architecture |

---

## 2. Complete aria2 RPC Methods Matrix & Implementation Status

The table below outlines all official aria2 RPC methods and their support across `aria2c`, `aria2p`, and `Shusha-DM`:

| RPC Method | Purpose / Description | aria2 Core | aria2p | Shusha API | Shusha GUI |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `aria2.addUri` | Add new HTTP/FTP/SFTP download | ✅ | ✅ | ✅ `add_uris` | ✅ Add Window |
| `aria2.addTorrent` | Add BitTorrent download (`.torrent`) | ✅ | ✅ | ✅ `add_torrent` | ✅ Add Window (Tab 2) |
| `aria2.addMetalink` | Add Metalink download (`.metalink`) | ✅ | ✅ | ✅ `add_metalink` | ✅ Add Window (Tab 3) |
| `aria2.remove` | Remove active/waiting download | ✅ | ✅ | ✅ `remove` | ✅ Toolbar / Context Menu |
| `aria2.forceRemove` | Immediately remove without cleanup wait | ✅ | ✅ | ✅ `remove(force=True)` | ✅ Context Menu |
| `aria2.pause` | Pause active download | ✅ | ✅ | ✅ `pause` | ✅ Toolbar / Context Menu |
| `aria2.pauseAll` | Pause all active downloads | ✅ | ✅ | ✅ `pause_all` | ✅ Queue Button |
| `aria2.forcePause` | Immediately pause active download | ✅ | ✅ | ✅ `client.force_pause` | 🔄 Backend Only |
| `aria2.forcePauseAll` | Immediately pause all downloads | ✅ | ✅ | ✅ `client.force_pause_all`| 🔄 Backend Only |
| `aria2.unpause` | Resume paused download | ✅ | ✅ | ✅ `resume` | ✅ Toolbar / Context Menu |
| `aria2.unpauseAll` | Resume all paused downloads | ✅ | ✅ | ✅ `resume_all` | ✅ Queue Button |
| `aria2.tellStatus` | Query status of single GID | ✅ | ✅ | ✅ `download_status` | ✅ Status / Details Window |
| `aria2.getUris` | Get URIs associated with download | ✅ | ✅ | ✅ `client.get_uris` | ✅ URI Manager Window |
| `aria2.getFiles` | Get file list & selective download flags | ✅ | ✅ | ✅ `client.get_files` | ✅ Torrent File Selector |
| `aria2.getPeers` | Get connected BitTorrent peers | ✅ | ✅ | ✅ `get_peers` | ✅ Inspector Tab (Peers) |
| `aria2.getServers` | Get connected HTTP/FTP mirror servers | ✅ | ✅ | ✅ `get_servers` | ✅ Inspector Tab (Servers) |
| `aria2.tellActive` | Query list of currently active downloads | ✅ | ✅ | ✅ `active_downloads` | ✅ Main Downloads Table |
| `aria2.tellWaiting` | Query list of waiting/queued downloads | ✅ | ✅ | ✅ `waiting_downloads`| ✅ Main Downloads Table |
| `aria2.tellStopped` | Query list of stopped/completed/errored | ✅ | ✅ | ✅ `stopped_downloads`| ✅ Main Downloads Table |
| `aria2.changePosition` | Reorder download in queue (POS_SET/CUR/END)| ✅ | ✅ | ✅ `move`, `move_up`, etc.| ✅ Toolbar Up/Down Arrows |
| `aria2.changeUri` | Add, remove, or modify download URIs | ✅ | ✅ | ✅ `change_uri` | ✅ URI Manager Window |
| `aria2.getOption` | Get options for specific download | ✅ | ✅ | ✅ `get_options` | ✅ Inspector / Options Tab |
| `aria2.changeOption` | Modify live options for a download | ✅ | ✅ | ✅ `set_options` | ✅ Settings / Inspector |
| `aria2.getGlobalOption` | Query daemon-wide global options | ✅ | ✅ | ✅ `get_global_options` | ✅ Settings Window |
| `aria2.changeGlobalOption`| Update daemon-wide global options | ✅ | ✅ | ✅ `set_global_options` | ✅ Settings Window |
| `aria2.getGlobalStat` | Daemon transfer speeds & queue counts | ✅ | ✅ | ✅ `get_stats` | ✅ Bottom Status Bar |
| `aria2.purgeDownloadResult`| Clear completed/errored results | ✅ | ✅ | ✅ `purge` | ✅ Clear Queue Button |
| `aria2.removeDownloadResult`| Remove single completed/errored result | ✅ | ✅ | ✅ `client.remove_result`| ✅ Delete on item |
| `aria2.getVersion` | Query aria2 version and enabled features | ✅ | ✅ | ✅ `client.get_version` | 🔄 Backend Only |
| `aria2.getSessionInfo` | Get session ID (token check) | ✅ | ✅ | ✅ `client.get_session_info`| 🔄 Backend Only |
| `aria2.shutdown` | Gracefully shut down aria2c daemon | ✅ | ✅ | ✅ `remote.stop_server` | ✅ App Exit Hook |
| `aria2.saveSession` | Persist current session to input-file | ✅ | ✅ | ✅ `client.save_session` | ✅ App Exit Hook |

---

## 3. High-Value Capabilities Identified from aria2p

The `aria2p` reference implementation demonstrates several software design patterns that benefit Shusha:

1. **Typed Options Abstraction**:
   - `aria2p` defines structured dataclasses/enums for valid aria2 option keys (e.g. `max-download-limit`, `select-file`, `split`, `header`).
   - *Shusha Adoption*: `src/shusha/models/structs_options.py` implements structured option objects, simplifying GUI-to-RPC translation.

2. **Granular File Selection in Multi-File Downloads**:
   - In torrent and metalink downloads, users frequently want to select or unselect specific files.
   - `aria2.changeOption(gid, {"select-file": "1,3,4-7"})` allows dynamic sub-file filtering.
   - *Shusha Adoption*: Implemented via `TorrentFilesWindow` and `open_selective_files()` in `Aria2Gui`.

3. **Multi-Source Fallback & Mirror Optimization**:
   - Querying `aria2.getServers` and `aria2.getPeers` provides insight into network bottlenecks.
   - *Shusha Adoption*: Tabbed inspector displays live mirror connection speeds and peer distribution.

4. **Resilient Daemon Lifecycle Management**:
   - Handling RPC secret authentication, ephemeral ports, and ensuring clean background process termination with PID validation.

---

## 4. Shusha-DM Modernization Roadmap

Based on the protocol and library analysis, the following feature additions are recommended for future milestones:

### Milestone A: UX & Visual Enhancements
- **Piece Map Graphic**: Visual grid representing bitfield pieces downloaded/verified in real time.
- **Bandwidth Scheduling**: Time-based speed limits (e.g., unlimited at night, throttled during working hours).

### Milestone B: Protocol & Performance Improvements
- **WebSocket Event Listener**: Optional WebSocket listener mode for instant event-driven UI updates instead of interval polling.
- **Batch Link Parser**: Clipboard monitor and multi-line regex parser for batch download links (supporting authentication headers and custom referrers).
