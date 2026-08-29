"""
Download lifecycle use cases for Shusha 2.
"""

import contextlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.identifiers import CategoryId, DownloadId, Gid, make_download_id
from shusha.domain.peer import Peer
from shusha.domain.server import Server
from shusha.domain.states import DownloadState
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


@dataclass(frozen=True, slots=True)
class AddDownloadRequest:
    """Input DTO for initiating a download."""

    uris: Sequence[str] | None = None
    torrent_bytes: bytes | None = None
    metalink_bytes: bytes | None = None
    category_id: CategoryId | None = None
    custom_dir: Path | None = None
    options: dict[str, str] | None = None
    position: int | None = None


@dataclass(frozen=True, slots=True)
class DownloadInspection:
    """Detailed inspection snapshot for a download."""

    download: Download
    files: list[DownloadFile]
    peers: list[Peer]
    servers: list[Server]
    options: dict[str, str]


class AddDownloadUseCase:
    """Handles adding single/batch URIs, torrents, or metalinks."""

    def __init__(
        self,
        client: Aria2Client,
        download_repo: DownloadRepository,
        category_repo: CategoryRepository,
        default_dir: Path | None = None,
    ) -> None:
        self.client = client
        self.download_repo = download_repo
        self.category_repo = category_repo
        self.default_dir = default_dir or (Path.home() / "Downloads")

    def execute(self, request: AddDownloadRequest) -> list[DownloadId]:
        """Process and schedule new download tasks."""
        options = dict(request.options or {})
        target_dir = request.custom_dir or self.default_dir
        assigned_category = request.category_id

        # Automatic category matching if not explicitly provided
        if not assigned_category and request.uris:
            first_uri = request.uris[0]
            filename = Path(first_uri).name
            for cat in self.category_repo.list_all():
                if cat.rule.matches(filename, first_uri):
                    assigned_category = cat.id
                    if cat.download_dir:
                        target_dir = Path(cat.download_dir)
                    break

        options["dir"] = str(target_dir)

        gids: list[Gid] = []
        if request.torrent_bytes:
            gid = self.client.add_torrent(
                torrent_content=request.torrent_bytes,
                uris=request.uris,
                options=options,
                position=request.position,
            )
            gids.append(gid)
        elif request.metalink_bytes:
            gids = self.client.add_metalink(
                metalink_content=request.metalink_bytes,
                options=options,
                position=request.position,
            )
        elif request.uris:
            gid = self.client.add_uri(
                uris=request.uris,
                options=options,
                position=request.position,
            )
            gids.append(gid)
        else:
            raise ValueError(
                "AddDownloadRequest must contain uris, torrent_bytes, or metalink_bytes"
            )

        created_ids: list[DownloadId] = []
        for g in gids:
            dl_id = make_download_id(f"dl-{g}")
            # Fetch immediate snapshot from aria2 and persist
            try:
                dl = self.client.tell_status(g)
            except Exception:
                # Fallback if tellStatus has not registered yet
                dl = Download(
                    gid=g,
                    download_id=dl_id,
                    name=Path(request.uris[0]).name
                    if request.uris
                    else f"download-{g}",
                    state=DownloadState.QUEUED,
                    category_id=assigned_category,
                    dir_path=str(target_dir),
                )
            if assigned_category:
                dl = dl.assign_category(assigned_category)
            self.download_repo.save(dl)
            created_ids.append(dl_id)

        return created_ids


class PauseDownloadUseCase:
    """Pauses an active download."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(self, download_id: DownloadId, force: bool = False) -> None:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        self.client.pause(dl.gid, force=force)
        paused_dl = dl.transition_to(DownloadState.PAUSED)
        self.download_repo.save(paused_dl)


class ResumeDownloadUseCase:
    """Resumes a paused download."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(self, download_id: DownloadId) -> None:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        self.client.unpause(dl.gid)
        resumed_dl = dl.transition_to(DownloadState.ACTIVE)
        self.download_repo.save(resumed_dl)


class RemoveDownloadUseCase:
    """Removes a download from aria2 and the database, with optional file deletion."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(
        self, download_id: DownloadId, delete_files: bool = False, force: bool = False
    ) -> None:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        with contextlib.suppress(Exception):
            self.client.remove(dl.gid, force=force)

        with contextlib.suppress(Exception):
            self.client.remove_download_result(dl.gid)

        if delete_files:
            files_to_delete = list(dl.files)
            if not files_to_delete:
                with contextlib.suppress(Exception):
                    fresh = self.client.tell_status(dl.gid)
                    files_to_delete = fresh.files

            for f in files_to_delete:
                p = Path(f.path)
                if p.exists() and p.is_file():
                    with contextlib.suppress(Exception):
                        p.unlink()
                ctl = Path(f"{f.path}.aria2")
                if ctl.exists() and ctl.is_file():
                    with contextlib.suppress(Exception):
                        ctl.unlink()

            if dl.dir_path and dl.name:
                fallback_p = Path(dl.dir_path) / dl.name
                if fallback_p.exists() and fallback_p.is_file():
                    with contextlib.suppress(Exception):
                        fallback_p.unlink()

        self.download_repo.delete(download_id)


class ChangeDownloadOptionsUseCase:
    """Dynamically modifies options on an active download."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(self, download_id: DownloadId, options: dict[str, str]) -> bool:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        return self.client.change_option(dl.gid, options)


class InspectDownloadUseCase:
    """Fetches complete real-time inspection details for a download."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(self, download_id: DownloadId) -> DownloadInspection:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        live_dl = dl
        with contextlib.suppress(Exception):
            live_dl = self.client.tell_status(dl.gid)

        files = live_dl.files
        with contextlib.suppress(Exception):
            files = self.client.get_files(dl.gid)

        peers: list[Peer] = []
        with contextlib.suppress(Exception):
            peers = self.client.get_peers(dl.gid)

        servers: list[Server] = []
        with contextlib.suppress(Exception):
            servers = self.client.get_servers(dl.gid)

        options: dict[str, str] = {}
        with contextlib.suppress(Exception):
            options = self.client.get_option(dl.gid)

        return DownloadInspection(
            download=live_dl,
            files=files,
            peers=peers,
            servers=servers,
            options=options,
        )
