from pathlib import Path

from shusha.models.client import Client, XMLRPCClientException
from shusha.models.daemon import Daemon
from shusha.models.database import ShushaDB
from shusha.models.logger import LoggerService
from shusha.models.utilities import download_dir, format_size, format_speed

logger = LoggerService(__name__)
DEFAULT_DIR = download_dir()


class Api:
    def __init__(self, daemon=None):
        self.remote = daemon or Daemon()
        self.client = Client(self.remote)
        self.db = ShushaDB(filename="shusha.db")
        self._downloads = self.db.all()
        self._options = {}
        self._gids = set()
        self.gid = None

    def start_server(self):
        pid = self.remote.start_server()
        logger.log(f"Aria2 server started with PID: {pid}")
        return pid

    def stop_server(self):
        self.remote.stop_server()
        logger.log("Aria2 server stopped.")

    def load_db(self):
        self.db.load()

    def save_db(self):
        self.db.save()

    def persistence(self):
        _downloads = []
        _all_downloads = self.get_all_downloads()

        if _all_downloads:
            _downloads.append(_all_downloads)
            table = self.db.table("downloads")
            try:
                logger.log("Saving session downloads to db:")
                self.db.begin_transaction()
                table.insert_multiple(_downloads)
                self.db.commit_transaction()
            except Exception as e:
                logger.log(f"Error inserting new doc: {e}", level="error")

    def live(self, gid):
        """Live monitoring of a download."""
        new_doc = self.get_download(gid)
        if new_doc:
            self._gids.add(gid)
            table = self.db.table("downloads")
            # print(new_doc)
            try:
                logger.log("Live Inserting new doc")
                table.insert(new_doc)
                self.db.save()
            except Exception as e:
                logger.log(f"Error inserting new doc: {e}", level="error")

    def updatedb(self):
        """Update the db with new download status"""
        for gid in self._gids:
            new_doc = self.get_download(gid)
            if new_doc:
                table = self.db.table("downloads")
                try:
                    logger.log("Updating new doc")
                    table.update(new_data=new_doc, query=gid)
                    self.db.save()
                except Exception as e:
                    logger.log(f"Error updating new doc: {e}", level="error")

    def start_download(self, url, download_dir=None, opts: dict = {}):
        """Start a download and return the GID (Download ID)."""
        download_dir = download_dir or DEFAULT_DIR or Path(__file__).parent
        print(opts)
        if opts:
            options = {**opts, "dir": str(download_dir)}
            print(f"opts: {options}")
        else:
            options = {"dir": str(download_dir)}
            print(f"!opts: {options}")

        try:
            gid = self.client.add_uri([url], options)
            logger.log(f"Download started with GID: {gid}")
            self.gid = gid
            self.live(gid)
            return gid
        except XMLRPCClientException as e:
            logger.log(f"Error starting download: {e}", level="error")
            # Re- the exception for the caller to handle

    def get_download_status(self, gid, keys=None):
        """Get the status of a download given its GID."""
        try:
            return self.client.tell_status(gid=gid, keys=keys)
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting download status for GID {gid}: {e}",
                level="error",
            )

    def monitor_download_progress(self, gid):
        """Monitor and log the progress of a download."""
        try:
            while True:
                status = self.get_download_status(gid)
                is_active = status.get("status")
                if is_active == "active":
                    dl_speed = format_speed(int(status.get("downloadSpeed")))
                    dled_size = format_size(int(status.get("completedLength")))
                    logger.log(
                        f"Download Speed: {dl_speed}/s, Completed Length: {dled_size}"
                    )
                    time.sleep(1)
                else:
                    logger.log("Download completed.")
                    break
        except XMLRPCClientException as e:
            logger.log(
                f"Error monitoring download progress for GID {gid}: {e}",
                level="error",
            )

    def remove(self, gid):
        """Remove a download given its GID."""
        try:
            self.client.remove(gid)
            logger.log(f"Download with GID {gid} removed successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error removing download with GID {gid}: {e}", level="error"
            )

    def remove_f(self, gid):
        """Remove a download given its GID and delete the downloaded file."""
        try:
            self.client.force_remove(gid)
            logger.log(f"Download with GID {gid} stopped successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error stopping download with GID {gid}: {e}", level="error"
            )

    def pause(self, gid):
        """Pause a download given its GID."""
        try:
            if gid:
                self.client.pause(gid)
                logger.log(f"Download with GID {gid} paused successfully.")
            else:
                logger.log(f"No GID:{gid} provided.", level="warning")
        except XMLRPCClientException as e:
            logger.log(
                f"Error pausing download with GID {gid}: {e}", level="error"
            )

    def pause_all(self):
        """Pause all active downloads."""
        try:
            self.client.pause_all()
            logger.log("All active downloads paused successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error pausing all active downloads: {e}", level="error"
            )

    def un_pause(self, gid):
        """Un-pause a download given its GID."""
        try:
            self.client.unpause(gid)
            logger.log(f"Download with GID {gid} un-paused successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error un-pausing download with GID {gid}: {e}", level="error"
            )

    def un_pause_all(self):
        """Un-pause all active downloads."""
        try:
            self.client.unpause_all()
            logger.log("All active downloads un-paused successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error un-pausing all active downloads: {e}", level="error"
            )

    def get_download(self, gid, keys=None):
        """Get detailed information about a specific download."""
        try:
            return self.client.tell_status(gid=gid, keys=keys)
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting download details for GID {gid}: {e}",
                level="error",
            )

    def get_downloads(self, keys=None):
        """Get information about active downloads."""
        try:
            return self.client.tell_active(keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")

    def move(self, gid, pos, how):
        """Change the position of a download in the download queue."""
        try:
            return self.client.change_position(gid, pos, how)
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download with GID {gid}: {e}", level="error"
            )

    def move_to_top(self, gid):
        """Move a download to the top of the download queue."""
        try:
            return self.move(gid, 0, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download to the top: {e}", level="error")

    def move_to_bottom(self, gid):
        """Move a download to the bottom of the download queue."""
        try:
            return self.move(gid, -1, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download to the bottom: {e}", level="error"
            )

    def move_up(self, gid):
        """Move a download up in the download queue."""
        try:
            return self.move(gid, -1, "POS_CUR")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download up: {e}", level="error")

    def move_down(self, gid):
        """Move a download down in the download queue."""
        try:
            return self.move(gid, 1, "POS_CUR")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download down: {e}", level="error")

    def move_to(self, gid, pos):
        """Move a download to a specific position in the download queue."""
        try:
            return self.move(gid, pos, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download to position {pos}: {e}", level="error"
            )

    def get_active(self, keys=None):
        """Get information about active downloads."""
        try:
            return self.client.tell_active(keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")
            return []

    def get_waiting(self, offset, num, keys=None):
        """Get information about waiting downloads."""
        try:
            return self.client.tell_waiting(offset, num, keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting waiting downloads: {e}", level="error")
            return []

    def get_stopped(self, offset, num, keys=None):
        """Get information about stopped downloads."""
        try:
            return self.client.tell_stopped(offset, num, keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting stopped downloads: {e}", level="error")
            return []

    def get_all_downloads(self, keys=None):
        """Get information about all downloads."""
        try:
            all_downloads = []
            waiting = self.get_waiting(0, 1000, keys) or []
            stopped = self.get_stopped(0, 1000, keys) or []
            active = self.get_active(keys) or []

            if waiting and stopped and active or waiting or stopped or active:
                logger.log("Fetched all downloads")
                all_downloads.append(waiting)
                all_downloads.append(stopped)
                all_downloads.append(active)
                return all_downloads
            else:
                logger.log("No downloads found.")
                return []
        except XMLRPCClientException as e:
            logger.log(f"Error getting all downloads: {e}", level="error")
            return []

    def get_stats(self):
        """Get global statistics about downloads."""
        try:
            return self.client.get_global_stat()
        except XMLRPCClientException as e:
            logger.log(f"Error getting global statistics: {e}", level="error")

    def get_version(self):
        """Get version information of Aria2."""
        try:
            return self.client.get_version()
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting Aria2 version information: {e}", level="error"
            )

    def get_session_info(self):
        """Get session information."""
        try:
            return self.client.get_session_info()
        except XMLRPCClientException as e:
            logger.log(f"Error getting session information: {e}", level="error")

    def save_session(self):
        """Save the current session."""
        try:
            if self._options is None:
                self._options = self.get_global_options()
                save_session_option = self._options.get("save-session")
                if save_session_option is not None:
                    return self.client.save_session()
            else:
                logger.log(
                    "Session file not set. Please set the 'save-session' option.",
                    level="warning",
                )

        except XMLRPCClientException as e:
            logger.log(f"Error saving session: {e}", level="error")

    def shutdown(self):
        """Shutdown the Aria2 server."""
        try:
            self.client.shutdown()
            logger.log("Aria2 server shutdown initiated.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error initiating Aria2 server shutdown: {e}", level="error"
            )

    def force_shutdown_aria2(self):
        """Forcefully shutdown the Aria2 server."""
        try:
            return self.client.force_shutdown()
        except XMLRPCClientException as e:
            logger.log(
                f"Error forcefully shutting down Aria2 server: {e}",
                level="error",
            )

    def get_options(self, gid: str):
        """Get options."""
        try:
            return self.client.get_option(gid=gid)
        except XMLRPCClientException as e:
            logger.log(f"Error getting options: {e}", level="error")

    def change_options(self, gid: str, options: dict):
        """Change options."""
        try:
            return self.client.change_option(gid, options)
        except XMLRPCClientException as e:
            logger.log(f"Error changing options: {e}", level="error")

    def get_global_options(self):
        """Get global options."""
        try:
            return self.client.get_global_option()
        except XMLRPCClientException as e:
            logger.log(f"Error getting global options: {e}", level="error")

    def change_global_options(self, options):
        """Change global options."""
        try:
            return self.client.change_global_option(options)
        except XMLRPCClientException as e:
            logger.log(f"Error changing global options: {e}", level="error")


if __name__ == "__main__":
    import time

    # Create an instance of the Api class
    api = Api()

    try:
        pid = api.start_server()

        # Start a download
        url = "https://proof.ovh.net/files/10Mb.dat"
        download_gid = api.start_download(url)

        logger.log(api.get_downloads())
        # Monitor download progress
        logger.log("Monitoring download progress...")
        api.monitor_download_progress(download_gid)

    except Exception as e:
        logger.log(f"An unexpected error occurred: {e}", level="error")

    finally:
        # Stop the download
        logger.log("Stopping the download...")
        try:
            api.pause(download_gid)
        except Exception as e:
            logger.log(f"Error stopping the download: {e}", level="error")

        # Shutdown the Aria2 server
        logger.log("Shutting down Aria2 server...")
        try:
            api.stop_server()
        except Exception as e:
            logger.log(f"Error shutting down Aria2 server: {e}", level="error")
