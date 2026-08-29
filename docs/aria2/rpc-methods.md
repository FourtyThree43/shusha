# aria2 RPC Methods Specification

> Authoritative RPC specification (36 methods).

| RPC Method | Category | Parameters | Return Type | Auth Required | Description |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `aria2.addUri` | `downloads` | `uris: list[str], options: dict[str, str], position: int` | `str` | Yes | Adds a new download. uris is an array of HTTP/FTP/SFTP/BitTorrent Magnet URIs pointing to the same resource. |
| `aria2.addTorrent` | `bittorrent` | `torrent: str, uris: list[str], options: dict[str, str], position: int` | `str` | Yes | Adds a BitTorrent download by uploading a base64-encoded .torrent file. |
| `aria2.addMetalink` | `metalink` | `metalink: str, options: dict[str, str], position: int` | `list[str]` | Yes | Adds a Metalink download by uploading a base64-encoded Metalink file. |
| `aria2.remove` | `control` | `gid: str` | `str` | Yes | Removes the download denoted by GID. If download is active, stops download first. |
| `aria2.forceRemove` | `control` | `gid: str` | `str` | Yes | Forcefully removes the download denoted by GID without contacting trackers. |
| `aria2.pause` | `control` | `gid: str` | `str` | Yes | Pauses the download denoted by GID. |
| `aria2.pauseAll` | `control` | `none` | `str` | Yes | Pauses all active and waiting downloads. |
| `aria2.forcePause` | `control` | `gid: str` | `str` | Yes | Forcefully pauses the download denoted by GID without waiting for piece actions. |
| `aria2.forcePauseAll` | `control` | `none` | `str` | Yes | Forcefully pauses all active and waiting downloads. |
| `aria2.unpause` | `control` | `gid: str` | `str` | Yes | Changes download status from paused to waiting. |
| `aria2.unpauseAll` | `control` | `none` | `str` | Yes | Unpauses all paused downloads. |
| `aria2.tellStatus` | `inspection` | `gid: str, keys: list[str]` | `dict` | Yes | Returns download progress and status for the download denoted by GID. |
| `aria2.getUris` | `inspection` | `gid: str` | `list[dict]` | Yes | Returns URIs used in the download denoted by GID. |
| `aria2.getFiles` | `inspection` | `gid: str` | `list[dict]` | Yes | Returns the file list of the download denoted by GID. |
| `aria2.getPeers` | `inspection` | `gid: str` | `list[dict]` | Yes | Returns peer list of the BitTorrent download denoted by GID. |
| `aria2.getServers` | `inspection` | `gid: str` | `list[dict]` | Yes | Returns connected HTTP/FTP/SFTP servers for the download denoted by GID. |
| `aria2.tellActive` | `inspection` | `keys: list[str]` | `list[dict]` | Yes | Returns a list of active downloads. |
| `aria2.tellWaiting` | `inspection` | `offset: int, num: int, keys: list[str]` | `list[dict]` | Yes | Returns a paginated list of waiting downloads, including paused. |
| `aria2.tellStopped` | `inspection` | `offset: int, num: int, keys: list[str]` | `list[dict]` | Yes | Returns a paginated list of stopped/completed/error downloads. |
| `aria2.changePosition` | `queue` | `gid: str, pos: int, how: str` | `int` | Yes | Moves the download in the queue. |
| `aria2.changeUri` | `downloads` | `gid: str, fileIndex: int, delUris: list[str], addUris: list[str], position: int` | `list[int]` | Yes | Removes the URIs in delUris and adds the URIs in addUris for the download denoted by GID. |
| `aria2.getOption` | `options` | `gid: str` | `dict[str, str]` | Yes | Returns download-scoped options for the download denoted by GID. |
| `aria2.changeOption` | `options` | `gid: str, options: dict[str, str]` | `str` | Yes | Changes download-scoped options dynamically for the download denoted by GID. |
| `aria2.getGlobalOption` | `options` | `none` | `dict[str, str]` | Yes | Returns all global options currently applied to the aria2 daemon session. |
| `aria2.changeGlobalOption` | `options` | `options: dict[str, str]` | `str` | Yes | Changes global options dynamically on the active aria2 daemon session. |
| `aria2.getGlobalStat` | `statistics` | `none` | `dict` | Yes | Returns global download/upload speed and total counts. |
| `aria2.purgeDownloadResult` | `maintenance` | `none` | `str` | Yes | Purges completed/error/removed download results to free memory. |
| `aria2.removeDownloadResult` | `maintenance` | `gid: str` | `str` | Yes | Removes a specific completed/error/removed download result from memory denoted by GID. |
| `aria2.getVersion` | `system` | `none` | `dict` | Yes | Returns version information and list of enabled compile-time features. |
| `aria2.getSessionInfo` | `system` | `none` | `dict` | Yes | Returns session ID used for WebSocket notifications. |
| `aria2.shutdown` | `system` | `none` | `str` | Yes | Gracefully shuts down the aria2 daemon. |
| `aria2.forceShutdown` | `system` | `none` | `str` | Yes | Immediately shuts down the aria2 daemon without waiting for active actions. |
| `aria2.saveSession` | `system` | `none` | `str` | Yes | Saves the current session to the file specified by --save-session. |
| `system.multicall` | `system` | `methods: list[dict]` | `list` | Yes | Executes multiple RPC methods in a single request transaction. |
| `system.listMethods` | `system` | `none` | `list[str]` | No | Returns all supported RPC methods on the server. |
| `system.listNotifications` | `system` | `none` | `list[str]` | No | Returns all supported notification event names on the server. |