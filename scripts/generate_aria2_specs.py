import json
import re
import subprocess
from pathlib import Path
from typing import TypedDict

ROOT = Path("/home/BillGates/code/shusha")
SPEC_DIR = ROOT / "spec" / "aria2"
DOCS_ARIA2_DIR = ROOT / "docs" / "aria2"

SPEC_DIR.mkdir(parents=True, exist_ok=True)
DOCS_ARIA2_DIR.mkdir(parents=True, exist_ok=True)

# 1. Parse aria2c --help=#all
help_output = subprocess.check_output(["aria2c", "--help=#all"], text=True)

opt_blocks = re.split(r"\n(?= -| --)", help_output)

class OptionDict(TypedDict):
    name: str
    short_name: str | None
    category: str
    type: str
    default: str | None
    minimum: int | None
    maximum: int | None
    enum_values: list[str] | None
    scope: list[str]
    rpc_supported: bool
    cli_supported: bool
    sensitive: bool
    deprecated: bool
    experimental: bool
    description: str
    documentation_reference: str

options: list[OptionDict] = []

SENSITIVE_NAMES = {
    "rpc-secret", "http-passwd", "http-user", "http-proxy-passwd", "http-proxy-user",
    "ftp-passwd", "ftp-user", "ftp-proxy-passwd", "ftp-proxy-user", "header",
    "rpc-certificate", "rpc-private-key", "ca-certificate", "certificate", "private-key"
}

RPC_CHANGABLE_DOWNLOAD = {
    "dir", "out", "header", "http-user", "http-passwd", "http-proxy", "http-proxy-user", "http-proxy-passwd",
    "http-auth-challenge", "http-no-cache", "http-accept-gzip", "user-agent", "referer", "lowest-speed-limit",
    "max-download-limit", "max-upload-limit", "max-connection-per-server", "split", "min-split-size",
    "log-level", "timeout", "connect-timeout", "max-tries", "retry-wait", "ftp-user", "ftp-passwd",
    "ftp-type", "ftp-pasv", "ftp-proxy", "ftp-proxy-user", "ftp-proxy-passwd", "select-file",
    "bt-max-peers", "bt-request-peer-speed-limit", "bt-remove-unselected-file", "bt-stop-timeout",
    "bt-prioritize-piece", "seed-ratio", "seed-time", "piece-length", "allow-overwrite", "auto-file-renaming",
    "conditional-get", "dry-run", "parameterized-uri", "pause", "check-integrity", "continue"
}

def infer_type(opt_name: str, val_str: str | None, default_str: str | None, desc: str) -> str:
    opt_name_lower = opt_name.lower()
    if val_str:
        v = val_str.lower()
        if "true|false" in v or "true/false" in v:
            return "boolean"
        if "1-600" in v or "0-*" in v or "1-*" in v or "sec" in opt_name_lower or "interval" in opt_name_lower or "timeout" in opt_name_lower:
            if "sec" in opt_name_lower or "timeout" in opt_name_lower or "wait" in opt_name_lower or "interval" in opt_name_lower:
                return "duration"
            return "integer"
        if "bytes" in v or "size" in opt_name_lower or "length" in opt_name_lower:
            return "size"
        if "speed" in opt_name_lower or "limit" in opt_name_lower or "rate" in opt_name_lower:
            return "rate"
        if "path" in opt_name_lower or "file" in opt_name_lower or "dir" in opt_name_lower:
            return "path"
        if "uri" in opt_name_lower or "url" in opt_name_lower:
            return "uri"
        if "," in val_str or "|" in val_str:
            return "enum"
    if default_str:
        d = default_str.lower()
        if d in ("true", "false"):
            return "boolean"
        if d.isdigit():
            if "sec" in opt_name_lower or "timeout" in opt_name_lower or "wait" in opt_name_lower:
                return "duration"
            return "integer"
    if "path" in opt_name_lower or "file" in opt_name_lower or "dir" in opt_name_lower:
        return "path"
    if "header" in opt_name_lower:
        return "header"
    return "string"

