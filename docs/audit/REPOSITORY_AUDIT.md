# Repository Source Inventory & Module Audit

> **Issue ID:** `P0-002`  
> **Status:** `DONE`  
> **Total Source Files:** 42 modules  
> **Total Source Lines:** 10,182 LOC  
> **Classification Key:**  
> - `KEEP`: Reusable as-is in target architecture.  
> - `ADAPT`: Core logic preserved but refactored into domain/application/infrastructure layers.  
> - `REWRITE`: Completely rewritten from scratch to adhere to modern typed architecture.  
> - `REMOVE`: Obsolete or replaced entirely.

---

## 1. Complete Module-by-Module Inventory

| Module Path | LOC | Classes / Key Functions | Primary Couplings | Identified Code Smells & Gaps | Target Rewrite Layer | Disposition |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| `src/shusha/ShushaDM.py` | 74 | `main`, entry point | Tkinter, ttkbootstrap, `App` | Instantiates UI directly, sets theme from string | `src/shusha/__main__.py` | **REWRITE** |
| `src/shusha/__about__.py` | 9 | `__version__` | None | None | `src/shusha/__about__.py` | **KEEP** |
| `src/shusha/__init__.py` | 0 | Package init | None | Empty | `src/shusha/__init__.py` | **KEEP** |
| `src/shusha/__main__.py` | 15 | CLI entrypoint | `sys`, `cli.main` | Legacy sys.exit invocation | `src/shusha/__main__.py` | **REWRITE** |
| `src/shusha/cli.py` | 242 | `CLI`, `main` | `argparse`, `ControllerAPI`, `ws_client` | Monolithic argparse handler; direct stdout formatting | `src/shusha/cli/` | **REWRITE** |
| `src/shusha/controller/__init__.py` | 0 | Package init | None | Empty | `src/shusha/controller/` | **REMOVE** |
| `src/shusha/controller/api.py` | 967 | `ControllerAPI` | `client`, `database`, `daemon`, `settings` | 967 LOC god-object proxying everything; untyped dict returns | `src/shusha/application/services/` | **REWRITE** |
| `src/shusha/models/__init__.py` | 0 | Package init | None | Empty | `src/shusha/domain/` | **REMOVE** |
| `src/shusha/models/batch_parser.py` | 121 | `BatchParser` | Regex, URL parsing | Good parsing logic, but untyped dictionaries returned | `src/shusha/domain/download_source.py` | **ADAPT** |
| `src/shusha/models/category_manager.py` | 78 | `CategoryManager` | `database` | Direct DB queries embedded in manager | `src/shusha/domain/category.py` & `application/services/categories.py` | **ADAPT** |
| `src/shusha/models/client.py` | 464 | `Aria2Client` | `xmlrpc.client`, `socket`, `urllib` | XML-RPC transport mixed with model parsing; untyped dicts | `src/shusha/infrastructure/aria2/xmlrpc/` | **REWRITE** |
| `src/shusha/models/clipboard_watcher.py` | 114 | `ClipboardWatcher` | `tkinter`, threading | Tkinter root passed into background thread; thread-safety risk | `src/shusha/infrastructure/os/clipboard.py` | **ADAPT** |
| `src/shusha/models/daemon.py` | 240 | `DaemonManager` | `subprocess`, `platformdirs`, `socket` | Popen lifecycle without supervisor protocol; unredacted logs | `src/shusha/infrastructure/daemon/` | **REWRITE** |
| `src/shusha/models/database.py` | 975 | `DatabaseManager` | `sqlite3`, `platformdirs` | Raw SQL queries string-concatenated; no schema migration versioning | `src/shusha/infrastructure/persistence/` | **REWRITE** |
| `src/shusha/models/db.py` | 31 | `Database` | `sqlite3` | Obsolete duplicate DB helper | Dead code | **REMOVE** |
| `src/shusha/models/logger.py` | 108 | `LoggerService` | `logging`, `platformdirs` | Import-time mkdir side-effects; unredacted secrets | `src/shusha/telemetry/logging.py` | **REWRITE** |
| `src/shusha/models/media_extractor.py` | 102 | `MediaExtractor` | `urllib`, regex, `m3u8` | Good M3U8 parser, needs typed Segment dataclasses | `src/shusha/application/services/media_extractor.py` | **ADAPT** |
| `src/shusha/models/mirror_prober.py` | 125 | `MirrorProber`, `MirrorProbeResult` | `urllib.request`, `concurrent.futures` | Useful probing logic, needs clean timeout/cancellation | `src/shusha/infrastructure/networking/mirror_prober.py` | **ADAPT** |
| `src/shusha/models/post_actions.py` | 127 | `PostActionsManager` | `subprocess`, `shutil`, `os` | Direct shell command execution and script runner; security review needed | `src/shusha/application/services/post_actions.py` | **ADAPT** |
| `src/shusha/models/scheduler.py` | 116 | `DownloadScheduler` | `datetime`, `threading` | Custom timer loop; needs cron/interval schedule domain model | `src/shusha/application/services/scheduler.py` | **ADAPT** |
| `src/shusha/models/settings.py` | 74 | `SettingsManager` | `json`, `platformdirs` | Raw JSON configuration serialization without schema validation | `src/shusha/infrastructure/configuration/` | **REWRITE** |
| `src/shusha/models/structs_downloads.py` | 491 | `DownloadItem`, `DownloadStatus`, `Aria2File` | `dataclasses` | Dataclass definitions with loose types and dict loaders | `src/shusha/domain/download.py` | **ADAPT** |
| `src/shusha/models/structs_options.py` | 114 | `Aria2Options` | `dataclasses` | Partial option coverage (~25 options out of 200+ aria2 options) | `src/shusha/infrastructure/aria2/options/` | **REWRITE** |
| `src/shusha/models/structs_stats.py` | 70 | `GlobalStat`, `EngineStats` | `dataclasses` | Good start for engine stats, needs typed bitrates | `src/shusha/domain/statistics.py` | **ADAPT** |
| `src/shusha/models/svg_assets.py` | 304 | `SVGAssetGenerator`, `VectorIconProvider` | `tkinter`, SVG drawing | Useful vector glyph renderers, keep and extend | `src/shusha/presentation/theme/icons.py` | **ADAPT** |
| `src/shusha/models/torrent_creator.py` | 154 | `TorrentCreator`, `TorrentMeta` | `hashlib`, `bencode` | Custom bencoding and hashing; needs robust piece hashing | `src/shusha/domain/torrent.py` | **ADAPT** |
| `src/shusha/models/tracker_service.py` | 115 | `TrackerService` | `urllib.request` | Remote tracker list fetcher; lacks retry and caching | `src/shusha/infrastructure/networking/trackers.py` | **ADAPT** |
| `src/shusha/models/utilities.py` | 402 | Formatting, speed, sizes, URLs | `platformdirs`, `subprocess` | Mixed bag of utility functions; some invoke subprocess `xdg-open` | `src/shusha/utils/` | **ADAPT** |
| `src/shusha/models/webhook_server.py` | 150 | `WebhookServer`, `WebhookRequestHandler` | `http.server`, `threading` | Unauthenticated local HTTP server for browser extension | `src/shusha/infrastructure/networking/webhook.py` | **REWRITE** |
| `src/shusha/models/ws_client.py` | 400 | `Aria2WsClient`, `JsonRpcException` | `socket`, `json`, `threading` | Handcrafted JSON-RPC/WebSocket client; mixed transport and event loop | `src/shusha/infrastructure/aria2/jsonrpc/` | **REWRITE** |
| `src/shusha/views/__init__.py` | 0 | Package init | None | Empty | `src/shusha/presentation/` | **REMOVE** |
| `src/shusha/views/add_win.py` | 250 | `AddDownloadWindow` | Tkinter, ttkbootstrap | Directly talks to `ControllerAPI`; no validation separation | `src/shusha/presentation/dialogs/add_download.py` | **REWRITE** |
| `src/shusha/views/app.py` | 1111 | `App` | Tkinter, ttkbootstrap, `ControllerAPI`, DB | 1111 LOC god-view; owns polling loop, table rendering, DB calls | `src/shusha/presentation/app.py` & `screens/` | **REWRITE** |
| `src/shusha/views/batch_add_win.py` | 160 | `BatchAddWindow` | Tkinter, ttkbootstrap | Direct controller access, lack of preview validation | `src/shusha/presentation/dialogs/batch_add.py` | **REWRITE** |
| `src/shusha/views/checksum_win.py` | 167 | `ChecksumVerifierWindow` | Tkinter, `hashlib`, threading | Good hashing logic, needs separation from UI thread | `src/shusha/presentation/dialogs/checksum.py` | **ADAPT** |
| `src/shusha/views/create_torrent_win.py` | 165 | `CreateTorrentWindow` | Tkinter, `TorrentCreator` | Direct blocking torrent creation from UI | `src/shusha/presentation/dialogs/torrent.py` | **REWRITE** |
| `src/shusha/views/inspector_win.py` | 303 | `DownloadInspectorWindow` | Tkinter, ttkbootstrap | Directly queries aria2 via ControllerAPI | `src/shusha/presentation/screens/inspector/` | **REWRITE** |
| `src/shusha/views/piece_map.py` | 126 | `PieceMapCanvas` | Tkinter `Canvas` | Direct canvas bitfield rendering; useful, needs clean ViewModel | `src/shusha/presentation/widgets/piece_map.py` | **ADAPT** |
| `src/shusha/views/settings_win.py` | 657 | `SettingsWindow` | Tkinter, ttkbootstrap | 657 LOC multi-tab dialog directly saving to SettingsManager | `src/shusha/presentation/screens/settings/` | **REWRITE** |
| `src/shusha/views/speed_graph.py` | 140 | `SpeedGraphCanvas` | Tkinter `Canvas` | Direct canvas graph plotting; useful, needs reactive data model | `src/shusha/presentation/widgets/speed_graph.py` | **ADAPT** |
| `src/shusha/views/status_win.py` | 400 | `StatusWindow` | Tkinter, ttkbootstrap | Monolithic status dialog; obsolete | `src/shusha/presentation/screens/inspector/` | **REMOVE** |
| `src/shusha/views/torrent_win.py` | 216 | `TorrentWindow` | Tkinter, ttkbootstrap | File selection dialog for torrents | `src/shusha/presentation/dialogs/torrent.py` | **REWRITE** |
| `src/shusha/views/uri_win.py` | 142 | `UriWindow` | Tkinter, ttkbootstrap | URI editor; obsolete | `src/shusha/presentation/dialogs/uri.py` | **REMOVE** |

---

## 2. Summary of Source Dispositions

- **KEEP (3 modules):** `__init__.py`, `__about__.py`
- **ADAPT (16 modules):** `batch_parser.py`, `category_manager.py`, `clipboard_watcher.py`, `media_extractor.py`, `mirror_prober.py`, `post_actions.py`, `scheduler.py`, `structs_downloads.py`, `structs_stats.py`, `svg_assets.py`, `torrent_creator.py`, `tracker_service.py`, `utilities.py`, `checksum_win.py`, `piece_map.py`, `speed_graph.py`
- **REWRITE (17 modules):** `ShushaDM.py`, `__main__.py`, `cli.py`, `api.py`, `client.py`, `daemon.py`, `database.py`, `logger.py`, `settings.py`, `structs_options.py`, `webhook_server.py`, `ws_client.py`, `add_win.py`, `app.py`, `batch_add_win.py`, `create_torrent_win.py`, `inspector_win.py`, `settings_win.py`, `torrent_win.py`
- **REMOVE (6 modules):** `models/db.py`, `views/status_win.py`, `views/uri_win.py`, and empty init modules.
