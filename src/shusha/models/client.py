"""
This module contains the Client class.

The Client class is used to interact with the aria2 daemon using XML-RPC.
The Client class is a wrapper around the xmlrpc.client.ServerProxy class.
"""

import xmlrpc.client
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
        logger.log(XMLRPCClientException(faultCode, faultString), "error")

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
        torrent = xmlrpc.client.Binary(open(torrent, "rb").read())
        return self._call_method(
            "addTorrent", [torrent, uris, options, position]
        )

    def add_metalink(self, metalink, options=None, position=None):
        return self._call_method("addMetalink", [metalink, options, position])

    def remove(self, gid: str):
        """
        Removes an item with the specified ID from the collection.

        :param gid: The ID of the item to be removed
        :type gid: str
        :return: The GID of the removed download.
        """
        return self._call_method("remove", [gid])

    def force_remove(self, gid: str):
        """
        Removes a specific item by its ID using the force remove method.

        :param gid: a string representing the ID of the item to be removed
        :return: The GID of the removed download.
        """
        return self._call_method("forceRemove", [gid])

    def pause(self, gid: str):
        """
        Pause the specified task identified by the given ID.

        :param gid: str - The ID of the task to pause.
        :return: The result of calling the "pause" method with the specified ID.
        """
        return self._call_method("pause", [gid])

    def pause_all(self):
        """
        Method to pause all tasks.
        """
        return self._call_method("pauseAll")

    def force_pause(self, gid: str):
        """
        Pause the specified task identified by the given ID forcefully.

        :param gid: str - The ID of the task to pause.
        :return: The result of calling the "forcePause" method with the specified ID.
        """
        return self._call_method("forcePause", [gid])

    def force_pause_all(self):
        """
        Method to force pause all operations.
        """
        return self._call_method("forcePauseAll")

    def unpause(self, gid: str):
        """
        Method to unpause a specific item using its ID.

        :param gid: str - the ID of the item to unpause
        :return: the result of the method call
        """
        return self._call_method("unpause", [gid])

    def unpause_all(self):
        """
        Unpauses all items.
        """
        return self._call_method("unpauseAll")

    def tell_status(self, gid: str, keys: list[str] | None = None):
        """
        A method to retrieve the status of a given identifier, with optional keys.
        :param gid: The identifier for which the status is to be retrieved.
        :param keys: Optional list of specific keys for which the status is to be retrieved.
        :return: A dictionary containing the status information, or an empty dictionary if no status is found.
        """
        _struct = self._call_method("tellStatus", [gid, keys])

        if _struct:
            return _struct
        return {}

    def get_uris(self, gid: str):
        return self._call_method("getUris", [gid])

    def get_files(self, gid: str):
        return self._call_method("getFiles", [gid])

    def get_peers(self, gid: str):
        return self._call_method("getPeers", [gid])

    def get_servers(self, gid: str):
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

    def get_option(self, gid: str):
        """
        Retrieve an option for a given group ID.

        :param gid: a string representing the group ID
        :return: the options for the given group ID, or an empty dictionary if no options are found
        """
        options = self._call_method("getOption", [gid])
        if options:
            return options
        return {}

    def change_option(self, gid, options):
        return self._call_method("changeOption", [gid, options])

    def get_global_option(self):
        """
        Retrieve the global option by calling the 'getGlobalOption' method and return it.
        If no global options are found, an empty dictionary is returned.
        """
        global_options = self._call_method("getGlobalOption")
        if global_options:
            return global_options
        return {}

    def change_global_option(self, options):
        """
        Change a global option using the given options.
        :param self: The object instance
        :param options: The options to be changed
        :return: The result of calling the method with the provided options
        """
        return self._call_method("changeGlobalOption", [options])

    def get_global_stat(self):
        """
        Retrieves the global statistics by calling the 'getGlobalStat' method.
        Returns the statistics if available, otherwise returns an empty dictionary.
        """
        stats = self._call_method("getGlobalStat")
        if stats:
            return stats
        return {}

    def purge_download_result(self):
        return self._call_method("purgeDownloadResult")

    def remove_download_result(self, gid: str):
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
        """
        Call multiple methods in a single request.

        :param methods: The list of methods to call.
        :type methods: list
        :return: The result of calling multiple methods.
        :rtype: any
        """
        return self._call_method("system.multicall", [methods])

    def list_methods(self):
        """
        Returns a list of available methods for the system.

        :return: List of available methods for the system.
        """
        return self._call_method("system.listMethods")

    def list_notifications(self):
        """
        Retrieves a list of notifications from the system.

        :return: List of notifications from the system.
        """
        return self._call_method("system.listNotifications")
