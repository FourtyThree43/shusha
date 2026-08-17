import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from shusha.controller.api import ShushaAPI
from shusha.models.client import Client, XMLRPCClientException
from shusha.models.daemon import Daemon
from shusha.models.database import ShushaDB


class TestShushaAPI(unittest.TestCase):
    def setUp(self):
        self.mock_daemon = MagicMock(spec=Daemon)
        self.mock_client = MagicMock(spec=Client)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_api.db"
        self.db = ShushaDB(str(self.db_path))
        self.api = ShushaAPI(
            daemon=self.mock_daemon, client=self.mock_client, db=self.db
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_stop_server(self):
        self.mock_daemon.start_server.return_value = 1234
        pid = self.api.start_server()
        self.assertEqual(pid, 1234)

        self.api.stop_server()
        self.mock_daemon.stop_server.assert_called_once()

    def test_add_uris(self):
        self.mock_client.add_uri.return_value = "gid_add_test"
        self.mock_client.tell_status.return_value = {
            "gid": "gid_add_test",
            "status": "active",
            "files": [],
        }
        dl = self.api.add_uris(["http://example.com/test.zip"])
        self.assertIsNotNone(dl)
        assert dl is not None
        self.assertEqual(dl.gid, "gid_add_test")

    def test_pause_and_resume(self):
        self.mock_client.tell_status.return_value = {
            "gid": "gid1",
            "status": "paused",
            "files": [],
        }
        res_pause = self.api.pause("gid1")
        self.mock_client.pause.assert_called_once_with("gid1")
        self.assertEqual(len(res_pause), 1)

        self.mock_client.tell_status.return_value = {
            "gid": "gid1",
            "status": "active",
            "files": [],
        }
        res_resume = self.api.resume("gid1")
        self.mock_client.unpause.assert_called_once_with("gid1")
        self.assertEqual(len(res_resume), 1)

    def test_get_stats_success_and_fallback(self):
        # Success
        self.mock_client.get_global_stat.return_value = {
            "downloadSpeed": "5000",
            "uploadSpeed": "2000",
            "numActive": "1",
        }
        stats = self.api.get_stats()
        self.assertEqual(stats.download_speed, 5000)
        self.assertEqual(stats.upload_speed, 2000)

        # Fallback on RPC failure
        self.mock_client.get_global_stat.side_effect = XMLRPCClientException(
            1, "Unauthorized"
        )
        safe_stats = self.api.get_stats()
        self.assertEqual(safe_stats.download_speed, 0)
        self.assertEqual(safe_stats.num_active, 0)

    def test_pause_all_and_resume_all(self):
        self.mock_client.pause_all.return_value = "OK"
        self.mock_client.unpause_all.return_value = "OK"
        self.mock_client.tell_active.return_value = []
        self.mock_client.tell_waiting.return_value = []
        self.mock_client.tell_stopped.return_value = []

        self.api.pause_all()
        self.mock_client.pause_all.assert_called_once()

        self.api.resume_all()
        self.mock_client.unpause_all.assert_called_once()

    def test_purge_all(self):
        self.mock_client.purge_download_result.return_value = "OK"
        self.mock_client.tell_active.return_value = []
        self.mock_client.tell_waiting.return_value = []
        self.mock_client.tell_stopped.return_value = []
        res = self.api.purge()
        self.assertIsInstance(res, list)

    def test_file_operations_move_and_copy(self):
        with (
            tempfile.TemporaryDirectory() as src_dir,
            tempfile.TemporaryDirectory() as dst_dir,
        ):
            test_file = Path(src_dir) / "sample.txt"
            test_file.write_text("hello world")

            mock_dl = MagicMock()
            mock_dl.is_complete = True
            mock_dl.root_files_paths = [test_file]

            # Test move
            res = ShushaAPI.move_files([mock_dl], dst_dir)
            self.assertEqual(res, [True])
            dest_file = Path(dst_dir) / "sample.txt"
            self.assertTrue(dest_file.exists())
            self.assertFalse(test_file.exists())

            # Test copy
            with tempfile.TemporaryDirectory() as copy_dst:
                mock_dl.root_files_paths = [dest_file]
                res_copy = ShushaAPI.copy_files([mock_dl], copy_dst)
                self.assertEqual(res_copy, [True])
                self.assertTrue((Path(copy_dst) / "sample.txt").exists())


if __name__ == "__main__":
    unittest.main()
