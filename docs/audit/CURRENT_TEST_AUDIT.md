# Current Test Suite Audit & Gap Analysis

> **Issue ID:** `P0-004`  
> **Status:** `DONE`  
> **Total Test Files:** 37 files  
> **Total Test Cases:** 167 collected items  
> **Pass Rate in Standard Environment:** 157 passed, 9 skipped, 1 failed (GUI display required).

---

## 1. Test File Inventory & Classification

| Test File | Test Cases | Module Tested | Test Type | Execution Notes / Dependencies | Gaps Identified |
| :--- | :---: | :--- | :---: | :--- | :--- |
| `tests/test_app_actions.py` | 17 | `views/app.py` | Integration / UI | Uses `unittest.mock` to mock controller | Mocks Tkinter internals rather than testing presentation logic |
| `tests/test_batch_parser.py` | 6 | `models/batch_parser.py` | Unit | Pure logic, fast | Needs edge-case test for invalid UTF-8 and huge payloads |
| `tests/test_category_manager.py` | 3 | `models/category_manager.py` | Integration | Uses in-memory/temp SQLite DB | Needs test for rule priority conflict |
| `tests/test_checksum_win.py` | 1 | `views/checksum_win.py` | Unit / UI | Mocks Tkinter root | Needs non-mocked hash stream test |
| `tests/test_cli.py` | 5 | `cli.py` | Integration | Tests CLI arguments via runner | Needs stdin piping test |
| `tests/test_client.py` | 13 | `models/client.py` | Integration | Mocks `xmlrpc.client.ServerProxy` | Lacks live aria2c protocol integration test |
| `tests/test_clipboard_watcher.py` | 3 | `models/clipboard_watcher.py` | Unit | Mocks Tkinter clipboard | Needs threading concurrency race condition test |
| `tests/test_controller_api.py` | 17 | `controller/api.py` | Integration | Mocks client and database | God-object tests; tests too many concerns simultaneously |
| `tests/test_daemon.py` | 3 | `models/daemon.py` | Integration | Mocks `subprocess.Popen` | Lacks test for zombie process recovery and stale PID file |
| `tests/test_database.py` | 10 | `models/database.py` | Integration | Creates temporary SQLite file | Lacks schema migration version upgrade test |
| `tests/test_gui_smoke.py` | 4 | `views/app.py` | UI Smoke | Requires X11/Tkinter display | Fails on headless environments without virtual framebuffer |
| `tests/test_inspector_win.py` | 2 | `views/inspector_win.py` | UI Smoke | Mocks controller | Does not test tab switching state transitions |
| `tests/test_logger.py` | 1 | `models/logger.py` | Unit | Tests logging output format | Needs tests for secret redaction |
| `tests/test_media_extractor.py` | 3 | `models/media_extractor.py` | Unit | M3U8 string parsing | Needs encrypted stream & nested playlist test |
| `tests/test_mirror_prober.py` | 4 | `models/mirror_prober.py` | Unit | Mocks `urllib.request` | Needs test for HTTP redirect loop and chunked HEAD |
| `tests/test_notifications.py` | 4 | `models/utilities.py` | Unit | Platform notification dispatch | Platform-dependent mock tests |
| `tests/test_path_opening.py` | 5 | `models/utilities.py` | Unit | OS path opening | Mocks `subprocess.Popen` |
| `tests/test_peers_and_servers.py` | 4 | `views/inspector_win.py` | Integration | Mocks client responses | Tests dictionary parsing |
| `tests/test_piece_map.py` | 1 | `views/piece_map.py` | UI Unit | Mocks Canvas drawing | Needs test for 100,000+ piece bitfield performance |
| `tests/test_post_actions.py` | 4 | `models/post_actions.py` | Unit | Tests post-download scripts | Needs safety validation tests for untrusted commands |
| `tests/test_query_syntax.py` | 3 | `views/app.py` | Unit | Search bar filter syntax | Good query syntax test |
| `tests/test_scheduler.py` | 2 | `models/scheduler.py` | Unit | Time window matching | Needs timezone and DST transition tests |
| `tests/test_security.py` | 2 | `models/utilities.py` | Unit | Path sanitization & traversal | Needs symlink breakout and Unicode normalization test |
| `tests/test_session_persistence.py` | 2 | `views/app.py` | Integration | Session dump and load | Tests UI persistence coupling |
| `tests/test_settings.py` | 1 | `models/settings.py` | Unit | JSON config save/load | Needs corrupt JSON recovery test |
| `tests/test_settings_win.py` | 4 | `views/settings_win.py` | UI Unit | Mocks settings manager | Needs validation failure rejection test |
| `tests/test_speed_graph.py` | 1 | `views/speed_graph.py` | UI Unit | Mocks Canvas drawing | Needs dynamic sampling frequency test |
| `tests/test_status_and_uri_win.py` | 2 | `views/status_win.py` | UI Unit | Mocks controller | Obsolete view test |
| `tests/test_structs.py` | 7 | `models/structs_downloads.py` | Unit | Dataclass property parsing | Good unit coverage for download models |
| `tests/test_svg_assets.py` | 4 | `models/svg_assets.py` | Unit / UI | SVG vector rendering | Tests icon generation |
| `tests/test_torrent_creator.py` | 3 | `models/torrent_creator.py` | Unit | Bencode and piece hashing | Needs multi-gigabyte file chunking test |
| `tests/test_torrent_features.py` | 4 | `views/torrent_win.py` | Integration | Torrent file tree parsing | Needs corrupted .torrent bencode test |
| `tests/test_tracker_service.py` | 3 | `models/tracker_service.py` | Integration | Mocks URL fetch | Needs test for tracker timeout fallback |
| `tests/test_utilities.py` | 10 | `models/utilities.py` | Unit | Formatting & conversion | High quality unit tests |
| `tests/test_webhook_server.py` | 2 | `models/webhook_server.py` | Integration | Starts local HTTP server | Network port binding conflict when run in parallel |
| `tests/test_ws_client.py` | 7 | `models/ws_client.py` | Unit | Mocks socket/WebSocket | Needs WebSocket reconnect and heartbeat ping/pong test |

---

## 2. Key Test Gaps & Strategy for Shusha 2

1. **Lack of Headless UI Testability:**
   Current UI tests instantiate Tkinter widgets, causing failures in headless CI. Shusha 2 will test 100% of presentation logic via headless ViewModels.
2. **Missing Real Engine Integration Harness:**
   Most tests mock `xmlrpc.client.ServerProxy` or `ws_client`. Shusha 2 will include a real `aria2c` test suite (`tests/integration/aria2/`) driven by a temporary aria2 daemon.
3. **No Database Migration Tests:**
   The current suite tests SQLite with fresh schemas. Shusha 2 will introduce versioned migration fixtures (`v1 -> v2 -> v3`) verifying data preservation.
