import unittest
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.views.status_win import DownloadWindow
from shusha.views.uri_win import UriManagerWindow


class TestStatusAndUriWindows(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_status_window_headless(self):
        try:
            root = ttk.Window(themename="bootstrap-dark")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for DownloadWindow test")

        mock_api = MagicMock()
        mock_api.get_peers.return_value = [
            {
                "ip": "1.2.3.4",
                "port": "5000",
                "downloadSpeed": "1000",
                "uploadSpeed": "500",
                "seeder": "true",
                "peerId": "qBit",
            }
        ]
        mock_api.get_servers.return_value = [
            {
                "servers": [
                    {
                        "uri": "http://example.com/file",
                        "downloadSpeed": "2000",
                        "currentConnection": "2",
                    }
                ]
            }
        ]
        mock_dl = MagicMock()
        mock_dl.gid = "gid123"
        mock_dl.progress = 50.0
        mock_dl.name = "TestFile.zip"
        mock_dl.files = []
        mock_dl.status = "active"
        mock_dl.completed_length_string.return_value = "50 MB"
        mock_dl.total_length_string.return_value = "100 MB"
        mock_dl.download_speed_string.return_value = "1 MB/s"
        mock_dl.eta_string.return_value = "00:01:00"
        mock_dl.connections = 4

        win = DownloadWindow(master=root, api=mock_api)
        win.update_stats_frame(mock_dl)
        self.assertEqual(win.download_gid, "gid123")

        # Test peer and server population
        self.assertEqual(len(win.peers_tree.get_children()), 1)
        self.assertEqual(len(win.servers_tree.get_children()), 1)

        # Test limits apply
        win.limit_dl_var.set("500")
        win._apply_limits()
        mock_api.change_download_speed_limits.assert_called_with(
            "gid123", max_download="500K", max_upload="0"
        )

        win._on_close()
        root.destroy()

    def test_uri_manager_window_headless(self):
        try:
            root = ttk.Window(themename="bootstrap-dark")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for UriManagerWindow test")

        mock_api = MagicMock()
        mock_api.client.get_uris.return_value = [
            {"uri": "http://mirror1.com/dl", "status": "used"},
            {"uri": "http://mirror2.com/dl", "status": "waiting"},
        ]
        mock_api.change_uri.return_value = [0, 1]

        uri_win = UriManagerWindow(master=root, api=mock_api, gid="gid_uri_test")
        self.assertEqual(len(uri_win.tree.get_children()), 2)

        # Test add mirror
        uri_win.new_uri_var.set("http://mirror3.com/dl")
        uri_win._on_add_uri()
        mock_api.change_uri.assert_called_with(
            "gid_uri_test", file_index=1, add_uris=["http://mirror3.com/dl"]
        )

        uri_win.destroy()
        root.destroy()


if __name__ == "__main__":
    unittest.main()