for block in opt_blocks:
    lines = block.strip().splitlines()
    if not lines:
        continue
    header_line = lines[0].strip()
    if not (header_line.startswith("-") or header_line.startswith("--")):
        continue
    
    short_name: str | None = None
    long_name: str | None = None
    
    name_part = header_line.split("  ")[0].strip()
    desc_first_line = header_line[len(name_part):].strip()
    
    parts = [p.strip() for p in name_part.split(",")]
    for p in parts:
        if p.startswith("--"):
            long_name = p[2:].split("=")[0].split("[")[0].strip()
        elif p.startswith("-"):
            short_name = p[1:].split("=")[0].split("[")[0].strip()
            
    if not long_name:
        continue
        
    full_text = "\n".join(lines)
    
    tags: list[str] = []
    tags_match = re.search(r"Tags:\s*([^\n]+)", full_text)
    if tags_match:
        tags = [t.strip().lstrip("#") for t in tags_match.group(1).split(",")]
        
    possible_values: str | None = None
    pv_match = re.search(r"Possible Values:\s*([^\n]+)", full_text)
    if pv_match:
        possible_values = pv_match.group(1).strip()
        
    default_val: str | None = None
    def_match = re.search(r"Default:\s*([^\n]+)", full_text)
    if def_match:
        default_val = def_match.group(1).strip()
        
    desc_lines: list[str] = []
    if desc_first_line:
        desc_lines.append(desc_first_line)
    for line in lines[1:]:
        s = line.strip()
        if s.startswith("Tags:") or s.startswith("Possible Values:") or s.startswith("Default:"):
            continue
        if s:
            desc_lines.append(s)
            
    description = " ".join(desc_lines)
    
    category = "basic"
    if tags:
        category = tags[0]
    elif "bt-" in long_name or "torrent" in long_name or "dht" in long_name:
        category = "bittorrent"
    elif "metalink" in long_name:
        category = "metalink"
    elif "http" in long_name:
        category = "http"
    elif "ftp" in long_name:
        category = "ftp"
    elif "rpc" in long_name:
        category = "rpc"
    elif "checksum" in long_name or "hash" in long_name or "piece-hash" in long_name:
        category = "checksum"
        
    opt_type = infer_type(long_name, possible_values, default_val, description)
    
    enum_values: list[str] | None = None
    if possible_values and ("|" in possible_values or "," in possible_values) and opt_type == "enum":
        raw_choices = [c.strip() for c in re.split(r"[,|]", possible_values)]
        enum_values = [c.lstrip("#") for c in raw_choices if c]
        
    min_val: int | None = None
    max_val: int | None = None
    if possible_values:
        range_match = re.match(r"^(\d+)-(\d+|\*)$", possible_values)
        if range_match:
            min_val = int(range_match.group(1))
            if range_match.group(2) != "*":
                max_val = int(range_match.group(2))
                
    scopes: list[str] = ["GLOBAL"]
    if long_name in RPC_CHANGABLE_DOWNLOAD:
        scopes.append("DOWNLOAD")
        
    if "rpc" in category or "rpc" in long_name:
        scopes.append("RPC")
    if "daemon" in long_name or category == "rpc":
        scopes.append("DAEMON")
        
    is_sensitive = long_name in SENSITIVE_NAMES or "passwd" in long_name or "secret" in long_name
    is_deprecated = "deprecated" in tags or "deprecated" in category.lower()
    is_experimental = "experimental" in tags or "experimental" in category.lower()
    
    options.append({
        "name": long_name,
        "short_name": short_name,
        "category": category,
        "type": opt_type,
        "default": default_val,
        "minimum": min_val,
        "maximum": max_val,
        "enum_values": enum_values,
        "scope": scopes,
        "rpc_supported": long_name in RPC_CHANGABLE_DOWNLOAD or "rpc" in scopes or not ("help" in long_name or "version" in long_name),
        "cli_supported": True,
        "sensitive": is_sensitive,
        "deprecated": is_deprecated,
        "experimental": is_experimental,
        "description": description,
        "documentation_reference": f"https://aria2.github.io/manual/en/html/aria2c.html#cmdoption-{long_name}"
    })

print(f"Parsed {len(options)} options from aria2c.")
(SPEC_DIR / "options.json").write_text(json.dumps(options, indent=2), encoding="utf-8")

class RpcParam(TypedDict):
    name: str
    type: str
    required: bool
    description: str

