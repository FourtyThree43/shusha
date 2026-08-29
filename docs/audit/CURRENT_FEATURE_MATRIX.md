# Current Feature Matrix & Implementation Mapping

> **Issue ID:** `P0-003`  
> **Status:** `DONE`  
> **Purpose:** Inventory all existing capabilities, evaluate test/documentation coverage, and define the target implementation layer for the Shusha 2 rewrite.

---

## 1. Feature Coverage Matrix

| Feature Domain | Feature Name | Current Implementation Location | Current Tests | Current Docs | Target Implementation Location | Rewrite Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Downloads** | HTTP/HTTPS Downloads | `models/client.py`, `views/add_win.py` | `test_client.py`, `test_controller_api.py` | `docs/FEATURES_GUIDE.md` | `application/services/downloads.py` | **REWRITE** |
| **Downloads** | FTP / SFTP Downloads | `models/client.py`, `models/utilities.py` | `test_client.py` | `docs/FEATURES_GUIDE.md` | `application/services/downloads.py` | **REWRITE** |
| **Downloads** | BitTorrent (.torrent files) | `models/client.py`, `views/torrent_win.py` | `test_torrent_features.py` | `docs/FEATURES_GUIDE.md` | `domain/torrent.py`, `application/services/torrent.py` | **REWRITE** |
| **Downloads** | Magnet Links | `models/batch_parser.py`, `models/client.py` | `test_batch_parser.py` | `docs/FEATURES_GUIDE.md` | `domain/download_source.py` | **ADAPT** |
| **Downloads** | Metalink Ingestion | `models/client.py` (`addMetalink`) | `test_client.py` | `docs/ARIA2_FEATURE_ANALYSIS.md` | `domain/metalink.py`, `application/services/metalink.py` | **REWRITE** |
| **Downloads** | Batch URL Parsing | `models/batch_parser.py`, `views/batch_add_win.py` | `test_batch_parser.py` | `docs/FEATURES_GUIDE.md` | `domain/download_source.py` | **ADAPT** |
| **Downloads** | M3U8 Stream Extraction | `models/media_extractor.py` | `test_media_extractor.py` | `docs/FEATURES_GUIDE.md` | `application/services/media_extractor.py` | **ADAPT** |
| **Downloads** | Mirror Latency Probing | `models/mirror_prober.py` | `test_mirror_prober.py` | `docs/FEATURES_GUIDE.md` | `infrastructure/networking/mirror_prober.py` | **ADAPT** |
| **Downloads** | Checksum Verification | `views/checksum_win.py`, `models/utilities.py` | `test_checksum_win.py` | `docs/FEATURES_GUIDE.md` | `domain/checksum.py`, `presentation/dialogs/checksum.py` | **ADAPT** |
| **Downloads** | Torrent File Creator | `models/torrent_creator.py`, `views/create_torrent_win.py` | `test_torrent_creator.py` | `docs/FEATURES_GUIDE.md` | `domain/torrent.py`, `application/services/torrent.py` | **ADAPT** |
| **Engine & RPC** | XML-RPC Client | `models/client.py` | `test_client.py` | `docs/JSON_RPC_WEBSOCKET_SPEC.md` | `infrastructure/aria2/xmlrpc/` | **REWRITE** |
| **Engine & RPC** | JSON-RPC / WebSocket Client | `models/ws_client.py` | `test_ws_client.py` | `docs/JSON_RPC_WEBSOCKET_SPEC.md` | `infrastructure/aria2/jsonrpc/` | **REWRITE** |
| **Engine & RPC** | Daemon Supervision | `models/daemon.py` | `test_daemon.py` | `docs/MULTI_OS_GUIDE.md` | `infrastructure/daemon/` | **REWRITE** |
| **Engine & RPC** | Public Tracker Synchronization | `models/tracker_service.py` | `test_tracker_service.py` | `docs/FEATURES_GUIDE.md` | `infrastructure/networking/trackers.py` | **ADAPT** |
| **Queue & Scheduling** | Download Scheduling (Time-based) | `models/scheduler.py` | `test_scheduler.py` | `docs/FEATURES_GUIDE.md` | `domain/scheduler.py`, `application/services/scheduler.py` | **ADAPT** |
| **Queue & Scheduling** | Category Rules & Auto-filing | `models/category_manager.py` | `test_category_manager.py` | `docs/FEATURES_GUIDE.md` | `domain/category.py`, `application/services/categories.py` | **ADAPT** |
| **Automation** | Post-Download Automation Hooks | `models/post_actions.py` | `test_post_actions.py` | `docs/FEATURES_GUIDE.md` | `application/services/post_actions.py` | **ADAPT** |
| **Automation** | Clipboard URL Sniffer | `models/clipboard_watcher.py` | `test_clipboard_watcher.py` | `docs/FEATURES_GUIDE.md` | `infrastructure/os/clipboard.py` | **ADAPT** |
| **Automation** | Browser Webhook Server | `models/webhook_server.py`, `extensions/` | `test_webhook_server.py` | `docs/FEATURES_GUIDE.md` | `infrastructure/networking/webhook.py` | **REWRITE** |
| **Persistence** | SQLite Download History | `models/database.py` | `test_database.py` | `docs/ARCHITECTURE.md` | `infrastructure/persistence/` | **REWRITE** |
| **Persistence** | Settings Storage | `models/settings.py` | `test_settings.py` | `docs/ARCHITECTURE.md` | `infrastructure/configuration/` | **REWRITE** |
| **UI & Visuals** | Main Desktop Window | `views/app.py` | `test_gui_smoke.py` | `docs/design_documentation.md` | `presentation/app.py`, `presentation/screens/` | **REWRITE** |
| **UI & Visuals** | Download Inspector Panel | `views/inspector_win.py` | `test_inspector_win.py` | `docs/design_documentation.md` | `presentation/screens/inspector/` | **REWRITE** |
| **UI & Visuals** | Piece Map Visualizer | `views/piece_map.py` | `test_piece_map.py` | `docs/design_documentation.md` | `presentation/widgets/piece_map.py` | **ADAPT** |
| **UI & Visuals** | Live Speed Graph | `views/speed_graph.py` | `test_speed_graph.py` | `docs/design_documentation.md` | `presentation/widgets/speed_graph.py` | **ADAPT** |
| **UI & Visuals** | SVG Vector Icon Engine | `models/svg_assets.py` | `test_svg_assets.py` | `docs/design_documentation.md` | `presentation/theme/icons.py` | **ADAPT** |
| **CLI** | Headless CLI Interface | `cli.py` | `test_cli.py` | `docs/FEATURES_GUIDE.md` | `cli/` | **REWRITE** |
