import platform
import subprocess
import time
from pathlib import Path

from models.logger import LoggerService


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6800
DEFAULT_TIMEOUT = 60.0
BIN_PATH = Path("resources/bin/aria2c.exe")
CONF_PATH = Path("resources/aria2.conf")

logger = LoggerService(logger_name="ShushaServer")


class Daemon:

    def __init__(
        self,
        aria2d=None,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.aria2d = aria2d or BIN_PATH
        self.host = host
        self.port = port
        self.timeout = timeout
        self.process = None

    def _build_command(self):
        command = [
            str(self.aria2d),
            # "--enable-rpc",
            # "--rpc-listen-all",
            # f"--rpc-listen-port={self.port}",
            # "--rpc-max-request-size=2M",
            # # "--rpc-secret=null",
            # "--quiet=true",
            "--conf-path=" + str(CONF_PATH),
        ]
        return command

    def start_server(self):
        if self.process and self.process.poll() is None:
            logger.log("Aria2 server is already running.", level="warning")
            return

        command = self._build_command()
        # NO_WINDOW option avoids opening additional CMD window in MS Windows.
        NO_WINDOW = 0x08000000
        creationflags = NO_WINDOW if platform.system() == "Windows" else 0
        try:
            logger.log("Starting Aria2 server...")
            self.process = subprocess.Popen(
                command,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False,
                creationflags=creationflags,
            )
            time.sleep(2)
            logger.log("Aria2 server started successfully.")
            return self.process.pid
        except FileNotFoundError as e:
            logger.log(f"Aria2 executable not found: {e}")
        except subprocess.CalledProcessError as e:
            logger.log(f"Error starting Aria2 server: {e}")
        except Exception as e:
            logger.log(f"Unexpected error starting Aria2 server: {e}")

    def stop_server(self):
        if not self.process or self.process.poll() is not None:
            logger.log("Aria2 server is not running.", level="warning")
            return

        try:
            logger.log("Stopping Aria2 server...")
            self.process.terminate()
            self.process.wait(timeout=self.timeout)
            logger.log("Aria2 server stopped successfully.")
        except Exception as e:
            logger.log(f"Error stopping Aria2 server: {e}", level="error")
        finally:
            self.process = None

    def restart_server(self):
        try:
            self.stop_server()
            time.sleep(3)
        except Exception as e:
            logger.log(f"Error stopping Aria2 server: {e}", level="error")
        finally:
            return self.start_server()


# Example Usage:
if __name__ == "__main__":
    # logger_service = LoggerService()
    d = Daemon()
    pid = d.start_server()
    logger.log(pid)

    logger.log("Attempting to start the server again...")
    d.start_server()  # test if server is already running

    time.sleep(3)

    pid = d.restart_server()  # test restart
    logger.log(pid)

    d.stop_server()
    logger.log("Attempting to stop the server again...")
    d.stop_server()  # test if server is already stopped
