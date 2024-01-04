from pathlib import Path

from client import Client, XMLRPCClientException
from daemon import Daemon, logger


class HelperUtilities:
    @staticmethod
    def sizeof_fmt(num, delim=" ", suffix="B"):
        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < 1024.0:
                return f"{num:3.1f}{delim}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}{delim}Yi{suffix}"


class Api:
    def __init__(self, daemon=None):
        self.remote = daemon or Daemon()
        self.client = Client(self.remote)

    def start_server(self):
        pid = self.remote.start_server()
        logger.log(f"Aria2 server started with PID: {pid}")
        return pid

    def stop_server(self):
        self.remote.stop_server()
        logger.log("Aria2 server stopped.")

    def start_download(self, url, download_dir=None):
        """Start a download and return the GID (Download ID)."""
        download_dir = download_dir or Path(__file__).parent
        try:
            gid = self.client.add_uri([url], {"dir": str(download_dir)})
            logger.log(f"Download started with GID: {gid}")
            return gid
        except XMLRPCClientException as e:
            logger.log(f"Error starting download: {e}", level="error")
            raise  # Re-raise the exception for the caller to handle

    def get_download_status(self, gid):
        """Get the status of a download given its GID."""
        try:
            return self.client.tell_status(gid=gid)
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting download status for GID {gid}: {e}",
                level="error",
            )
            raise

    def monitor_download_progress(self, gid):
        """Monitor and log the progress of a download."""
        try:
            while True:
                status = self.get_download_status(gid)
                is_active = status.get("status")
                if is_active == "active":
                    dl_speed = HelperUtilities.sizeof_fmt(
                        int(status.get("downloadSpeed"))
                    )
                    dled_size = HelperUtilities.sizeof_fmt(
                        int(status.get("completedLength"))
                    )
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
            raise

    def stop_download(self, gid):
        """Stop a download given its GID."""
        try:
            self.client.force_remove(gid)
            logger.log(f"Download with GID {gid} stopped successfully.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error stopping download with GID {gid}: {e}", level="error"
            )
            raise

    def shutdown(self):
        """Shutdown the Aria2 server."""
        try:
            self.client.shutdown()
            logger.log("Aria2 server shutdown initiated.")
        except XMLRPCClientException as e:
            logger.log(
                f"Error initiating Aria2 server shutdown: {e}", level="error"
            )
            raise

    def get_download(self, gid):
        """Get detailed information about a specific download."""
        try:
            return self.client.tell_status(gid)
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting download details for GID {gid}: {e}",
                level="error",
            )
            raise

    def get_downloads(self, keys=None):
        """Get information about active downloads."""
        try:
            return self.client.tell_active(keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")
            raise

    def move(self, gid, pos, how):
        """Change the position of a download in the download queue."""
        try:
            return self.client.change_position(gid, pos, how)
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download with GID {gid}: {e}", level="error"
            )
            raise

    def move_to_top(self, gid):
        """Move a download to the top of the download queue."""
        try:
            return self.move(gid, 0, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download to the top: {e}", level="error")
            raise

    def move_to_bottom(self, gid):
        """Move a download to the bottom of the download queue."""
        try:
            return self.move(gid, -1, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download to the bottom: {e}", level="error"
            )
            raise

    def move_up(self, gid):
        """Move a download up in the download queue."""
        try:
            return self.move(gid, -1, "POS_CUR")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download up: {e}", level="error")
            raise

    def move_down(self, gid):
        """Move a download down in the download queue."""
        try:
            return self.move(gid, 1, "POS_CUR")
        except XMLRPCClientException as e:
            logger.log(f"Error moving download down: {e}", level="error")
            raise

    def move_to(self, gid, pos):
        """Move a download to a specific position in the download queue."""
        try:
            return self.move(gid, pos, "POS_SET")
        except XMLRPCClientException as e:
            logger.log(
                f"Error moving download to position {pos}: {e}", level="error"
            )
            raise

    def get_active_downloads(self, keys=None):
        """Get information about active downloads."""
        try:
            return self.client.tell_active(keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting active downloads: {e}", level="error")
            raise

    def get_waiting_downloads(self, offset, num, keys=None):
        """Get information about waiting downloads."""
        try:
            return self.client.tell_waiting(offset, num, keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting waiting downloads: {e}", level="error")
            raise

    def get_stopped_downloads(self, offset, num, keys=None):
        """Get information about stopped downloads."""
        try:
            return self.client.tell_stopped(offset, num, keys)
        except XMLRPCClientException as e:
            logger.log(f"Error getting stopped downloads: {e}", level="error")
            raise

    def get_global_stat(self):
        """Get global statistics about downloads."""
        try:
            return self.client.get_global_stat()
        except XMLRPCClientException as e:
            logger.log(f"Error getting global statistics: {e}", level="error")
            raise

    def get_version(self):
        """Get version information of Aria2."""
        try:
            return self.client.get_version()
        except XMLRPCClientException as e:
            logger.log(
                f"Error getting Aria2 version information: {e}", level="error"
            )
            raise

    def get_session_info(self):
        """Get session information."""
        try:
            return self.client.get_session_info()
        except XMLRPCClientException as e:
            logger.log(f"Error getting session information: {e}", level="error")
            raise

    def save_session(self):
        """Save the current session."""
        try:
            return self.client.save_session()
        except XMLRPCClientException as e:
            logger.log(f"Error saving session: {e}", level="error")
            raise

    # def shutdown_aria2(self):
    #     """Shutdown the Aria2 server."""
    #     try:
    #         return self.client.shutdown()
    #     except XMLRPCClientException as e:
    #         logger.log(f"Error initiating Aria2 server shutdown: {e}", level="error")
    #         raise

    def force_shutdown_aria2(self):
        """Forcefully shutdown the Aria2 server."""
        try:
            return self.client.force_shutdown()
        except XMLRPCClientException as e:
            logger.log(
                f"Error forcefully shutting down Aria2 server: {e}",
                level="error",
            )
            raise

    def get_global_options(self):
        """Get global options."""
        try:
            return self.client.get_global_option()
        except XMLRPCClientException as e:
            logger.log(f"Error getting global options: {e}", level="error")
            raise

    def change_global_options(self, options):
        """Change global options."""
        try:
            return self.client.change_global_option(options)
        except XMLRPCClientException as e:
            logger.log(f"Error changing global options: {e}", level="error")
            raise


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
            api.stop_download(download_gid)
        except Exception as e:
            logger.log(f"Error stopping the download: {e}", level="error")

        # Shutdown the Aria2 server
        logger.log("Shutting down Aria2 server...")
        try:
            api.stop_server()
        except Exception as e:
            logger.log(f"Error shutting down Aria2 server: {e}", level="error")
