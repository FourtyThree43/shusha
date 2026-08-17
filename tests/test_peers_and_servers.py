import unittest
from unittest.mock import MagicMock

from shusha.controller.api import ShushaAPI
from shusha.models.client import Client
from shusha.models.daemon import Daemon


class TestPeersAndServers(unittest.TestCase):
    def setUp(self):
        self.mock_daemon = MagicMock(spec=Daemon)
        self.mock_client = MagicMock(spec=Client)
        self.mock_db = MagicMock()
        self.api = ShushaAPI(
            daemon=self.mock_daemon, client=self.mock_client, db=self.mock_db
        )

    def test_get_peers(self):
        self.mock_client.get_peers.return_value = [
            {
                "peerId": "qBittorrent/4.3.9",
                "ip": "192.168.1.100",
                "port": "51413",
                "downloadSpeed": "1048576",
                "uploadSpeed": "524288",
                "seeder": "true",
            }
        ]
        peers = self.api.get_peers("test_gid_123")
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]["ip"], "192.168.1.100")
        self.assertEqual(peers[0]["downloadSpeed"], "1048576")

    def test_get_servers(self):
        self.mock_client.get_servers.return_value = [
            {
                "index": "1",
                "servers": [
                    {
                        "uri": "https://fast.mirror.org/ubuntu.iso",
                        "currentConnection": "4",
                        "downloadSpeed": "5242880",
                    }
                ],
            }
        ]
        servers = self.api.get_servers("test_gid_456")
        self.assertEqual(len(servers), 1)
        self.assertEqual(len(servers[0]["servers"]), 1)
        self.assertEqual(
            servers[0]["servers"][0]["uri"], "https://fast.mirror.org/ubuntu.iso"
        )

    def test_change_download_speed_limits(self):
        self.mock_client.change_option.return_value = "OK"
        res = self.api.change_download_speed_limits(
            "test_gid_789", max_download="500K", max_upload="100K"
        )
        self.assertTrue(res)
        self.mock_client.change_option.assert_called_once_with(
            "test_gid_789", {"max-download-limit": "500K", "max-upload-limit": "100K"}
        )

    def test_change_uri(self):
        self.mock_client.change_uri.return_value = [1, 1]
        res = self.api.change_uri(
            gid="test_gid_999",
            file_index=1,
            del_uris=["http://dead.mirror/file.zip"],
            add_uris=["http://new.mirror/file.zip"],
        )
        self.assertEqual(res, [1, 1])
        self.mock_client.change_uri.assert_called_once_with(
            "test_gid_999",
            1,
            ["http://dead.mirror/file.zip"],
            ["http://new.mirror/file.zip"],
            None,
        )


if __name__ == "__main__":
    unittest.main()
