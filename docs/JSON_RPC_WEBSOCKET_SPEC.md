# aria2 JSON-RPC 2.0 & WebSocket Protocol Specification

This specification documents the communication protocol between **Shusha-DM** and the **aria2c** daemon over JSON-RPC 2.0 and WebSockets.

---

## 1. Endpoints & Transport

- **WebSocket URI**: `ws://{host}:{port}/jsonrpc`
- **HTTP POST URI**: `http://{host}:{port}/jsonrpc`
- **Default Port**: `6800`

---

## 2. Request & Response Envelope

### Standard Request
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "method": "aria2.addUri",
  "params": [
    "token:secret_passphrase",
    ["https://example.com/archive.zip"],
    {
      "dir": "/downloads",
      "split": "16",
      "max-connection-per-server": "16"
    }
  ]
}
```

### Successful Response
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "result": "2089b05ecca3d829"
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "id": "req_001",
  "error": {
    "code": 1,
    "message": "Resource not found"
  }
}
```

---

## 3. Real-Time Push Notifications (WebSocket)

When connected via WebSocket, aria2 pushes server-initiated notifications without an `id` field:

| Notification Method | Trigger Event | Parameters |
| :--- | :--- | :--- |
| `aria2.onDownloadStart` | A task begins active download | `[{"gid": "<gid>"}]` |
| `aria2.onDownloadPause` | A task is paused | `[{"gid": "<gid>"}]` |
| `aria2.onDownloadStop` | A task is aborted / stopped | `[{"gid": "<gid>"}]` |
| `aria2.onDownloadComplete` | HTTP/FTP task completes and passes checksum | `[{"gid": "<gid>"}]` |
| `aria2.onDownloadError` | Unrecoverable error occurred | `[{"gid": "<gid>"}]` |
| `aria2.onBtDownloadComplete` | BitTorrent data payload finishes downloading | `[{"gid": "<gid>"}]` |

---

## 4. Batch Requests via `system.multicall`

To minimize latency when polling multiple downloads, requests are bundled into a single JSON-RPC frame:

```json
{
  "jsonrpc": "2.0",
  "id": "batch_1",
  "method": "system.multicall",
  "params": [[
    {"methodName": "aria2.tellStatus", "params": ["token:secret", "gid_1", ["status", "downloadSpeed"]]},
    {"methodName": "aria2.tellStatus", "params": ["token:secret", "gid_2", ["status", "downloadSpeed"]]},
    {"methodName": "aria2.getGlobalStat", "params": ["token:secret"]}
  ]]
}
```
