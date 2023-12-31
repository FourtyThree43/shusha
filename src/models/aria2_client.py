from pathlib import Path, PurePath
import platform
import subprocess
import time
import xmlrpc.client
import logging

logging.basicConfig(level=logging.INFO)


class XMLRPCClientException(Exception):
    """An exception specific to XML-RPC errors."""

    def __init__(self, faultCode: int, faultString: str) -> None:
        """Initialize the exception.

        Parameters:
            faultCode: The fault code.
            faultString: The fault string describing the error.
        """
        super().__init__()
        self.faultCode = faultCode
        self.faultString = faultString

    def __str__(self):
        return f"XML-RPC Error - Code: {self.faultCode}, Message: {self.faultString}"

    def __bool__(self):
        return False


class Aria2Client:
    ARIA2_OPTIONS = [
        "--no-conf",
        "--enable-rpc",
        "--rpc-listen-all",
        "--quiet=true",
        # Add other options as needed
    ]

    def __init__(self, host, port, aria2_path="", secret=None):
        self.aria2_path = Path(aria2_path)
        self.host = host
        self.port = port
        self.server_uri = f"http://{host}:{port}/rpc"
        self.server = xmlrpc.client.ServerProxy(self.server_uri,
                                                allow_none=True)
        self.secret = secret

    def check_aria_path(self):
        return self.aria2_path.exists() and self.aria2_path.is_file()

    def initialize_aria2d(self):
        if not self.check_aria_path():
            cwd = Path(__file__).parent
            aria2d = PurePath.joinpath(cwd, "aria2c.exe")
        else:
            aria2d = self.aria2_path

        return aria2d

    def start_aria(self):
        aria2d = self.initialize_aria2d()

        if platform.system() == "Windows":
            NO_WINDOW = 0x08000000
            try:
                subprocess.Popen(
                    [
                        str(aria2d),
                        *self.ARIA2_OPTIONS,
                        f"--rpc-listen-port={self.port}",
                        "--rpc-max-request-size=2M",
                    ],
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                    creationflags=NO_WINDOW,
                )
                logging.info("Aria2 started successfully.")
            except Exception as e:
                logging.error(f"Error starting Aria2: {e}")
        else:
            raise NotImplementedError(
                "Starting Aria2 is not implemented for this platform.")

    def _build_request_params(self, method, params=None):
        request_params = [self.secret] if self.secret else []
        if params:
            request_params.extend(params)
        return request_params

    def _call_method(self, method, params=None):
        request_params = self._build_request_params(method, params)
        try:
            return getattr(self.server.aria2, method)(*request_params)
        except xmlrpc.client.Fault as e:
            self._handle_xmlrpc_error(e)
            return None

    def _handle_xmlrpc_error(self, xmlrpc_fault):
        faultCode = xmlrpc_fault.faultCode
        faultString = xmlrpc_fault.faultString
        raise XMLRPCClientException(faultCode, faultString)

    def add_uri(self, uris, options=None, position=None):
        return self._call_method("addUri", [uris, options, position])

    def add_torrent(self, torrent, uris=None, options=None, position=None):
        return self._call_method("addTorrent",
                                 [torrent, uris, options, position])

    def add_metalink(self, metalink, options=None, position=None):
        return self._call_method("addMetalink", [metalink, options, position])

    def remove(self, gid):
        return self._call_method("remove", [gid])

    def force_remove(self, gid):
        return self._call_method("forceRemove", [gid])

    def pause(self, gid):
        return self._call_method("pause", [gid])

    def pause_all(self):
        return self._call_method("pauseAll")

    def force_pause(self, gid):
        return self._call_method("forcePause", [gid])

    def force_pause_all(self):
        return self._call_method("forcePauseAll")

    def unpause(self, gid):
        return self._call_method("unpause", [gid])

    def unpause_all(self):
        return self._call_method("unpauseAll")

    def get_files(self, gid):
        return self._call_method("getFiles", [gid])

    def get_servers(self, gid):
        return self._call_method("getServers", [gid])

    def tell_active(self, keys=None):
        return self._call_method("tellActive", [keys])

    def tell_waiting(self, offset, num, keys=None):
        return self._call_method("tellWaiting", [offset, num, keys])

    def tell_stopped(self, offset, num, keys=None):
        return self._call_method("tellStopped", [offset, num, keys])

    def change_position(self, gid, pos, how):
        return self._call_method("changePosition", [gid, pos, how])

    def change_uri(self, gid, file_index, del_uris, add_uris, position=None):
        return self._call_method(
            "changeUri", [gid, file_index, del_uris, add_uris, position])

    def get_option(self, gid):
        return self._call_method("getOption", [gid])

    def change_option(self, gid, options):
        return self._call_method("changeOption", [gid, options])

    def get_global_option(self):
        return self._call_method("getGlobalOption")

    def change_global_option(self, options):
        return self._call_method("changeGlobalOption", [options])

    def get_global_stat(self):
        return self._call_method("getGlobalStat")

    def purge_download_result(self):
        return self._call_method("purgeDownloadResult")

    def remove_download_result(self, gid):
        return self._call_method("removeDownloadResult", [gid])

    def get_version(self):
        return self._call_method("getVersion")

    def get_session_info(self):
        return self._call_method("getSessionInfo")

    def shutdown(self):
        logging.info("Shutting down Aria2.")
        return self._call_method("shutdown")

    def force_shutdown(self):
        return self._call_method("forceShutdown")

    def save_session(self):
        return self._call_method("saveSession")

    def multicall(self, methods):
        return self._call_method("system.multicall", [methods])

    def list_methods(self):
        return self._call_method("system.listMethods")

    def list_notifications(self):
        return self._call_method("system.listNotifications")

    def get_uris(self, gid):
        return self._call_method("getUris", [gid])

    def tell_status(self, gid, keys=None):
        return self._call_method("tellStatus", [gid, keys])

    def get_all_downloads(self):
        active_downloads = self.tell_active()
        waiting_downloads = self.tell_waiting(0, 1000)
        stopped_downloads = self.tell_stopped(0, 1000)

        return active_downloads + waiting_downloads + stopped_downloads


if __name__ == "__main__":
    aria2_path = "aria2c"
    host = "localhost"
    port = 6800
    aria2_client = Aria2Client(host, port, aria2_path)

    # Start Aria2
    aria2_client.start_aria()
    time.sleep(3)

    url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
    dl_path = Path(__file__).parent

    gid = aria2_client.add_uri([url], {"dir": str(dl_path)})
    time.sleep(5)
    print(gid)

    # listofdl = aria2_client.get_all_downloads()
    # print(listofdl)

    time.sleep(5)
    aria2_client.shutdown()