class RpcReturn(TypedDict):
    type: str
    description: str

class RpcMethod(TypedDict):
    name: str
    category: str
    description: str
    parameters: list[RpcParam]
    returns: RpcReturn
    errors: list[int]
    authentication_required: bool

rpc_methods: list[RpcMethod] = [
    {
        "name": "aria2.addUri",
        "category": "downloads",
        "description": "Adds a new download. uris is an array of HTTP/FTP/SFTP/BitTorrent Magnet URIs pointing to the same resource.",
        "parameters": [
            {"name": "uris", "type": "list[str]", "required": True, "description": "Array of URIs for the file."},
            {"name": "options", "type": "dict[str, str]", "required": False, "description": "Download-scoped aria2 options."},
            {"name": "position", "type": "int", "required": False, "description": "Queue position (0-based)."}
        ],
        "returns": {"type": "str", "description": "GID of the newly registered download."},
        "errors": [1, 28],
        "authentication_required": True
    },
    {
        "name": "aria2.addTorrent",
        "category": "bittorrent",
        "description": "Adds a BitTorrent download by uploading a base64-encoded .torrent file.",
        "parameters": [
            {"name": "torrent", "type": "str", "required": True, "description": "Base64-encoded torrent file content."},
            {"name": "uris", "type": "list[str]", "required": False, "description": "Array of web seed URIs."},
            {"name": "options", "type": "dict[str, str]", "required": False, "description": "Download-scoped aria2 options."},
            {"name": "position", "type": "int", "required": False, "description": "Queue position (0-based)."}
        ],
        "returns": {"type": "str", "description": "GID of the newly registered torrent download."},
        "errors": [1, 25, 26, 28],
        "authentication_required": True
    },
    {
        "name": "aria2.addMetalink",
        "category": "metalink",
        "description": "Adds a Metalink download by uploading a base64-encoded Metalink file.",
        "parameters": [
            {"name": "metalink", "type": "str", "required": True, "description": "Base64-encoded Metalink file content."},
            {"name": "options", "type": "dict[str, str]", "required": False, "description": "Download-scoped aria2 options."},
            {"name": "position", "type": "int", "required": False, "description": "Queue position."}
        ],
        "returns": {"type": "list[str]", "description": "Array of GIDs registered from the Metalink file."},
        "errors": [1, 20, 28],
        "authentication_required": True
    },
    {
        "name": "aria2.remove",
        "category": "control",
        "description": "Removes the download denoted by GID. If download is active, stops download first.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "str", "description": "GID of the removed download."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.forceRemove",
        "category": "control",
        "description": "Forcefully removes the download denoted by GID without contacting trackers.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "str", "description": "GID of the removed download."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.pause",
        "category": "control",
        "description": "Pauses the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "str", "description": "GID of the paused download."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.pauseAll",
        "category": "control",
        "description": "Pauses all active and waiting downloads.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.forcePause",
        "category": "control",
        "description": "Forcefully pauses the download denoted by GID without waiting for piece actions.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "str", "description": "GID of the paused download."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.forcePauseAll",
        "category": "control",
        "description": "Forcefully pauses all active and waiting downloads.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.unpause",
        "category": "control",
        "description": "Changes download status from paused to waiting.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "str", "description": "GID of the unpaused download."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.unpauseAll",
        "category": "control",
        "description": "Unpauses all paused downloads.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.tellStatus",
        "category": "inspection",
        "description": "Returns download progress and status for the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."},
            {"name": "keys", "type": "list[str]", "required": False, "description": "Subset of keys to return (e.g. ['gid', 'status', 'completedLength'])."}
        ],
        "returns": {"type": "dict", "description": "Download status dictionary."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getUris",
        "category": "inspection",
        "description": "Returns URIs used in the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "list[dict]", "description": "List of URI objects containing 'uri' and 'status'."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getFiles",
        "category": "inspection",
        "description": "Returns the file list of the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "list[dict]", "description": "List of file structures with index, path, length, completedLength, selected, uris."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getPeers",
        "category": "inspection",
        "description": "Returns peer list of the BitTorrent download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "list[dict]", "description": "List of peer objects (peerId, ip, port, bitfield, amChoking, peerChoking, downloadSpeed, uploadSpeed, seeder)."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getServers",
        "category": "inspection",
        "description": "Returns connected HTTP/FTP/SFTP servers for the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "list[dict]", "description": "List of server structures containing index, servers (uri, currentUri, downloadSpeed)."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.tellActive",
        "category": "inspection",
        "description": "Returns a list of active downloads.",
        "parameters": [
            {"name": "keys", "type": "list[str]", "required": False, "description": "Keys to fetch."}
        ],
        "returns": {"type": "list[dict]", "description": "Array of active download status dictionaries."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.tellWaiting",
        "category": "inspection",
        "description": "Returns a paginated list of waiting downloads, including paused.",
        "parameters": [
            {"name": "offset", "type": "int", "required": True, "description": "Offset from 0."},
            {"name": "num", "type": "int", "required": True, "description": "Maximum number of items to return."},
            {"name": "keys", "type": "list[str]", "required": False, "description": "Keys to fetch."}
        ],
        "returns": {"type": "list[dict]", "description": "Array of waiting download status dictionaries."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.tellStopped",
        "category": "inspection",
        "description": "Returns a paginated list of stopped/completed/error downloads.",
        "parameters": [
            {"name": "offset", "type": "int", "required": True, "description": "Offset from 0."},
            {"name": "num", "type": "int", "required": True, "description": "Maximum number of items to return."},
            {"name": "keys", "type": "list[str]", "required": False, "description": "Keys to fetch."}
        ],
        "returns": {"type": "list[dict]", "description": "Array of stopped download status dictionaries."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.changePosition",
        "category": "queue",
        "description": "Moves the download in the queue.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."},
            {"name": "pos", "type": "int", "required": True, "description": "Target position."},
            {"name": "how", "type": "str", "required": True, "description": "'POS_SET', 'POS_CUR', or 'POS_END'."}
        ],
        "returns": {"type": "int", "description": "Resulting queue position."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.changeUri",
        "category": "downloads",
        "description": "Removes the URIs in delUris and adds the URIs in addUris for the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."},
            {"name": "fileIndex", "type": "int", "required": True, "description": "1-based file index."},
            {"name": "delUris", "type": "list[str]", "required": True, "description": "URIs to delete."},
            {"name": "addUris", "type": "list[str]", "required": True, "description": "URIs to add."},
            {"name": "position", "type": "int", "required": False, "description": "Insertion index."}
        ],
        "returns": {"type": "list[int]", "description": "Array containing number of deleted and added URIs."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getOption",
        "category": "options",
        "description": "Returns download-scoped options for the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."}
        ],
        "returns": {"type": "dict[str, str]", "description": "Key-value map of options."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.changeOption",
        "category": "options",
        "description": "Changes download-scoped options dynamically for the download denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID of the download."},
            {"name": "options", "type": "dict[str, str]", "required": True, "description": "Options dictionary."}
        ],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1, 28],
        "authentication_required": True
    },
    {
        "name": "aria2.getGlobalOption",
        "category": "options",
        "description": "Returns all global options currently applied to the aria2 daemon session.",
        "parameters": [],
        "returns": {"type": "dict[str, str]", "description": "Global options dictionary."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.changeGlobalOption",
        "category": "options",
        "description": "Changes global options dynamically on the active aria2 daemon session.",
        "parameters": [
            {"name": "options", "type": "dict[str, str]", "required": True, "description": "Global options to change."}
        ],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1, 28],
        "authentication_required": True
    },
    {
        "name": "aria2.getGlobalStat",
        "category": "statistics",
        "description": "Returns global download/upload speed and total counts.",
        "parameters": [],
        "returns": {
            "type": "dict",
            "description": "Global stats: downloadSpeed, uploadSpeed, numActive, numWaiting, numStopped, numStoppedTotal."
        },
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.purgeDownloadResult",
        "category": "maintenance",
        "description": "Purges completed/error/removed download results to free memory.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.removeDownloadResult",
        "category": "maintenance",
        "description": "Removes a specific completed/error/removed download result from memory denoted by GID.",
        "parameters": [
            {"name": "gid", "type": "str", "required": True, "description": "GID to remove."}
        ],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.getVersion",
        "category": "system",
        "description": "Returns version information and list of enabled compile-time features.",
        "parameters": [],
        "returns": {
            "type": "dict",
            "description": "Dictionary with 'version' (str) and 'enabledFeatures' (list[str])."
        },
        "errors": [],
        "authentication_required": True
    },
    {
        "name": "aria2.getSessionInfo",
        "category": "system",
        "description": "Returns session ID used for WebSocket notifications.",
        "parameters": [],
        "returns": {
            "type": "dict",
            "description": "Dictionary with 'sessionId' (str)."
        },
        "errors": [],
        "authentication_required": True
    },
    {
        "name": "aria2.shutdown",
        "category": "system",
        "description": "Gracefully shuts down the aria2 daemon.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.forceShutdown",
        "category": "system",
        "description": "Immediately shuts down the aria2 daemon without waiting for active actions.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "aria2.saveSession",
        "category": "system",
        "description": "Saves the current session to the file specified by --save-session.",
        "parameters": [],
        "returns": {"type": "str", "description": "'OK' on success."},
        "errors": [1],
        "authentication_required": True
    },
    {
        "name": "system.multicall",
        "category": "system",
        "description": "Executes multiple RPC methods in a single request transaction.",
        "parameters": [
            {"name": "methods", "type": "list[dict]", "required": True, "description": "Array of method call objects ({'methodName': '...', 'params': [...]})."}
        ],
        "returns": {"type": "list", "description": "Array of return values corresponding to each method call."},
        "errors": [],
        "authentication_required": True
    },
    {
        "name": "system.listMethods",
        "category": "system",
        "description": "Returns all supported RPC methods on the server.",
        "parameters": [],
        "returns": {"type": "list[str]", "description": "Array of method name strings."},
        "errors": [],
        "authentication_required": False
    },
    {
        "name": "system.listNotifications",
        "category": "system",
        "description": "Returns all supported notification event names on the server.",
        "parameters": [],
        "returns": {"type": "list[str]", "description": "Array of notification event name strings."},
        "errors": [],
        "authentication_required": False
    }
]

