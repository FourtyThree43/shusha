"""Aria2 API Controller.

This module defines the `ShushaAPI` class, which interacts with an aria2c process via
XML-RPC / JSON-RPC to provide high-level download management, queue control, option
modification, and statistics querying.

The Aria2 XML-RPC Client API reference can be found at:
https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from shusha.models.batch_parser import extract_urls
from shusha.models.client import Client, XMLRPCClientException
from shusha.models.daemon import Daemon
from shusha.models.database import ShushaDB
from shusha.models.logger import LoggerService
from shusha.models.scheduler import BandwidthScheduler
from shusha.models.settings import AppSettings
from shusha.models.structs_downloads import Download
from shusha.models.structs_options import Options
from shusha.models.structs_stats import Stats
from shusha.models.ws_client import Aria2WsClient

OptionsType = Options | dict[str, Any]
OperationResult = bool | XMLRPCClientException

logger = LoggerService(logger_name="ShushaAPI")


class ShushaAPI:
    """High-level API client for managing aria2 downloads and daemon operations."""

    def __init__(
        self,
        daemon: Daemon | None = None,
        client: Client | None = None,
        db: ShushaDB | None = None,
        ws_client: Aria2WsClient | None = None,
        host: str | None = None,
        port: int | None = None,
        secret: str | None = None,
    ) -> None:
        """Initialize the ShushaAPI instance.

        Args:
            daemon: Optional Daemon instance. If None, created using configuration.
            client: Optional Client instance. If None, created from Daemon.
            db: Optional ShushaDB instance for session persistence.
            ws_client: Optional Aria2WsClient for real-time WebSocket events.
            host: Optional host address override for aria2 RPC.
            port: Optional port number override for aria2 RPC.
            secret: Optional secret token override for aria2 RPC authentication.
        """
        settings = AppSettings()
        cfg_host = host or settings.get_aria2_host()
        cfg_port = port or settings.get_aria2_port()
        cfg_secret = secret or settings.get_aria2_secret()

        self.remote = daemon or Daemon(host=cfg_host, port=cfg_port, secret=cfg_secret)
        self.client = client or Client(self.remote, secret=cfg_secret)
        self.db = db or ShushaDB(filename="shusha.db")
        self.ws_client = ws_client or Aria2WsClient(host=cfg_host, port=cfg_port, secret=cfg_secret)
        self.scheduler = BandwidthScheduler()

    def connect_ws(self) -> bool:
        """Connect WebSocket client for real-time aria2 notifications."""
        return self.ws_client.connect()

    def on_event(self, event_name: str, callback: Any) -> None:
        """Register a callback for an aria2 notification event."""
        self.ws_client.on(event_name, callback)

    def off_event(self, event_name: str, callback: Any = None) -> None:
        """Unregister a callback for an aria2 notification event."""
        self.ws_client.off(event_name, callback)

    def add_batch_urls(
        self,
        text_or_urls: str | list[str],
        options: OptionsType | None = None,
    ) -> list[Download]:
        """Parse and add batch URLs in sequence.

        Args:
            text_or_urls: Multi-line text or list of URL strings.
            options: Optional download configuration options.

        Returns:
            List of successfully added Download objects.
        """
        urls = extract_urls(text_or_urls) if isinstance(text_or_urls, str) else text_or_urls
        added: list[Download] = []
        for u in urls:
            dl = self.add_uris([u], options=options)
            if dl:
                added.append(dl)
        return added

    def __str__(self) -> str:
        """Return human-readable string representation of the API instance."""
        return f"ShushaAPI(client={self.client}, db={self.db})"

    def start_server(self) -> int | None:
        """Start the background Aria2 daemon server.

        Returns:
            The process PID if started successfully, or None if already running or remote.
        """
        pid = self.remote.start_server()
        logger.log(f"Aria2 server started with PID: {pid}")
        return pid

    def stop_server(self) -> None:
        """Stop the background Aria2 daemon server."""
        self.remote.stop_server()
        logger.log("Aria2 server stopped.")

    def get_download(self, gid: str) -> Download:
        """Get a Download object representing the specified GID.

        Args:
            gid: The unique GID of the download.

        Returns:
            A Download instance representing the download status and metadata.
        """
        download = self.download_status(gid)
        return download

    def get_downloads(self, gids: list[str] | None = None) -> list[Download]:
        """Retrieve downloads from the daemon.

        Args:
            gids: Optional list of GIDs to fetch. If None, fetches active, waiting,
                and stopped downloads.

        Returns:
            A list of Download objects matching the requested GIDs or all current downloads.
        """
        downloads: list[Download] = []

        if gids:
            for gid in gids:
                download = self.download_status(gid)
                downloads.append(download)
        else:
            structs: list[Download] = []
            structs.extend(self.active_downloads())
            structs.extend(self.waiting_downloads())
            structs.extend(self.stopped_downloads())

            if structs:
                downloads = structs

        return downloads

    def add(
        self,
        uri: list[str],
        options: OptionsType | None = None,
        position: int | None = None,
    ) -> list[Download]:
        """Add a new download from a list of mirror URIs.

        Args:
            uri: List of mirror URIs pointing to the same file.
            options: Optional dictionary or Options object of download configuration.
            position: Optional position in the queue (0-indexed).

        Returns:
            A list containing the newly created Download object, or empty list on error.
        """
        new_downloads: list[Download] = []

        if options is None:
            options = {}

        client_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        try:
            gid = self.client.add_uri(uri, client_options, position)
            if gid:
                logger.log(f"Download added with GID: {gid}")
                new_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error adding download: {e}", level="error")

        return new_downloads

    def add_uris(
        self,
        uris: list[str],
        options: OptionsType | None = None,
        position: int | None = None,
    ) -> Download | None:
        """Add a download from one or more URIs.

        Args:
            uris: List of URIs pointing to the resource to download.
            options: Optional Options object or dict of aria2 options.
            position: Optional 0-indexed position where the download should be placed.

        Returns:
            The newly created Download object, or None if the request failed.
        """
        if options is None:
            options = {}

        aria2c_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        try:
            gid = self.client.add_uri(uris, aria2c_options, position)
            logger.log(f"Download added with GID: {gid}")
            if gid:
                return self.get_download(gid)
            return None
        except XMLRPCClientException as e:
            logger.log(f"Error adding URI: {e}", level="error")
            return None

    def add_magnet(
        self,
        magnet: str,
        options: OptionsType | None = None,
        position: int | None = None,
    ) -> list[Download]:
        """Add a download using a BitTorrent Magnet URI.

        Args:
            magnet: The magnet link string.
            options: Optional dictionary or Options object for download configuration.
            position: Optional queue position.

        Returns:
            A list containing the created Download object, or empty on failure.
        """
        new_downloads: list[Download] = []

        try:
            gid = self.client.add_magnet(magnet, options, position)
            logger.log(f"Magnet link added with GID: {gid}")
            if gid:
                new_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error adding magnet link: {e}", level="error")

        return new_downloads

    def add_torrent(
        self,
        torrent: str,
        options: OptionsType | None = None,
        position: int | None = None,
    ) -> list[Download]:
        """Add a BitTorrent download from a `.torrent` file path.

        Args:
            torrent: Path to the local .torrent file.
            options: Optional dictionary or Options object.
            position: Optional queue insertion index.

        Returns:
            A list containing the created Download object, or empty list on error.
        """
        new_downloads: list[Download] = []

        try:
            gid = self.client.add_torrent(torrent, options, position)
            logger.log(f"Torrent added with GID: {gid}")
            if gid:
                dl = self.get_download(gid)
                if dl:
                    new_downloads.append(dl)

        except XMLRPCClientException as e:
            logger.log(f"Error adding torrent: {e}", level="error")

        return new_downloads

    def add_metalink(
        self,
        metalink: str,
        options: OptionsType | None = None,
        position: int | None = None,
    ) -> list[Download]:
        """Add a Metalink download from a `.metalink` or `.meta4` file path.

        Args:
            metalink: Path to the local metalink file.
            options: Optional dictionary or Options object.
            position: Optional queue insertion index.

        Returns:
            A list of Download objects created by the metalink descriptor.
        """
        new_downloads: list[Download] = []

        try:
            gids = self.client.add_metalink(metalink, options, position)
            logger.log(f"Metalink added: {gids}")
            if isinstance(gids, list):
                for gid in gids:
                    dl = self.get_download(gid)
                    if dl:
                        new_downloads.append(dl)
            elif gids:
                dl = self.get_download(gids)
                if dl:
                    new_downloads.append(dl)

        except XMLRPCClientException as e:
            logger.log(f"Error adding metalink: {e}", level="error")

        return new_downloads

    def retry_downloads(
        self,
        downloads: list[Download],
        clean: bool = False,
    ) -> list[OperationResult]:
        """Resume failed downloads by adding new URI tasks and removing failed entries.

        Args:
            downloads: List of Download instances to retry.
            clean: Whether to delete associated aria2 control files.

        Returns:
            List of operation results (True on success, XMLRPCClientException on failure).
        """
        result: list[OperationResult] = []

        for download in downloads:
            if not download.has_failed:
                continue
            try:
                uri = download.files[0].uris[0]["uri"]
            except IndexError:
                continue
            try:
                new_download = self.add_uris([uri], download.options)
            except XMLRPCClientException as error:
                result.append(error)
            else:
                if not new_download:
                    continue

                self.remove(download.gid)
                result.append(True)

        return result

    def remove(
        self, gid: str, force: bool = False, files: bool = False
    ) -> list[Download]:
        """Remove a download from the aria2 queue.

        Args:
            gid: The unique GID of the download to remove.
            force: If True, forces removal without waiting for daemon handshake.
            files: If True, deletes downloaded files from local storage.

        Returns:
            A list containing the removed Download object, or empty on failure.
        """
        removed_downloads: list[Download] = []

        try:
            download = self.get_download(gid)
            if force:
                self.client.force_remove(gid)
            else:
                self.client.remove(gid)

            if files and download:
                for file_obj in download.files:
                    if file_obj.path and file_obj.path.exists():
                        file_obj.path.unlink(missing_ok=True)

            logger.log(f"Download removed with GID: {gid}")
            if download:
                removed_downloads.append(download)

        except XMLRPCClientException as e:
            logger.log(f"Error removing download: {e}", level="error")

        return removed_downloads

    def unpause_all(self) -> list[Download]:
        """Resume all paused downloads (alias for `resume_all`).

        Returns:
            List of active downloads after resumption.
        """
        return self.resume_all()

    def pause(self, gid: str, force: bool = False) -> list[Download]:
        """Pause an active download.

        Args:
            gid: Unique GID of the download to pause.
            force: If True, forces immediate pause without waiting for cleanup.

        Returns:
            List containing the paused Download instance.
        """
        paused_downloads: list[Download] = []

        try:
            self.client.force_pause(gid) if force else self.client.pause(gid)
            logger.log(f"Download paused with GID: {gid}")
            paused_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error pausing download: {e}", level="error")

        return paused_downloads

    def pause_all(self) -> list[Download]:
        """Pause all active downloads across the daemon.

        Returns:
            List of all current downloads.
        """
        paused_downloads: list[Download] = []

        try:
            self.client.pause_all()
            logger.log("All downloads paused.")
            paused_downloads.extend(self.get_downloads())

        except XMLRPCClientException as e:
            logger.log(f"Error pausing all downloads: {e}", level="error")

        return paused_downloads

    def resume(self, gid: str) -> list[Download]:
        """Resume a paused download.

        Args:
            gid: Unique GID of the download to resume.

        Returns:
            List containing the resumed Download instance.
        """
        resumed_downloads: list[Download] = []

        try:
            self.client.unpause(gid)
            logger.log(f"Download resumed with GID: {gid}")
            resumed_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error resuming download: {e}", level="error")

        return resumed_downloads

    def resume_all(self) -> list[Download]:
        """Resume all paused downloads across the daemon.

        Returns:
            List of all current downloads.
        """
        resumed_downloads: list[Download] = []

        try:
            self.client.unpause_all()
            logger.log("All downloads resumed.")
            resumed_downloads.extend(self.get_downloads())

        except XMLRPCClientException as e:
            logger.log(f"Error resuming all downloads: {e}", level="error")

        return resumed_downloads

    def move(self, download: Download, pos: int) -> int:
        """Move a download in the queue relative to its current position.

        Args:
            download: The Download instance to move.
            pos: Relative offset (positive moves down, negative moves up).

        Returns:
            The resulting 0-indexed queue position.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to(self, download: Download, pos: int) -> int:
        """Move a download to an absolute position in the queue.

        Args:
            download: The Download instance to move.
            pos: Absolute target position (0 for top, negative for offset from end).

        Returns:
            The resulting 0-indexed queue position.
        """
        if pos < 0:
            how = "POS_END"
            pos = -pos
        else:
            how = "POS_SET"
        return self.client.change_position(download.gid, pos, how)

    def move_up(self, download: Download, pos: int = 1) -> int:
        """Move a download up towards the top of the queue.

        Args:
            download: The Download instance to move.
            pos: Number of positions to move up (default 1).

        Returns:
            The resulting 0-indexed queue position.
        """
        return self.client.change_position(download.gid, -pos, "POS_CUR")

    def move_down(self, download: Download, pos: int = 1) -> int:
        """Move a download down towards the bottom of the queue.

        Args:
            download: The Download instance to move.
            pos: Number of positions to move down (default 1).

        Returns:
            The resulting 0-indexed queue position.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to_top(self, download: Download) -> int:
        """Move a download directly to the top of the queue.

        Args:
            download: The Download instance to move.

        Returns:
            The resulting 0-indexed queue position (0).
        """
        return self.client.change_position(download.gid, 0, "POS_SET")

    def move_to_bottom(self, download: Download) -> int:
        """Move a download directly to the bottom of the queue.

        Args:
            download: The Download instance to move.

        Returns:
            The resulting 0-indexed queue position.
        """
        return self.client.change_position(download.gid, 0, "POS_END")

    def purge(self) -> list[Download]:
        """Purge completed, stopped, and removed download records from database and daemon.

        Returns:
            List of remaining active/waiting downloads.
        """
        purged_downloads: list[Download] = []

        try:
            self.db.purge()
            self.client.purge_download_result()
            logger.log("Completed and removed downloads purged.")
            purged_downloads.extend(self.get_downloads())

        except Exception as e:
            logger.log(f"Error purging downloads: {e}", level="error")

        return purged_downloads

    def download_status(self, gid: str, keys: list[str] | None = None) -> Download:
        """Query detailed download status for a single GID.

        Args:
            gid: Unique GID of the download.
            keys: Optional list of status keys to return (e.g. ['status', 'totalLength']).

        Returns:
            A Download instance containing the queried properties.
        """
        struct: dict[str, Any] = {}

        try:
            status = self.client.tell_status(gid, keys)
            if status is None:
                status = {}
                logger.log(f"Download not found with GID: {gid}", level="warning")

            struct = status

        except XMLRPCClientException as e:
            logger.log(f"Error getting download status: {e}", level="error")

        return Download(self, struct=struct)

    def active_downloads(self) -> list[Download]:
        """Fetch all currently active downloads.

        Returns:
            List of active Download instances.
        """
        active_downloads: list[Download] = []

        try:
            active = self.client.tell_active()

            if active:
                active_downloads.extend([Download(self, struct) for struct in active])
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")

        return active_downloads

    def waiting_downloads(self) -> list[Download]:
        """Fetch all waiting (queued/paused) downloads.

        Returns:
            List of waiting Download instances.
        """
        waiting_downloads: list[Download] = []

        try:
            waiting = self.client.tell_waiting(0, 1000)

            if waiting:
                waiting_downloads.extend([Download(self, struct) for struct in waiting])
        except XMLRPCClientException as e:
            logger.log(f"Error getting waiting downloads: {e}", level="error")

        return waiting_downloads

    def stopped_downloads(self) -> list[Download]:
        """Fetch all stopped (completed/failed/removed) downloads.

        Returns:
            List of stopped Download instances.
        """
        stopped_downloads: list[Download] = []

        try:
            stopped = self.client.tell_stopped(0, 1000)

            if stopped:
                stopped_downloads.extend([Download(self, struct) for struct in stopped])
        except XMLRPCClientException as e:
            logger.log(f"Error getting stopped downloads: {e}", level="error")

        return stopped_downloads

    def get_options(self, downloads: list[Download]) -> list[Options]:
        """Retrieve the configuration options for a list of downloads.

        Args:
            downloads: List of Download objects to fetch options for.

        Returns:
            List of Options instances corresponding to each download.
        """
        options: list[Options] = []
        for download in downloads:
            options.append(
                Options(self, self.client.get_option(download.gid), download)
            )
        return options

    def get_global_options(self) -> Options:
        """Retrieve the daemon-wide global options.

        Returns:
            An Options object containing global daemon settings.
        """
        return Options(self, self.client.get_global_option())

    def set_options(
        self, options: OptionsType, downloads: list[Download]
    ) -> list[bool]:
        """Apply option modifications to specific downloads.

        Args:
            options: Dictionary or Options object with modified options.
            downloads: List of Download targets.

        Returns:
            List of booleans indicating success for each download.
        """
        client_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        results: list[bool] = []
        for download in downloads:
            results.append(
                self.client.change_option(download.gid, client_options) == "OK"
            )
        return results

    def set_global_options(self, options: OptionsType) -> bool:
        """Apply option modifications globally to the daemon.

        Args:
            options: Dictionary or Options object with modified global options.

        Returns:
            True if applied successfully, False otherwise.
        """
        client_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        return self.client.change_global_option(client_options) == "OK"

    def get_stats(self) -> Stats:
        """Query daemon global transfer statistics and active task counts.

        Returns:
            A Stats object containing download/upload speeds and connection counts.
        """
        try:
            raw = self.client.get_global_stat()
            return Stats.from_dict(raw) if hasattr(Stats, "from_dict") else Stats(raw)
        except Exception as e:
            logger.log(f"Stats lookup error: {e}", level="debug")
            return Stats.from_dict({}) if hasattr(Stats, "from_dict") else Stats({})

    def get_peers(self, gid: str) -> list[dict[str, Any]]:
        """Retrieve connected BitTorrent peers for a download task.

        Args:
            gid: Unique GID of the torrent download.

        Returns:
            List of peer information dictionaries (IP, port, client, speed).
        """
        try:
            peers = self.client.get_peers(gid)
            return peers if isinstance(peers, list) else []
        except Exception as e:
            logger.log(f"Error fetching peers for {gid}: {e}", level="debug")
            return []

    def get_servers(self, gid: str) -> list[dict[str, Any]]:
        """Retrieve mirror server connection statistics for a download task.

        Args:
            gid: Unique GID of the download.

        Returns:
            List of server connection dictionaries (URI, current speed).
        """
        try:
            servers = self.client.get_servers(gid)
            return servers if isinstance(servers, list) else []
        except Exception as e:
            logger.log(f"Error fetching servers for {gid}: {e}", level="debug")
            return []

    def change_uri(
        self,
        gid: str,
        file_index: int = 1,
        del_uris: list[str] | None = None,
        add_uris: list[str] | None = None,
        position: int | None = None,
    ) -> list[int]:
        """Dynamically add or remove mirror URIs for an active download.

        Args:
            gid: Unique GID of the download.
            file_index: 1-based index of the target file within the download.
            del_uris: Optional list of URI strings to remove.
            add_uris: Optional list of URI strings to append.
            position: Optional index to insert new URIs at.

        Returns:
            A 2-element list `[deleted_count, added_count]`.
        """
        try:
            res = self.client.change_uri(
                gid, file_index, del_uris or [], add_uris or [], position
            )
            return res if isinstance(res, list) else [0, 0]
        except Exception as e:
            logger.log(f"Error changing URIs for {gid}: {e}", level="error")
            return [0, 0]

    def change_download_speed_limits(
        self,
        gid: str,
        max_download: str | None = None,
        max_upload: str | None = None,
    ) -> bool:
        """Adjust maximum download and upload speed limits for a specific task.

        Args:
            gid: Unique GID of the download.
            max_download: Speed limit string (e.g. '500K', '2M', '0' for unlimited).
            max_upload: Upload speed limit string.

        Returns:
            True if the limits were successfully updated, False otherwise.
        """
        options: dict[str, str] = {}
        if max_download is not None:
            options["max-download-limit"] = max_download
        if max_upload is not None:
            options["max-upload-limit"] = max_upload
        if not options:
            return True
        try:
            return self.client.change_option(gid, options) == "OK"
        except Exception as e:
            logger.log(f"Error setting speed limits on {gid}: {e}", level="error")
            return False

    @staticmethod
    def remove_files(
        downloads: list[Download],
        force: bool = False,
    ) -> list[bool]:
        """Remove downloaded files and directories from local disk.

        Args:
            downloads: List of Download instances whose files should be deleted.
            force: If True, delete even if download status is incomplete.

        Returns:
            List of booleans representing removal success for each download.
        """
        results: list[bool] = []
        for download in downloads:
            if download.is_complete or force:
                for path in download.root_files_paths:
                    if path.is_dir():
                        try:
                            shutil.rmtree(str(path))
                        except OSError as error:
                            logger.log(
                                f"Could not delete directory '{path}'",
                                level="error",
                            )
                            logger.log(error, level="error")
                            results.append(False)
                        else:
                            results.append(True)
                    else:
                        try:
                            path.unlink()
                        except FileNotFoundError as error:
                            logger.log(
                                f"File '{path}' did not exist when trying to delete it",
                                level="warning",
                            )
                            logger.log(error, level="error")
                        results.append(True)
            else:
                results.append(False)
        return results

    @staticmethod
    def move_files(
        downloads: list[Download],
        to_directory: str | Path,
        force: bool = False,
    ) -> list[bool]:
        """Move completed download files to a target destination directory.

        Args:
            downloads: List of Download objects whose files should be moved.
            to_directory: Destination directory path.
            force: If True, move files even if download is incomplete.

        Returns:
            List of booleans representing move success for each download.
        """
        if isinstance(to_directory, str):
            to_directory = Path(to_directory)

        to_directory.mkdir(parents=True, exist_ok=True)

        results: list[bool] = []
        for download in downloads:
            if download.is_complete or force:
                for path in download.root_files_paths:
                    shutil.move(str(path), str(to_directory))
                results.append(True)
            else:
                results.append(False)
        return results

    @staticmethod
    def copy_files(
        downloads: list[Download],
        to_directory: str | Path,
        force: bool = False,
    ) -> list[bool]:
        """Copy completed download files to a target destination directory.

        Args:
            downloads: List of Download objects whose files should be copied.
            to_directory: Destination directory path.
            force: If True, copy files even if download is incomplete.

        Returns:
            List of booleans representing copy success for each download.
        """
        if isinstance(to_directory, str):
            to_directory = Path(to_directory)

        to_directory.mkdir(parents=True, exist_ok=True)

        results: list[bool] = []
        for download in downloads:
            if download.is_complete or force:
                for path in download.root_files_paths:
                    if path.is_dir():
                        shutil.copytree(str(path), str(to_directory / path.name))
                    elif path.is_file():
                        shutil.copy(str(path), str(to_directory))

                results.append(True)
            else:
                results.append(False)
        return results
