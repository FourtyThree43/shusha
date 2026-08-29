# aria2 Notifications & WebSocket Events

> Authoritative event specifications (6 event notifications).

| Event Name | Parameters | Description |
| :--- | :--- | :--- |
| `aria2.onDownloadStart` | `[{"gid": "<GID>"}]` | Emitted when a download starts or resumes. |
| `aria2.onDownloadPause` | `[{"gid": "<GID>"}]` | Emitted when a download is paused. |
| `aria2.onDownloadStop` | `[{"gid": "<GID>"}]` | Emitted when a download is stopped by user intervention. |
| `aria2.onDownloadComplete` | `[{"gid": "<GID>"}]` | Emitted when a download completes successfully. |
| `aria2.onDownloadError` | `[{"gid": "<GID>"}]` | Emitted when a download stops due to an error. |
| `aria2.onBtDownloadComplete` | `[{"gid": "<GID>"}]` | Emitted when a BitTorrent download completes seeding or finishes downloading files. |