"""
Parsers for translating untyped external aria2 wire payloads into typed Domain entities.
"""

from collections.abc import Mapping
from pathlib import PurePath
from typing import cast

from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource, SourceStatus
from shusha.domain.identifiers import DownloadId, Gid, PeerId, make_gid
from shusha.domain.peer import Peer
from shusha.domain.server import Server
from shusha.domain.states import DownloadState
from shusha.domain.statistics import GlobalStatistics
from shusha.domain.values import Bitfield, BitRate, ByteSize, Duration, Port, Uri


def map_aria2_status_to_state(
    raw_status: str,
    seeder: bool = False,
) -> DownloadState:
    """Map wire-format aria2 status strings to Domain DownloadState."""
    status_lower = raw_status.lower()
    match status_lower:
        case "active":
            return DownloadState.SEEDING if seeder else DownloadState.ACTIVE
        case "waiting":
            return DownloadState.QUEUED
        case "paused":
            return DownloadState.PAUSED
        case "error":
            return DownloadState.FAILED
        case "complete":
            return DownloadState.COMPLETED
        case "removed":
            return DownloadState.REMOVED
        case _:
            return DownloadState.ACTIVE


def parse_download_source(raw: Mapping[str, str]) -> DownloadSource:
    """Parse raw URI item from aria2."""
    uri_str = raw.get("uri", "")
    status_str = raw.get("status", "waiting").upper()
    try:
        status = SourceStatus(status_str)
    except ValueError:
        status = SourceStatus.WAITING
    return DownloadSource(uri=Uri.parse(uri_str), status=status)


def parse_download_file(raw: Mapping[str, object]) -> DownloadFile:
    """Parse raw file item from aria2 tellStatus or getFiles."""
    index = int(str(raw.get("index", 1)))
    path = str(raw.get("path", ""))
    length = ByteSize(int(str(raw.get("length", 0))))
    completed_length = ByteSize(int(str(raw.get("completedLength", 0))))
    selected = str(raw.get("selected", "true")).lower() == "true"

    raw_uris = raw.get("uris", [])
    sources: list[DownloadSource] = []
    if isinstance(raw_uris, list):
        for u in raw_uris:
            if isinstance(u, Mapping):
                typed_u = cast(Mapping[str, str], u)
                sources.append(parse_download_source(typed_u))

    return DownloadFile(
        index=index,
        path=path,
        length=length,
        completed_length=completed_length,
        selected=selected,
        uris=sources,
    )


def parse_peer(raw: Mapping[str, str]) -> Peer:
    """Parse raw peer item from aria2 getPeers."""
    peer_id = PeerId(raw.get("peerId", "unknown"))
    ip = raw.get("ip", "0.0.0.0")
    port = Port(int(raw.get("port", 6881)))
    bitfield_str = raw.get("bitfield", "")
    bitfield = Bitfield(bitfield_str) if bitfield_str else None
    am_choking = raw.get("amChoking", "true").lower() == "true"
    peer_choking = raw.get("peerChoking", "true").lower() == "true"
    download_speed = BitRate(int(raw.get("downloadSpeed", 0)))
    upload_speed = BitRate(int(raw.get("uploadSpeed", 0)))
    seeder = raw.get("seeder", "false").lower() == "true"

    return Peer(
        peer_id=peer_id,
        ip=ip,
        port=port,
        bitfield=bitfield,
        am_choking=am_choking,
        peer_choking=peer_choking,
        download_speed=download_speed,
        upload_speed=upload_speed,
        seeder=seeder,
    )


def parse_server(raw: Mapping[str, object]) -> Server:
    """Parse raw server item from aria2 getServers."""
    servers_list = raw.get("servers", [])
    first_server: Mapping[str, str] = {}
    if (
        isinstance(servers_list, list)
        and servers_list
        and isinstance(servers_list[0], Mapping)
    ):
        first_server = cast(Mapping[str, str], servers_list[0])

    uri_str = first_server.get("uri", "http://unknown")
    cur_uri_str = first_server.get("currentUri", uri_str)
    download_speed = BitRate(int(first_server.get("downloadSpeed", 0)))

    return Server(
        uri=Uri.parse(uri_str),
        current_uri=Uri.parse(cur_uri_str),
        download_speed=download_speed,
    )


def parse_global_stat(raw: Mapping[str, str]) -> GlobalStatistics:
    """Parse global stats dictionary from aria2 getGlobalStat."""
    return GlobalStatistics(
        download_speed=BitRate(int(raw.get("downloadSpeed", 0))),
        upload_speed=BitRate(int(raw.get("uploadSpeed", 0))),
        num_active=int(raw.get("numActive", 0)),
        num_waiting=int(raw.get("numWaiting", 0)),
        num_stopped=int(raw.get("numStopped", 0)),
        num_stopped_total=int(raw.get("numStoppedTotal", 0)),
    )


def parse_download_status(raw: Mapping[str, object]) -> Download:
    """Parse raw tellStatus payload into strongly typed Domain Download entity."""
    gid_str = str(raw.get("gid", ""))
    gid: Gid = make_gid(gid_str)
    download_id = DownloadId(f"dl-{gid_str}")

    bittorrent_dict = raw.get("bittorrent")
    is_torrent = isinstance(bittorrent_dict, Mapping)
    seeder = False

    name = ""
    if is_torrent and isinstance(bittorrent_dict, Mapping):
        info_dict = bittorrent_dict.get("info")
        if isinstance(info_dict, Mapping):
            name = str(info_dict.get("name", ""))

    raw_status = str(raw.get("status", "active"))
    state = map_aria2_status_to_state(raw_status, seeder=seeder)

    total_length_raw = int(str(raw.get("totalLength", 0)))
    total_length = ByteSize(total_length_raw) if total_length_raw > 0 else None
    completed_length = ByteSize(int(str(raw.get("completedLength", 0))))
    download_speed = BitRate(int(str(raw.get("downloadSpeed", 0))))
    upload_speed = BitRate(int(str(raw.get("uploadSpeed", 0))))

    eta = Duration.calculate_eta(completed_length, total_length, download_speed)

    # Files
    raw_files = raw.get("files", [])
    files: list[DownloadFile] = []
    if isinstance(raw_files, list):
        for f in raw_files:
            if isinstance(f, Mapping):
                files.append(parse_download_file(cast(Mapping[str, object], f)))

    if not name and files:
        # Determine name from first file path or URI
        first_path = files[0].path
        if first_path:
            name = PurePath(first_path).name
        elif files[0].uris:
            name = PurePath(files[0].uris[0].uri.path).name

    if not name:
        name = f"download-{gid}"

    # Sources
    sources: list[DownloadSource] = []
    for f in files:
        sources.extend(f.uris)

    bitfield_str = str(raw.get("bitfield", ""))
    bitfield = Bitfield(bitfield_str) if bitfield_str else None

    error_code_raw = raw.get("errorCode")
    error_code = int(str(error_code_raw)) if error_code_raw is not None else None
    error_msg = str(raw.get("errorMessage", "")) if error_code else None

    connections = int(str(raw.get("connections", 0)))
    dir_path = str(raw.get("dir", ""))

    return Download(
        gid=gid,
        download_id=download_id,
        name=name,
        state=state,
        total_length=total_length,
        completed_length=completed_length,
        download_speed=download_speed,
        upload_speed=upload_speed,
        eta=eta,
        files=files,
        sources=sources,
        bitfield=bitfield,
        error_code=error_code,
        error_message=error_msg,
        connections=connections,
        dir_path=dir_path,
        is_torrent=is_torrent,
    )
