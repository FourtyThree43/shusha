"""
High-Level Strongly Typed aria2 Client Adapter.
Converts high-level application requests into typed RPC wire payloads and translates
untyped responses directly into domain entities.
"""

import base64
from collections.abc import Sequence
from typing import Protocol, cast

from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import Gid, make_gid
from shusha.domain.peer import Peer
from shusha.domain.server import Server
from shusha.domain.statistics import GlobalStatistics
from shusha.domain.values import BitRate
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport
from shusha.infrastructure.aria2.option_registry import OptionRegistry
from shusha.infrastructure.aria2.parsers import (
    parse_download_file,
    parse_download_source,
    parse_download_status,
    parse_global_stat,
    parse_peer,
    parse_server,
)


class RpcTransport(Protocol):
    """Protocol for underlying RPC transport implementations."""

    def call(self, method: str, params: list[object] | None = None) -> object: ...

    def multicall(self, calls: list[tuple[str, list[object]]]) -> list[object]: ...


class Aria2Client:
    """Strongly typed aria2 control plane adapter."""

    def __init__(
        self,
        transport: RpcTransport | None = None,
        registry: OptionRegistry | None = None,
    ) -> None:
        self.transport: RpcTransport = transport or JsonRpcTransport()
        self.registry = registry or OptionRegistry.get_default_registry()

    def _prepare_options(self, options: dict[str, str] | None) -> dict[str, str]:
        if not options:
            return {}
        return self.registry.serialize_for_rpc(options)

    # 1. Download Operations
    def add_uri(
        self,
        uris: Sequence[str],
        options: dict[str, str] | None = None,
        position: int | None = None,
    ) -> Gid:
        """Add download from URIs (HTTP/HTTPS/FTP/SFTP/Magnet)."""
        valid_opts = self._prepare_options(options)
        params: list[object] = [list(uris), valid_opts]
        if position is not None:
            params.append(position)

        res = self.transport.call("aria2.addUri", params)
        return make_gid(str(res))

    def add_torrent(
        self,
        torrent_content: bytes,
        uris: Sequence[str] | None = None,
        options: dict[str, str] | None = None,
        position: int | None = None,
    ) -> Gid:
        """Add BitTorrent download by uploading raw .torrent bytes."""
        b64_torrent = base64.b64encode(torrent_content).decode("ascii")
        valid_opts = self._prepare_options(options)
        params: list[object] = [b64_torrent, list(uris or []), valid_opts]
        if position is not None:
            params.append(position)

        res = self.transport.call("aria2.addTorrent", params)
        return make_gid(str(res))

    def add_metalink(
        self,
        metalink_content: bytes,
        options: dict[str, str] | None = None,
        position: int | None = None,
    ) -> list[Gid]:
        """Add Metalink download by uploading raw Metalink XML bytes."""
        b64_metalink = base64.b64encode(metalink_content).decode("ascii")
        valid_opts = self._prepare_options(options)
        params: list[object] = [b64_metalink, valid_opts]
        if position is not None:
            params.append(position)

        res = self.transport.call("aria2.addMetalink", params)
        if isinstance(res, list):
            return [make_gid(str(g)) for g in res]
        return [make_gid(str(res))]

    def remove(self, gid: Gid, force: bool = False) -> Gid:
        """Remove download."""
        method = "aria2.forceRemove" if force else "aria2.remove"
        res = self.transport.call(method, [str(gid)])
        return make_gid(str(res))

    def pause(self, gid: Gid, force: bool = False) -> Gid:
        """Pause download."""
        method = "aria2.forcePause" if force else "aria2.pause"
        res = self.transport.call(method, [str(gid)])
        return make_gid(str(res))

    def pause_all(self, force: bool = False) -> bool:
        """Pause all downloads."""
        method = "aria2.forcePauseAll" if force else "aria2.pauseAll"
        res = self.transport.call(method)
        return str(res) == "OK"

    def unpause(self, gid: Gid) -> Gid:
        """Unpause / resume download."""
        res = self.transport.call("aria2.unpause", [str(gid)])
        return make_gid(str(res))

    def unpause_all(self) -> bool:
        """Unpause all paused downloads."""
        res = self.transport.call("aria2.unpauseAll")
        return str(res) == "OK"

    # 2. Inspection Operations
    def tell_status(self, gid: Gid, keys: Sequence[str] | None = None) -> Download:
        """Get status of a specific download."""
        params: list[object] = [str(gid)]
        if keys:
            params.append(list(keys))
        res = self.transport.call("aria2.tellStatus", params)
        if not isinstance(res, dict):
            raise ValueError(f"Expected dictionary from tellStatus, got {type(res)}")
        return parse_download_status(cast(dict[str, object], res))

    def tell_active(self, keys: Sequence[str] | None = None) -> list[Download]:
        """Fetch all active downloads."""
        params: list[object] = []
        if keys:
            params.append(list(keys))
        res = self.transport.call("aria2.tellActive", params)
        if not isinstance(res, list):
            return []
        return [
            parse_download_status(cast(dict[str, object], item))
            for item in res
            if isinstance(item, dict)
        ]

    def tell_waiting(
        self, offset: int = 0, num: int = 100, keys: Sequence[str] | None = None
    ) -> list[Download]:
        """Fetch paginated waiting/queued downloads."""
        params: list[object] = [offset, num]
        if keys:
            params.append(list(keys))
        res = self.transport.call("aria2.tellWaiting", params)
        if not isinstance(res, list):
            return []
        return [
            parse_download_status(cast(dict[str, object], item))
            for item in res
            if isinstance(item, dict)
        ]

    def tell_stopped(
        self, offset: int = 0, num: int = 100, keys: Sequence[str] | None = None
    ) -> list[Download]:
        """Fetch paginated stopped/completed/error downloads."""
        params: list[object] = [offset, num]
        if keys:
            params.append(list(keys))
        res = self.transport.call("aria2.tellStopped", params)
        if not isinstance(res, list):
            return []
        return [
            parse_download_status(cast(dict[str, object], item))
            for item in res
            if isinstance(item, dict)
        ]

    def get_uris(self, gid: Gid) -> list[DownloadSource]:
        """Fetch source URIs for a download."""
        res = self.transport.call("aria2.getUris", [str(gid)])
        if not isinstance(res, list):
            return []
        return [
            parse_download_source(cast(dict[str, str], u))
            for u in res
            if isinstance(u, dict)
        ]

    def get_files(self, gid: Gid) -> list[DownloadFile]:
        """Fetch file list for a multi-file/torrent download."""
        res = self.transport.call("aria2.getFiles", [str(gid)])
        if not isinstance(res, list):
            return []
        return [
            parse_download_file(cast(dict[str, object], f))
            for f in res
            if isinstance(f, dict)
        ]

    def get_peers(self, gid: Gid) -> list[Peer]:
        """Fetch connected BitTorrent peers."""
        res = self.transport.call("aria2.getPeers", [str(gid)])
        if not isinstance(res, list):
            return []
        return [parse_peer(cast(dict[str, str], p)) for p in res if isinstance(p, dict)]

    def get_servers(self, gid: Gid) -> list[Server]:
        """Fetch connected origin/mirror servers."""
        res = self.transport.call("aria2.getServers", [str(gid)])
        if not isinstance(res, list):
            return []
        return [
            parse_server(cast(dict[str, object], s)) for s in res if isinstance(s, dict)
        ]

    # 3. Position & URI manipulation
    def change_position(self, gid: Gid, pos: int, how: str = "POS_SET") -> int:
        """Change position of a download in queue."""
        res = self.transport.call("aria2.changePosition", [str(gid), pos, how])
        return int(str(res))

    def change_uri(
        self,
        gid: Gid,
        file_index: int,
        del_uris: Sequence[str],
        add_uris: Sequence[str],
        position: int | None = None,
    ) -> tuple[int, int]:
        """Delete and add URIs for an active download."""
        params: list[object] = [str(gid), file_index, list(del_uris), list(add_uris)]
        if position is not None:
            params.append(position)
        res = self.transport.call("aria2.changeUri", params)
        if isinstance(res, list) and len(res) >= 2:
            return int(res[0]), int(res[1])
        return 0, 0

    # 4. Options
    def get_option(self, gid: Gid) -> dict[str, str]:
        """Get download-scoped options."""
        res = self.transport.call("aria2.getOption", [str(gid)])
        if isinstance(res, dict):
            return cast(dict[str, str], res)
        return {}

    def change_option(self, gid: Gid, options: dict[str, str]) -> bool:
        """Change download-scoped options dynamically."""
        valid_opts = self._prepare_options(options)
        res = self.transport.call("aria2.changeOption", [str(gid), valid_opts])
        return str(res) == "OK"

    def get_global_option(self) -> dict[str, str]:
        """Get global daemon options."""
        res = self.transport.call("aria2.getGlobalOption")
        if isinstance(res, dict):
            return cast(dict[str, str], res)
        return {}

    def change_global_option(self, options: dict[str, str]) -> bool:
        """Change global options dynamically."""
        valid_opts = self._prepare_options(options)
        res = self.transport.call("aria2.changeGlobalOption", [valid_opts])
        return str(res) == "OK"

    # 5. Global Stats & System
    def get_global_stat(self) -> GlobalStatistics:
        """Fetch global speed and queue statistics."""
        res = self.transport.call("aria2.getGlobalStat")
        if isinstance(res, dict):
            return parse_global_stat(cast(dict[str, str], res))
        return GlobalStatistics(
            download_speed=BitRate(0),
            upload_speed=BitRate(0),
            num_active=0,
            num_waiting=0,
            num_stopped=0,
            num_stopped_total=0,
        )

    def purge_download_result(self) -> bool:
        """Purge completed/error downloads from daemon memory."""
        res = self.transport.call("aria2.purgeDownloadResult")
        return str(res) == "OK"

    def remove_download_result(self, gid: Gid) -> bool:
        """Remove a single completed/error download from daemon memory."""
        res = self.transport.call("aria2.removeDownloadResult", [str(gid)])
        return str(res) == "OK"

    def get_version(self) -> tuple[str, list[str]]:
        """Fetch daemon version and compile-time enabled features."""
        res = self.transport.call("aria2.getVersion")
        if isinstance(res, dict):
            ver = str(res.get("version", ""))
            features = cast(list[str], res.get("enabledFeatures", []))
            return ver, features
        return "unknown", []

    def get_session_info(self) -> str:
        """Get daemon session ID."""
        res = self.transport.call("aria2.getSessionInfo")
        if isinstance(res, dict):
            return str(res.get("sessionId", ""))
        return ""

    def shutdown(self, force: bool = False) -> bool:
        """Shut down aria2 daemon."""
        method = "aria2.forceShutdown" if force else "aria2.shutdown"
        res = self.transport.call(method)
        return str(res) == "OK"

    def save_session(self) -> bool:
        """Save current aria2 session to disk."""
        res = self.transport.call("aria2.saveSession")
        return str(res) == "OK"
