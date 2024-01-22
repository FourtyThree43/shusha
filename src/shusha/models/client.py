"""
This module contains the Client class.

The Client class is used to interact with the aria2 daemon using XML-RPC.
The Client class is a wrapper around the xmlrpc.client.ServerProxy class.
"""

import xmlrpc.client
from pathlib import Path
from typing import Any

from shusha.models.daemon import Daemon
from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


class XMLRPCClientException(Exception):
    """An exception specific to XML-RPC errors."""

    def __init__(self, faultCode: int, faultString: str) -> None:
        """Initialize the exception.

        Parameters:
            faultCode: The fault code.
            faultString: The fault string describing the error.
        """
        super().__init__()
        self.errCode = faultCode
        self.errMsg = faultString

    def __str__(self):
        """
        Return a string representation of the XML-RPC Error, including the error code and message.
        """
        return f"XML-RPC Error - Code: {self.errCode}, Message: {self.errMsg}"

    def __bool__(self):
        """
        Return the boolean value of the object.
        """
        return False


class Client:
    """
    A wrapper class for the XML-RPC client used to interact with the aria2 daemon
    """

    def __init__(self, daemon: Daemon):
        """
        Initialize the class with a Daemon instance.

        Args:
            daemon (Daemon): The Daemon instance to be used.

        Returns:
            None
        """
        # self.logger = logger(logger_name="ShushaClient")
        self.remote = daemon
        self.secret = None
        self.server_uri = f"http://{self.remote.host}:{self.remote.port}/rpc"
        self.server = xmlrpc.client.ServerProxy(
            self.server_uri, allow_none=True
        )

    def __str__(self):
        """
        Return a string representation of the server URI.
        """
        return f"{self.server_uri}"

    def __repr__(self):
        """
        Return a string representation of the Client object with the remote host and port.
        """
        return f"Client(host='{self.remote.host}', port='{self.remote.port}')"

    def _build_request_params(self, params: list | None = None):
        """
        Build the request parameters for the XML-RPC server.

        Args:
            params: A list of parameters to be added to the request parameters.

        Returns:
            A list of parameters to be sent to the XML-RPC server.
        """
        request_params = [self.secret] if self.secret else []
        if params:
            request_params.extend(params)
        return request_params

    def _call_method(self, method: str, params: list[Any] | None = None):
        """
        Call a method on the XML-RPC server.

        Args:
            method: The method to be called.
            params: A list of parameters to be passed to the method.

        Returns:
            The result of the method call.

        Raises:
            XMLRPCClientException: If an XML-RPC error occurs.
        """
        request_params = self._build_request_params(params)
        try:
            return getattr(self.server.aria2, method)(*request_params)
        except xmlrpc.client.Fault as e:
            self._handle_xmlrpc_error(e)
            return None
        except Exception as e:
            logger.log(f"Unexpected error: {e}", level="error")
            return None

    def _handle_xmlrpc_error(self, xmlrpc_fault: xmlrpc.client.Fault):
        """
        Handle XML-RPC errors.

        Args:
            xmlrpc_fault: An instance of the xmlrpc.client.Fault class.
        """
        faultCode = xmlrpc_fault.faultCode
        faultString = xmlrpc_fault.faultString
        logger.log(XMLRPCClientException(faultCode, faultString), level="error")

    def add_uri(
        self,
        uris: list[str],
        options: dict[str, Any] | None = None,
        position: int | None = None,
    ) -> str | None:
        """
        Adds new HTTP(S)/FTP/SFTP/BitTorrent Magnet URI.

        If you want to add BitTorrent Magnet URI, you must set "bt-enable-lpd"
        option true. If you want to add BitTorrent Magnet URI as well as
        BitTorrent metadata, you must also set "bt-enable-peer-exchange" option
        true. BitTorrent Magnet URI does not contain the number of files and the
        total file size. Therefore, if you add BitTorrent Magnet URI without
        metadata, aria2 cannot perform any download progress sanity check. If you
        need such features, please consider to use "add_torrent()" instead.

        Args:
            uris: List of URIs.
            options: Additional options to be passed to the aria2c process.
            position: The position in the queue where the download should be added.

        Returns:
            str: The GID of the newly added download.
        """
        return self._call_method("addUri", [uris, options, position])

    def add_torrent(self, torrent, uris=None, options=None, position=None):
        return self._call_method(
            "addTorrent", [torrent, uris, options, position]
        )

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

    def tell_status(self, gid: str, keys: list[str] | None = None):
        return self._call_method("tellStatus", [gid, keys])

    def get_uris(self, gid):
        return self._call_method("getUris", [gid])

    def get_files(self, gid):
        return self._call_method("getFiles", [gid])

    def get_peers(self, gid):
        return self._call_method("getPeers", [gid])

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
            "changeUri", [gid, file_index, del_uris, add_uris, position]
        )

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

    # Custom methods

    # def get_all_downloads(self):
    #     active_downloads = self.tell_active()
    #     waiting_downloads = self.tell_waiting(0, 1000)
    #     stopped_downloads = self.tell_stopped(0, 1000)

    #     return active_downloads + waiting_downloads + stopped_downloads


if __name__ == "__main__":
    import os
    import time

    def sizeof_fmt(num, delim=" ", suffix="B"):
        for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
            if abs(num) < 1024.0:
                return f"{num:3.1f}{delim}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}{delim}Yi{suffix}"

    d = Daemon()
    client = Client(d)
    pid = d.start_server()
    logger.log(pid)

    try:
        logger.log(client)

        sesId = client.get_session_info().get("sessionId")
        logger.log(sesId)

        # gids = ["27ffc223275cbba0", "eea522f44eb7d7fe", "d6b3e42d7c8a0e0e"]
        url = "https://proof.ovh.net/files/10Mb.dat"
        dl_path = Path(__file__).parent

        gid = client.add_uri([url], {"dir": str(dl_path)})
        logger.log(f"Download started with GID: {gid}")

        status = client.tell_status(gid=gid)
        is_active = status.get("status")
        logger.log(is_active)

        # while is_active == "active":
        #     status = client.tell_status(gid=gid,
        #                                 keys=[
        #                                     "status", "totalLength",
        #                                     "completedLength", "downloadSpeed",
        #                                     "files"
        #                                 ])
        #     # logger.log(status.get("files"))
        #     is_active = status.get("status")
        #     # logger.log(status)
        #     dl_sp = int(status.get("downloadSpeed"))
        #     sz = int(status.get("completedLength"))

        #     sp = f"{sizeof_fmt(dl_sp)}/s"
        #     fs = f"{sizeof_fmt(sz)}"

        #     logger.log(f"- {fs} - {sp}")

        #     time.sleep(1)

        # client.save_session()
        time.sleep(5)

    finally:
        d.stop_server()
