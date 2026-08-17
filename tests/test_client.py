import unittest
import xmlrpc.client
from unittest.mock import MagicMock

from shusha.models.client import Client, XMLRPCClientException
from shusha.models.daemon import Daemon


class TestClient(unittest.TestCase):
    def setUp(self):
        self.daemon = Daemon(host="localhost", port=6800)
        self.client = Client(self.daemon)
        self.mock_server = MagicMock()
        self.client.server = self.mock_server

    def test_xmlrpc_client_exception(self):
        exc = XMLRPCClientException(1, "Generic error")
        self.assertEqual(exc.errCode, 1)
        self.assertEqual(exc.errMsg, "Generic error")
        self.assertIn("Code: 1", str(exc))
        self.assertFalse(bool(exc))

    def test_build_request_params_without_secret(self):
        params = self.client._build_request_params(["arg1", "arg2"])
        self.assertEqual(params, ["arg1", "arg2"])

    def test_build_request_params_with_secret(self):
        self.client.secret = "token:mysecret"
        params = self.client._build_request_params(["arg1"])
        self.assertEqual(params, ["token:mysecret", "arg1"])

    def test_add_uri_success(self):
        self.mock_server.aria2.addUri.return_value = "gid12345"
        gid = self.client.add_uri(["http://example.com/file.iso"])
        self.assertEqual(gid, "gid12345")
        self.mock_server.aria2.addUri.assert_called_once_with(
            ["http://example.com/file.iso"], None, None
        )

    def test_remove_success(self):
        self.mock_server.aria2.remove.return_value = "gid12345"
        res = self.client.remove("gid12345")
        self.assertEqual(res, "gid12345")
        self.mock_server.aria2.remove.assert_called_once_with("gid12345")

    def test_pause_and_unpause(self):
        self.mock_server.aria2.pause.return_value = "gid12345"
        self.mock_server.aria2.unpause.return_value = "gid12345"
        self.assertEqual(self.client.pause("gid12345"), "gid12345")
        self.assertEqual(self.client.unpause("gid12345"), "gid12345")

    def test_tell_status(self):
        status_dict = {"gid": "gid12345", "status": "active"}
        self.mock_server.aria2.tellStatus.return_value = status_dict
        res = self.client.tell_status("gid12345")
        self.assertEqual(res, status_dict)

    def test_tell_status_fault_returns_empty_dict(self):
        self.mock_server.aria2.tellStatus.side_effect = xmlrpc.client.Fault(
            1, "Not found"
        )
        res = self.client.tell_status("nonexistent")
        self.assertEqual(res, {})

    def test_global_options_and_stats(self):
        self.mock_server.aria2.getGlobalOption.return_value = {
            "max-download-limit": "0"
        }
        self.mock_server.aria2.getGlobalStat.return_value = {"downloadSpeed": "1000"}
        self.assertEqual(self.client.get_global_option(), {"max-download-limit": "0"})
        self.assertEqual(self.client.get_global_stat(), {"downloadSpeed": "1000"})


if __name__ == "__main__":
    unittest.main()
