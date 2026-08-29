"""
Unit tests for the strongly typed Aria2Client adapter.
"""

import unittest
from unittest.mock import MagicMock

from shusha.domain.identifiers import Gid
from shusha.domain.states import DownloadState
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.aria2.errors import Aria2EngineError
from shusha.infrastructure.aria2.option_registry import OptionRegistry


class TestAria2Client(unittest.TestCase):
    def setUp(self):
        self.mock_transport = MagicMock()
        self.registry = OptionRegistry.load_from_spec()
        self.client = Aria2Client(transport=self.mock_transport, registry=self.registry)

    def test_add_uri(self):
        self.mock_transport.call.return_value = "2089b05ecca3d829"
        gid = self.client.add_uri(
            ["https://example.com/file.zip"], options={"dir": "/tmp"}
        )
        self.assertEqual(str(gid), "2089b05ecca3d829")
        self.mock_transport.call.assert_called_once_with(
            "aria2.addUri", [["https://example.com/file.zip"], {"dir": "/tmp"}]
        )

    def test_add_torrent(self):
        self.mock_transport.call.return_value = "2089b05ecca3d830"
        gid = self.client.add_torrent(b"d8:announce...", options={"dir": "/tmp"})
        self.assertEqual(str(gid), "2089b05ecca3d830")
        self.assertTrue(self.mock_transport.call.called)

    def test_add_metalink(self):
        self.mock_transport.call.return_value = ["2089b05ecca3d831", "2089b05ecca3d832"]
        gids = self.client.add_metalink(b"<?xml...")
        self.assertEqual(len(gids), 2)
        self.assertEqual(str(gids[0]), "2089b05ecca3d831")

    def test_pause_and_unpause(self):
        self.mock_transport.call.return_value = "2089b05ecca3d829"
        gid = self.client.pause(Gid("2089b05ecca3d829"))
        self.assertEqual(str(gid), "2089b05ecca3d829")
        self.mock_transport.call.assert_called_with("aria2.pause", ["2089b05ecca3d829"])

        self.client.unpause(Gid("2089b05ecca3d829"))
        self.mock_transport.call.assert_called_with(
            "aria2.unpause", ["2089b05ecca3d829"]
        )

    def test_tell_status(self):
        self.mock_transport.call.return_value = {
            "gid": "2089b05ecca3d829",
            "status": "active",
            "totalLength": "2048",
            "completedLength": "1024",
            "downloadSpeed": "512",
            "uploadSpeed": "0",
            "dir": "/downloads",
            "files": [],
        }
        dl = self.client.tell_status(Gid("2089b05ecca3d829"))
        self.assertEqual(str(dl.gid), "2089b05ecca3d829")
        self.assertEqual(dl.state, DownloadState.ACTIVE)
        self.assertEqual(dl.completed_length.bytes, 1024)

    def test_tell_active(self):
        self.mock_transport.call.return_value = [
            {
                "gid": "2089b05ecca3d829",
                "status": "active",
                "totalLength": "2048",
                "completedLength": "1024",
                "downloadSpeed": "512",
                "uploadSpeed": "0",
                "dir": "/downloads",
                "files": [],
            }
        ]
        active = self.client.tell_active()
        self.assertEqual(len(active), 1)
        self.assertEqual(str(active[0].gid), "2089b05ecca3d829")

    def test_get_global_stat(self):
        self.mock_transport.call.return_value = {
            "downloadSpeed": "100000",
            "uploadSpeed": "20000",
            "numActive": "1",
            "numWaiting": "0",
            "numStopped": "3",
            "numStoppedTotal": "5",
        }
        stat = self.client.get_global_stat()
        self.assertEqual(stat.download_speed.bytes_per_sec, 100000)
        self.assertEqual(stat.num_active, 1)

    def test_change_position(self):
        self.mock_transport.call.return_value = 0
        new_pos = self.client.change_position(Gid("2089b05ecca3d829"), 0, "POS_SET")
        self.assertEqual(new_pos, 0)
        self.mock_transport.call.assert_called_with(
            "aria2.changePosition", ["2089b05ecca3d829", 0, "POS_SET"]
        )

    def test_change_option(self):
        self.mock_transport.call.return_value = "OK"
        success = self.client.change_option(
            Gid("2089b05ecca3d829"), {"max-download-limit": "100K"}
        )
        self.assertTrue(success)

    def test_engine_error_propagation(self):
        self.mock_transport.call.side_effect = Aria2EngineError(
            code=1, message="Download not found"
        )
        with self.assertRaises(Aria2EngineError):
            self.client.tell_status(Gid("2089b05ecca3d829"))


if __name__ == "__main__":
    unittest.main()
