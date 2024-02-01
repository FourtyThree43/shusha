"""
This module contains the Aria2 Daemon class.

This class provides a wrapper for the Aria2 Daemon, a remote Aria2 server.
The class provides methods to start, stop, and restart the Aria2 server.
"""

import platform
import subprocess
import time
from pathlib import Path

from shusha.models.logger import LoggerService

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6800
DEFAULT_TIMEOUT = 60.0
SCRIPT_PATH = Path(__file__).parent
BIN_PATH = SCRIPT_PATH / Path("../resources/bin/aria2c.exe")
CONF_PATH = SCRIPT_PATH / Path("../resources/aria2.conf")

logger = LoggerService(__name__)


class Daemon:
    """
    A wrapper class for the Aria2 Daemon, a remote Aria2 server.
    """

    def __init__(
        self,
        aria2d=None,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        timeout=DEFAULT_TIMEOUT,
    ):
        """
        Initialize the Aria2 client.

        :param aria2d: (str) The path to the Aria2 daemon executable.
        :param host: (str) The host to connect to. Default is DEFAULT_HOST.
        :param port: (int) The port to connect to. Default is DEFAULT_PORT.
        :param timeout: (int) The timeout for the connection. Default is DEFAULT_TIMEOUT.
        :return: None
        """
        self.aria2d = aria2d or BIN_PATH
        self.host = host
        self.port = port
        self.timeout = timeout
        self.process = None

    def __str__(self):
        """
        Return a string representation of the Daemon object including its host, port, and timeout.
        """
        return f"Daemon(host={self.host}, port={self.port}, timeout={self.timeout})"

    def __repr__(self):
        """
        Return a string representation of the object.
        """
        return self.__str__()

    def _get_version(self):
        """
        Get the version of the Aria2 server to check if it is running.

        Returns:
            The version of the Aria2 server.
        """
        try:
            command = [str(self.aria2d), "--version"]
            output = subprocess.check_output(command, shell=False, text=True)
            return output.strip()
        except FileNotFoundError as e:
            logger.log(f"Aria2 executable not found: {e}")
        except subprocess.CalledProcessError as e:
            logger.log(f"Error getting Aria2 version: {e}")
        except Exception as e:
            logger.log(f"Unexpected error getting Aria2 version: {e}")

    def aria2c_exists(self):
        """
        Check if the Aria2 executable exists.

        Returns:
            True if the Aria2 executable exists, False otherwise.
        """
        version = self._get_version()

        if version:
            self.aria2d = "aria2c"  # use system-wide Aria2
            return True
        else:
            return False

    def _build_command(self):
        """Build the command to start the Aria2 server.

        Returns:
            The command to start the Aria2 server.
        """
        base_command = [str(self.aria2d)]

        if CONF_PATH.exists():
            command = base_command + ["--conf-path=" + str(CONF_PATH)]
        else:
            # Use default configuration
            command = base_command + [
                "--enable-rpc",
                "--rpc-listen-all",
                f"--rpc-listen-port={self.port}",
                "--rpc-max-request-size=2M",
                "--rpc-secret=null",
                "--quiet=true",
            ]

        return command

    def _start_server_process(self, command: list):
        """Start the Aria2 server process.

        Args:
            command (list): The command to start the Aria2 server.

        Returns:
            The process ID of the Aria2 server.
        """
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

    def start_server(self):
        """Start the Aria2 server.

        Returns:
            The process ID of the Aria2 server.
        """
        if self.process and self.process.poll() is None:
            logger.log("Aria2 server is already running.", level="warning")
            return

        command = self._build_command()
        return self._start_server_process(command)

    def stop_server(self):
        """Stop the Aria2 server."""
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
        """Restart the Aria2 server."""
        try:
            self.stop_server()
            time.sleep(3)
        except Exception as e:
            logger.log(f"Error stopping Aria2 server: {e}", level="error")
        finally:
            return self.start_server()
