"""
Unit tests for the JsonRpcTransport and multicall pipeline.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from shusha.infrastructure.aria2.errors import (
    Aria2AuthenticationError,
    Aria2EngineError,
)
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport


class TestJsonRpcTransport(unittest.TestCase):
    def setUp(self):
        self.transport = JsonRpcTransport(
            endpoint="http://127.0.0.1:6800/jsonrpc",
            secret="mysecret",
        )

    @patch("urllib.request.urlopen")
    def test_successful_call_with_secret(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-1",
                "result": "2089b05ecca3d829",
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.transport.call("aria2.addUri", [["http://example.com"]])
        self.assertEqual(result, "2089b05ecca3d829")

        # Verify request had token prepended
        call_args = mock_urlopen.call_args[0][0]
        sent_json = json.loads(call_args.data.decode("utf-8"))
        self.assertEqual(sent_json["params"][0], "token:mysecret")
        self.assertEqual(sent_json["params"][1], ["http://example.com"])

    @patch("urllib.request.urlopen")
    def test_engine_error_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-1",
                "error": {"code": 1, "message": "No URI to download"},
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with self.assertRaises(Aria2EngineError) as ctx:
            self.transport.call("aria2.addUri", [[]])
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("No URI", ctx.exception.message)

    @patch("urllib.request.urlopen")
    def test_authentication_error_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-1",
                "error": {"code": 1, "message": "Unauthorized"},
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with self.assertRaises(Aria2AuthenticationError):
            self.transport.call("aria2.getVersion")

    @patch("urllib.request.urlopen")
    def test_multicall(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-multi",
                "result": [["res1"], ["res2"]],
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        results = self.transport.multicall(
            [
                ("aria2.tellActive", []),
                ("aria2.getGlobalStat", []),
            ]
        )
        self.assertEqual(results, ["res1", "res2"])


if __name__ == "__main__":
    unittest.main()
