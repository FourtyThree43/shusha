import unittest
from unittest.mock import MagicMock

from shusha.models.structs_downloads import BitTorrent, Download, File
from shusha.models.structs_options import Options
from shusha.models.structs_stats import Stats


class TestStructs(unittest.TestCase):
    def test_stats_struct(self):
        stats = Stats(
            {
                "downloadSpeed": "1048576",
                "uploadSpeed": "524288",
                "numActive": "2",
                "numWaiting": "3",
                "numStopped": "1",
                "numStoppedTotal": "5",
            }
        )
        self.assertEqual(stats.download_speed, 1048576)
        self.assertEqual(stats.upload_speed, 524288)
        self.assertEqual(stats.num_active, 2)
        self.assertEqual(stats.num_waiting, 3)
        self.assertEqual(stats.num_stopped, 1)
        self.assertEqual(stats.num_stopped_total, 5)
        self.assertIn("MiB/s", stats.download_speed_string())
        self.assertIn("KiB/s", stats.upload_speed_string())

    def test_file_struct(self):
        file_struct = {
            "index": "1",
            "path": "/tmp/test.zip",
            "length": "1000",
            "completedLength": "500",
            "selected": "true",
            "uris": [{"status": "used", "uri": "http://example.com/test.zip"}],
        }
        f = File(file_struct)
        self.assertEqual(f.index, 1)
        self.assertEqual(f.length, 1000)
        self.assertEqual(f.completed_length, 500)
        self.assertTrue(f.selected)
        self.assertIn("1000", f.length_string(human_readable=False))
        self.assertIn("500", f.completed_length_string(human_readable=False))

    def test_bittorrent_struct(self):
        bt_struct = {
            "announceList": [["http://tracker.com"]],
            "comment": "Sample comment",
            "creationDate": 1600000000,
            "mode": "multi",
            "info": {"name": "TorrentName"},
        }
        bt = BitTorrent(bt_struct)
        self.assertEqual(bt.comment, "Sample comment")
        self.assertEqual(bt.mode, "multi")
        self.assertEqual(bt.info, {"name": "TorrentName"})
        self.assertEqual(str(bt), "TorrentName")

    def test_download_struct(self):
        mock_api = MagicMock()
        dl_struct = {
            "gid": "abc1234567890def",
            "status": "active",
            "totalLength": "2000",
            "completedLength": "1000",
            "downloadSpeed": "500",
            "uploadSpeed": "100",
            "dir": "/downloads",
            "files": [
                {
                    "index": "1",
                    "path": "/downloads/file.bin",
                    "length": "2000",
                    "completedLength": "1000",
                    "selected": "true",
                    "uris": [{"status": "used", "uri": "http://example.com/file.bin"}],
                }
            ],
        }
        dl = Download(api=mock_api, struct=dl_struct)
        self.assertEqual(dl.gid, "abc1234567890def")
        self.assertTrue(dl.is_active)
        self.assertFalse(dl.is_complete)
        self.assertFalse(dl.has_failed)
        self.assertEqual(dl.progress, 50.0)
        self.assertEqual(dl.name, "file.bin")

    def test_options_struct(self):
        mock_api = MagicMock()
        opts = Options(
            api=mock_api, struct={"max-download-limit": "100000", "split": "4"}
        )
        self.assertEqual(opts.max_download_limit, 100000)
        self.assertEqual(opts.split, 4)


if __name__ == "__main__":
    unittest.main()