(SPEC_DIR / "rpc.json").write_text(json.dumps(rpc_methods, indent=2), encoding="utf-8")

# Generate Markdown Docs
opt_md = [
    "# aria2 Authoritative Option Registry",
    "",
    f"> Generated from `spec/aria2/options.json` ({len(options)} options).",
    "",
    "| Option Name | Short | Category | Type | Default | Scope | RPC Dynamic | Sensitive | Description |",
    "| :--- | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |"
]
for o in sorted(options, key=lambda x: x["name"]):
    short = f"`-{o['short_name']}`" if o["short_name"] else "—"
    scope_str = ", ".join(o["scope"])
    rpc_dyn = "Yes" if "DOWNLOAD" in o["scope"] else "No"
    sensitive = "🔒 Yes" if o["sensitive"] else "No"
    def_val = f"`{o['default']}`" if o["default"] else "—"
    desc_str = o["description"][:100] if o["description"] else ""
    opt_md.append(f"| [`--{o['name']}`]({o['documentation_reference']}) | {short} | `{o['category']}` | `{o['type']}` | {def_val} | `{scope_str}` | {rpc_dyn} | {sensitive} | {desc_str}... |")

(DOCS_ARIA2_DIR / "options.md").write_text("\n".join(opt_md), encoding="utf-8")

rpc_md = [
    "# aria2 RPC Methods Specification",
    "",
    f"> Authoritative RPC specification ({len(rpc_methods)} methods).",
    "",
    "| RPC Method | Category | Parameters | Return Type | Auth Required | Description |",
    "| :--- | :--- | :--- | :--- | :---: | :--- |"
]
for m in rpc_methods:
    params_str = ", ".join([f"{p['name']}: {p['type']}" for p in m["parameters"]]) or "none"
    ret_type = m["returns"]["type"]
    auth = "Yes" if m["authentication_required"] else "No"
    rpc_md.append(f"| `{m['name']}` | `{m['category']}` | `{params_str}` | `{ret_type}` | {auth} | {m['description']} |")

(DOCS_ARIA2_DIR / "rpc-methods.md").write_text("\n".join(rpc_md), encoding="utf-8")

print("Regenerated cleanly with full types!")
