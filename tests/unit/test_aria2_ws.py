"""
Unit tests for the Aria2WebSocketClient.
"""

import json
import unittest
from unittest.mock import MagicMock

from shusha.infrastructure.aria2.ws_client import Aria2WebSocketClient


class TestAria2WebSocketClient(unittest.TestCase):
    def setUp(self):
        self.ws_client = Aria2WebSocketClient(endpoint="ws://127.0.0.1:6800/jsonrpc")

    def test_listener_registration(self):
        callback = MagicMock()
        self.ws_client.on("aria2.onDownloadStart", callback)
        self.assertIn("aria2.onDownloadStart", self.ws_client._listeners)

        self.ws_client.off("aria2.onDownloadStart", callback)
        self.assertNotIn(
            callback, self.ws_client._listeners.get("aria2.onDownloadStart", [])
        )

    def test_raw_message_dispatch(self):
        callback = MagicMock()
        self.ws_client.on("aria2.onDownloadComplete", callback)

        msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "aria2.onDownloadComplete",
                "params": [{"gid": "2089b05ecca3d829"}],
            }
        )
        self.ws_client._handle_raw_message(msg)
        callback.assert_called_once_with(
            "aria2.onDownloadComplete", {"gid": "2089b05ecca3d829"}
        )


if __name__ == "__main__":
    unittest.main()
