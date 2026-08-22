import json
import threading
import unittest
from unittest.mock import MagicMock, patch

from shusha.models.ws_client import Aria2WsClient, JsonRpcException


class TestWsClient(unittest.TestCase):
    def setUp(self):
        self.client = Aria2WsClient(host="localhost", port=6800, secret="testsecret")

    def test_init_and_state(self):
        self.assertFalse(self.client.is_connected)
        self.assertEqual(self.client.secret, "testsecret")

    def test_event_listener_registration(self):
        callback = MagicMock()
        self.client.on("aria2.onDownloadComplete", callback)
        self.assertIn("aria2.onDownloadComplete", self.client._event_listeners)

        # Dispatch event
        self.client._dispatch_event("aria2.onDownloadComplete", {"gid": "gid123"})
        callback.assert_called_once_with("aria2.onDownloadComplete", {"gid": "gid123"})

        # Unregister
        self.client.off("aria2.onDownloadComplete", callback)
        self.assertEqual(len(self.client._event_listeners["aria2.onDownloadComplete"]), 0)

    def test_handle_notification_message(self):
        callback = MagicMock()
        self.client.on("aria2.onDownloadStart", callback)

        msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "aria2.onDownloadStart",
            "params": [{"gid": "gid_started"}]
        })
        self.client._handle_message(msg)
        callback.assert_called_once_with("aria2.onDownloadStart", {"gid": "gid_started"})

    def test_handle_rpc_response_message(self):
        event = threading.Event()
        holder = []
        self.client._pending_requests["req_99"] = (event, holder)

        msg = json.dumps({
            "jsonrpc": "2.0",
            "id": "req_99",
            "result": "OK"
        })
        self.client._handle_message(msg)
        self.assertTrue(event.is_set())
        self.assertEqual(holder[0]["result"], "OK")

    @patch("urllib.request.urlopen")
    def test_http_call_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "req_1",
            "result": "gid_test_123"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.client.call("aria2.addUri", ["http://example.com/file.zip"])
        self.assertEqual(result, "gid_test_123")

    @patch("urllib.request.urlopen")
    def test_http_call_error(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "req_1",
            "error": {"code": 1, "message": "Download error"}
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with self.assertRaises(JsonRpcException):
            self.client.call("aria2.addUri", ["http://invalid.url"])

    @patch("urllib.request.urlopen")
    def test_multicall(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "req_1",
            "result": [["active_result"], ["global_stat_result"]]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        batch = [
            ("aria2.tellActive", []),
            ("aria2.getGlobalStat", []),
        ]
        results = self.client.multicall(batch)
        self.assertEqual(results, ["active_result", "global_stat_result"])
