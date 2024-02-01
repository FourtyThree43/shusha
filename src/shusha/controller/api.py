"""
Aria2 API.

This module defines the ShushaAPI class, which makes use of a XML-RPC client to
provide higher-level methods to interact easily with a remote aria2c process to
manage downloads.

The Aria2 XML-RPC Client API documentation can be found at:
https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, Union

from models.client import Client, XMLRPCClientException
from models.daemon import Daemon
from models.database import ShushaDB
from models.logger import LoggerService
from models.structs_downloads import Download
from models.structs_options import Options
from models.structs_stats import Stats

OptionsType = Union[Options, dict]
OperationResult = Union[bool, XMLRPCClientException]

logger = LoggerService(logger_name="ShushaAPI")


class ShushaAPI:
    """
    A class that provides higher-level methods to interact with a remote aria2c
    process to manage downloads.
    """

    def __init__(
        self,
        daemon: Optional[Daemon] = None,
        client: Optional[Client] = None,
        db: Optional[ShushaDB] = None,
    ):
        self.remote = daemon or Daemon()
        self.client = client or Client(self.remote)
        self.db = db or ShushaDB(filename="shusha.db")

    def __str__(self):
        return f"ShushaAPI(client={self.client}, db={self.db})"

    def start_server(self):
        """Start the Aria2 server."""
        pid = self.remote.start_server()
        logger.log(f"Aria2 server started with PID: {pid}")
        return pid

    def stop_server(self):
        self.remote.stop_server()
        logger.log("Aria2 server stopped.")

    def get_download(self, gid) -> Download:
        """Get a Download object from the database.

        Parameters:
            gid: The GID of the download.

        Returns:
            A Download object representing the download.
        """
        download = self.download_status(gid)

        return download

    def get_downloads(self, gids: list[str] | None = None) -> List[Download]:
        """Get all downloads from the database.

        Returns:
            A list of Download objects representing the downloads.
        """
        # self.db.get_downloads()

        downloads = []

        if gids:
            for gid in gids:
                download = self.download_status(gid)
                downloads.append(download)
        else:
            structs = []
            structs.extend(self.active_downloads())
            structs.extend(self.waiting_downloads())
            structs.extend(self.stopped_downloads())

            if structs:
                downloads = structs

        return downloads

    def add(
        self,
        uri: list[str],
        options: Optional[OptionsType] = None,
        position: Optional[int] = None,
    ) -> List[Download]:
        """Add a download.

        Parameters:
            uri: The URI of the download.
            options: A dictionary of options to be passed to the aria2c process.
            position: The position in the queue where the download should be added.

        Returns:
            A list of Download objects representing the downloads added.
        """
        new_downloads = []

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

    def add_uris(self, uris: list[str], options: OptionsType | None = None, 
                position: int | None = None) -> Download | None:
        """
        Add a download with a URL (or more).

        Parameters:
            uris: A list of URIs that point to the same resource.
            options: An instance of the `Options` class or a dictionary
                    containing aria2c options to create the download with.
            position: The position where to insert the new download in the queue. Start at 0 (top).

        Returns:
            The newly created download object. Returns None if an error occurred.

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
            else:
                return None
        except XMLRPCClientException as e:
            logger.log(f"Error adding URI: {e}", level="error")
    def add_magnet(
        self,
        magnet: str,
        options: Optional[OptionsType] = None,
        position: Optional[int] = None,
    ) -> List[Download]:
        """Add a magnet link.

        Parameters:
            magnet: The magnet link.
            options: A dictionary of options to be passed to the aria2c process.
            position: The position in the queue where the download should be added.

        Returns:
            A list of Download objects representing the downloads added.
        """
        new_downloads = []

        try:
            gid = self.client.add_magnet(magnet, options, position)
            logger.log(f"Magnet link added with GID: {gid}")
            new_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error adding magnet link: {e}", level="error")

        return new_downloads

    def add_torrent(
        self,
        torrent: str,
        options: Optional[OptionsType] = None,
        position: Optional[int] = None,
    ) -> List[Download]:
        """Add a torrent.

        Parameters:
            torrent: The torrent file.
            options: A dictionary of options to be passed to the aria2c process.
            position: The position in the queue where the download should be added.

        Returns:
            A list of Download objects representing the downloads added.
        """
        new_downloads = []

        try:
            gid = self.client.add_torrent(torrent, options, position)
            logger.log(f"Torrent added with GID: {gid}")
            new_downloads.append(self.get_download(gid) if gid else [])

        except XMLRPCClientException as e:
            logger.log(f"Error adding torrent: {e}", level="error")

        return new_downloads

    def retry_downloads(
        self,
        downloads: list[Download],
        clean: bool = False,  # noqa: FBT001,FBT002
    ) -> list[OperationResult]:
        """Resume failed downloads from where they left off with new GIDs.

        Parameters:
            downloads: The list of downloads to remove.
            clean: Whether to remove the aria2 control file as well.

        Returns:
            Success or failure of the operation for each given download.
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
                new_download_gid = self.add_uris([uri], download.options)
            except XMLRPCClientException as error:
                result.append(error)
            else:
                if not new_download_gid:
                    continue

                self.remove(download.gid)
                result.append(True)

        return result

    def remove(self, gid: str, force: bool = False) -> List[Download]:
        """Remove a download.

        Parameters:
            gid: The GID of the download.
            force: True to force removal of the download.

        Returns:
            A list of Download objects representing the downloads removed.
        """
        removed_downloads = []

        try:
            self.client.force_remove if force else self.client.remove

            logger.log(f"Download removed with GID: {gid}")
            removed_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error removing download: {e}", level="error")

        return removed_downloads

    def pause(self, gid: str, force: bool = False) -> List[Download]:
        """Pause a download.

        Parameters:
            gid: The GID of the download.
            force: True to force pause of the download.

        Returns:
            A list of Download objects representing the downloads paused.
        """
        paused_downloads = []

        try:
            self.client.force_pause(gid) if force else self.client.pause(gid)
            logger.log(f"Download paused with GID: {gid}")
            paused_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error pausing download: {e}", level="error")

        return paused_downloads

    def pause_all(self) -> List[Download]:
        """Pause all downloads.

        Returns:
            A list of Download objects representing the downloads paused.
        """
        paused_downloads = []

        try:
            self.client.pause_all()
            logger.log("All downloads paused.")
            paused_downloads.extend(self.get_downloads())

        except XMLRPCClientException as e:
            logger.log(f"Error pausing all downloads: {e}", level="error")

        return paused_downloads

    def resume(self, gid: str) -> List[Download]:
        """Resume a download.

        Parameters:
            gid: The GID of the download.

        Returns:
            A list of Download objects representing the downloads resumed.
        """
        resumed_downloads = []

        try:
            self.client.unpause(gid)
            logger.log(f"Download resumed with GID: {gid}")
            resumed_downloads.append(self.get_download(gid))

        except XMLRPCClientException as e:
            logger.log(f"Error resuming download: {e}", level="error")

        return resumed_downloads

    def resume_all(self) -> List[Download]:
        """Resume all downloads.

        Returns:
            A list of Download objects representing the downloads resumed.
        """
        resumed_downloads = []

        try:
            self.client.unpause_all()
            logger.log("All downloads resumed.")
            resumed_downloads.extend(self.get_downloads())

        except XMLRPCClientException as e:
            logger.log(f"Error resuming all downloads: {e}", level="error")

        return resumed_downloads

    def move(self, download: Download, pos: int) -> int:
        """Move a download in the queue, relatively to its current position.

        Parameters:
            download: The download object to move.
            pos: The relative position (1 to move down, -1 to move up, -2 to move up two times, etc.).

        Returns:
            The new position of the download.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to(self, download: Download, pos: int) -> int:
        """Move a download in the queue, with absolute positioning.

        Parameters:
            download: The download object to move.
            pos: The absolute position in the queue where to move the download. 0 for top, -1 for bottom.

        Returns:
            The new position of the download.
        """
        if pos < 0:
            how = "POS_END"
            pos = -pos
        else:
            how = "POS_SET"
        return self.client.change_position(download.gid, pos, how)

    def move_up(self, download: Download, pos: int = 1) -> int:
        """Move a download up in the queue.

        Parameters:
            download: The download object to move.
            pos: Number of times to move up. With negative values, will move down (use move or move_down instead).

        Returns:
            The new position of the download.
        """
        return self.client.change_position(download.gid, -pos, "POS_CUR")

    def move_down(self, download: Download, pos: int = 1) -> int:
        """Move a download down in the queue.

        Parameters:
            download: The download object to move.
            pos: Number of times to move down. With negative values, will move up (use move or move_up instead).

        Returns:
            The new position of the download.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to_top(self, download: Download) -> int:
        """Move a download to the top of the queue.

        Parameters:
            download: The download object to move.

        Returns:
            The new position of the download.
        """
        return self.client.change_position(download.gid, 0, "POS_SET")

    def move_to_bottom(self, download: Download) -> int:
        """Move a download to the bottom of the queue.

        Parameters:
            download: The download object to move.

        Returns:
            The new position of the download.
        """
        return self.client.change_position(download.gid, 0, "POS_END")

    def purge(self) -> List[Download]:
        """Purge completed and removed downloads from the database.

        Returns:
            A list of Download objects representing the downloads purged.
        """
        purged_downloads = []

        try:
            self.db.purge()
            logger.log("Completed and removed downloads purged.")
            purged_downloads.extend(self.get_downloads())

        except Exception as e:
            logger.log(f"Error purging downloads: {e}", level="error")

        return purged_downloads

    def download_status(
        self, gid: str, keys: list[str] | None = None
    ) -> Download:
        """Get a struct of the download status.

        Args:
            gid: The GID of the download.
            keys: The keys of the struct to be returned.

        Returns:
            A Download object representing the download.
        """
        struct = {}

        try:
            status = self.client.tell_status(gid, keys)
            if status is None:
                status = {}
                logger.log(
                    f"Download not found with GID: {gid}", level="warning"
                )

            struct = status

        except XMLRPCClientException as e:
            logger.log(f"Error getting download status: {e}", level="error")

        return Download(self, struct=struct)

    def active_downloads(self) -> List[Download]:
        """Get all active downloads.

        Returns:
            A list of Download objects representing the active downloads.
        """
        active_downloads = []

        try:
            active = self.client.tell_active()

            if active:
                # logger.log(f"Active downloads retrieved: {active}")
                active_downloads.extend(
                    [Download(self, struct) for struct in active]
                )
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")

        return active_downloads

    def waiting_downloads(self) -> List[Download]:
        """Get all waiting downloads.

        Returns:
            A list of Download objects representing the waiting downloads.
        """
        waiting_downloads = []

        try:
            waiting = self.client.tell_waiting(0, 1000)

            if waiting:
                # logger.log(f"Waiting downloads retrieved: {waiting}")
                waiting_downloads.extend(
                    [Download(self, struct) for struct in waiting]
                )
        except XMLRPCClientException as e:
            logger.log(f"Error getting waiting downloads: {e}", level="error")

        return waiting_downloads

    def stopped_downloads(self) -> List[Download]:
        """Get all stopped downloads.

        Returns:
            A list of Download objects representing the stopped downloads.
        """
        stopped_downloads = []

        try:
            stopped = self.client.tell_stopped(0, 1000)

            if stopped:
                # logger.log(f"Stopped downloads retrieved: {stopped}")
                stopped_downloads.extend(
                    [Download(self, struct) for struct in stopped]
                )
        except XMLRPCClientException as e:
            logger.log(f"Error getting stopped downloads: {e}", level="error")

        return stopped_downloads

    def get_options(self, downloads: list[Download]) -> list[Options]:
        """Get options for each of the given downloads.

        Parameters:
            downloads: The list of downloads to get the options of.

        Returns:
            Options object for each given download.
        """
        # Note: batch/multicall candidate
        options = []
        for download in downloads:
            options.append(
                Options(self, self.client.get_option(download.gid), download)
            )
        return options

    def get_global_options(self) -> Options:
        """Get the global options.

        Returns:
            The global aria2c options.
        """
        return Options(self, self.client.get_global_option())

    def set_options(
        self, options: OptionsType, downloads: list[Download]
    ) -> list[bool]:
        """Set options for specific downloads.

        Parameters:
            options: An instance of the [`Options`] class or a dictionary
                containing aria2c options to create the download with.
            downloads: The list of downloads to set the options for.

        Returns:
            Success or failure of the operation for changing options for each
            given download.
        """
        client_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        # Note: batch/multicall candidate
        results = []
        for download in downloads:
            results.append(
                self.client.change_option(download.gid, client_options) == "OK"
            )
        return results

    def set_global_options(self, options: OptionsType) -> bool:
        """Set global options.

        Parameters:
            options: An instance of the [`Options`][aria2p.options.Options]
                    class or a dictionary containing aria2c options to create
                    the download with.

        Returns:
            Success or failure of the operation for changing global options.
        """
        client_options = (
            options.get_struct() if isinstance(options, Options) else options
        )

        return self.client.change_global_option(client_options) == "OK"

    def get_stats(self) -> Stats:
        """Get the stats of the remote aria2c process.

        Returns:
            The global stats returned by the remote process.
        """
        return Stats(self.client.get_global_stat())

    @staticmethod
    def remove_files(
        downloads: list[Download],
        force: bool = False,  # noqa: FBT001,FBT002
    ) -> list[bool]:
        """Remove downloaded files.

        Parameters:
            downloads:  the list of downloads for which to remove files.
            force: Whether to remove files even if download is not complete.

        Returns:
            Success or failure of the operation for each given download.
        """
        results = []
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
        force: bool = False,  # noqa: FBT001,FBT002
    ) -> list[bool]:
        """Move downloaded files to another directory.

        Parameters:
            downloads:  the list of downloads for which to move files.
            to_directory: The target directory to move files to.
            force: Whether to move files even if download is not complete.

        Returns:
            Success or failure of the operation for each given download.
        """
        if isinstance(to_directory, str):
            to_directory = Path(to_directory)

        # raises FileExistsError when target is already a file
        to_directory.mkdir(parents=True, exist_ok=True)

        results = []
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
        force: bool = False,  # noqa: FBT001,FBT002
    ) -> list[bool]:
        """Copy downloaded files to another directory.

        Parameters:
            downloads:  the list of downloads for which to move files.
            to_directory: The target directory to copy files into.
            force: Whether to move files even if download is not complete.

        Returns:
            Success or failure of the operation for each given download.
        """
        if isinstance(to_directory, str):
            to_directory = Path(to_directory)

        # raises FileExistsError when target is already a file
        to_directory.mkdir(parents=True, exist_ok=True)

        results = []
        for download in downloads:
            if download.is_complete or force:
                for path in download.root_files_paths:
                    if path.is_dir():
                        shutil.copytree(
                            str(path), str(to_directory / path.name)
                        )
                    elif path.is_file():
                        shutil.copy(str(path), str(to_directory))

                results.append(True)
            else:
                results.append(False)
        return results
