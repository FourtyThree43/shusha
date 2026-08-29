import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from shusha.controller.api import ShushaAPI
from shusha.models.client import Client
from shusha.models.daemon import Daemon
from shusha.models.structs_downloads import Download
from shusha.models.structs_options import Options


class TestShushaAPI(unittest.TestCase):
    def setUp(self):
        self.mock_daemon = MagicMock(spec=Daemon)
        self.mock_client = MagicMock(spec=Client)
        self.mock_client.get_option.return_value = {}
        self.mock_client.get_global_option.return_value = {}
        self.mock_db = MagicMock()
        self.api = ShushaAPI(
            daemon=self.mock_daemon, client=self.mock_client, db=self.mock_db
        )

    def test_str_representation(self):
        s = str(self.api)
        self.assertIn("ShushaAPI", s)

    def test_start_stop_server(self):
        self.mock_daemon.start_server.return_value = 1234
        pid = self.api.start_server()
        self.assertEqual(pid, 1234)

        self.api.stop_server()
        self.mock_daemon.stop_server.assert_called_once()

    def test_daemon_management_methods(self):
        self.mock_daemon.start_server.return_value = 1234
        self.mock_daemon.restart_server.return_value = 5678
        self.mock_client.is_server_reachable.return_value = True

        pid_start = self.api.start_server()
        self.assertEqual(pid_start, 1234)

        self.api.stop_server()
        self.mock_daemon.stop_server.assert_called_once()

        pid_restart = self.api.restart_server()
        self.assertEqual(pid_restart, 5678)

        self.assertTrue(self.api.is_server_running())
        self.assertTrue(self.api.reconnect())

    def test_get_download_and_get_downloads(self):
        self.mock_client.tell_status.return_value = {
            "gid": "gid1",
            "status": "active",
            "files": [],
        }
        dl = self.api.get_download("gid1")
        self.assertIsInstance(dl, Download)
        self.assertEqual(dl.gid, "gid1")

        # Specific gids
        dls = self.api.get_downloads(["gid1"])
        self.assertEqual(len(dls), 1)

        # All downloads (active, waiting, stopped)
        self.mock_client.tell_active.return_value = [
            {"gid": "g1", "status": "active", "files": []}
        ]
        self.mock_client.tell_waiting.return_value = [
            {"gid": "g2", "status": "waiting", "files": []}
        ]
        self.mock_client.tell_stopped.return_value = [
            {"gid": "g3", "status": "complete", "files": []}
        ]
        all_dls = self.api.get_downloads()
        self.assertEqual(len(all_dls), 3)

    def test_add_and_add_uris(self):
        self.mock_client.add_uri.return_value = "gid_add_test"
        self.mock_client.tell_status.return_value = {
            "gid": "gid_add_test",
            "status": "active",
            "files": [],
        }
        res_list = self.api.add(
            ["http://example.com/test.zip"], options={"dir": "/tmp"}
        )
        self.assertEqual(len(res_list), 1)
        self.assertEqual(res_list[0].gid, "gid_add_test")

        dl = self.api.add_uris(["http://example.com/test.zip"])
        self.assertIsNotNone(dl)
        assert dl is not None
        self.assertEqual(dl.gid, "gid_add_test")

    def test_add_magnet_and_metalink(self):
        self.mock_client.add_magnet.return_value = "mag_gid"
        self.mock_client.tell_status.return_value = {
            "gid": "mag_gid",
            "status": "active",
            "files": [],
        }
        res_mag = self.api.add_magnet("magnet:?xt=urn:btih:xyz")
        self.assertEqual(len(res_mag), 1)

        self.mock_client.add_metalink.return_value = ["meta_gid"]
        self.mock_client.tell_status.return_value = {
            "gid": "meta_gid",
            "status": "active",
            "files": [],
        }
        res_meta = self.api.add_metalink("/path/to/meta.metalink")
        self.assertEqual(len(res_meta), 1)

    def test_add_torrent(self):
        self.mock_client.add_torrent.return_value = "tor_gid"
        self.mock_client.tell_status.return_value = {
            "gid": "tor_gid",
            "status": "active",
            "files": [],
        }
        res = self.api.add_torrent("/path/to/sample.torrent")
        self.assertEqual(len(res), 1)

    def test_pause_and_resume(self):
        self.mock_client.tell_status.return_value = {
            "gid": "gid1",
            "status": "paused",
            "files": [],
        }
        res_pause = self.api.pause("gid1", force=True)
        self.mock_client.force_pause.assert_called_once_with("gid1")
        self.assertEqual(len(res_pause), 1)

        self.mock_client.tell_status.return_value = {
            "gid": "gid1",
            "status": "active",
            "files": [],
        }
        res_resume = self.api.resume("gid1")
        self.mock_client.unpause.assert_called_once_with("gid1")
        self.assertEqual(len(res_resume), 1)

    def test_pause_all_and_resume_all_and_unpause_all(self):
        self.mock_client.pause_all.return_value = "OK"
        self.mock_client.unpause_all.return_value = "OK"
        self.mock_client.tell_active.return_value = []
        self.mock_client.tell_waiting.return_value = []
        self.mock_client.tell_stopped.return_value = []

        self.api.pause_all()
        self.mock_client.pause_all.assert_called_once()

        self.api.resume_all()
        self.mock_client.unpause_all.assert_called_once()

        self.api.unpause_all()
        self.assertEqual(self.mock_client.unpause_all.call_count, 2)

    def test_remove_with_force_and_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "test.iso"
            fpath.write_text("dummy")

            mock_file = MagicMock()
            mock_file.path = fpath

            self.mock_client.tell_status.return_value = {
                "gid": "gid_rm",
                "status": "active",
                "files": [{"path": str(fpath)}],
            }
            res = self.api.remove("gid_rm", force=True, files=True)
            self.mock_client.force_remove.assert_called_once_with("gid_rm")
            self.assertEqual(len(res), 1)

    def test_queue_movement_methods(self):
        mock_dl = MagicMock()
        mock_dl.gid = "gid_move"

        self.mock_client.change_position.return_value = 0
        self.assertEqual(self.api.move(mock_dl, 2), 0)
        self.mock_client.change_position.assert_called_with("gid_move", 2, "POS_CUR")

        self.api.move_to(mock_dl, 0)
        self.mock_client.change_position.assert_called_with("gid_move", 0, "POS_SET")

        self.api.move_to(mock_dl, -1)
        self.mock_client.change_position.assert_called_with("gid_move", 1, "POS_END")

        self.api.move_up(mock_dl, 1)
        self.mock_client.change_position.assert_called_with("gid_move", -1, "POS_CUR")

        self.api.move_down(mock_dl, 2)
        self.mock_client.change_position.assert_called_with("gid_move", 2, "POS_CUR")

        self.api.move_to_top(mock_dl)
        self.mock_client.change_position.assert_called_with("gid_move", 0, "POS_SET")

        self.api.move_to_bottom(mock_dl)
        self.mock_client.change_position.assert_called_with("gid_move", 0, "POS_END")

    def test_purge(self):
        self.mock_client.purge_download_result.return_value = "OK"
        self.mock_client.tell_active.return_value = []
        self.mock_client.tell_waiting.return_value = []
        self.mock_client.tell_stopped.return_value = []
        res = self.api.purge()
        self.assertIsInstance(res, list)
        self.mock_db.purge.assert_called_once()
        self.mock_client.purge_download_result.assert_called_once()

    def test_options_and_global_options(self):
        mock_dl = MagicMock()
        mock_dl.gid = "gid_opt"
        self.mock_client.get_option.return_value = {"max-download-limit": "100K"}
        opts = self.api.get_options([mock_dl])
        self.assertEqual(len(opts), 1)

        self.mock_client.change_option.return_value = "OK"
        res_set = self.api.set_options({"max-download-limit": "200K"}, [mock_dl])
        self.assertEqual(res_set, [True])

        self.mock_client.get_global_option.return_value = {
            "max-concurrent-downloads": "5"
        }
        g_opt = self.api.get_global_options()
        self.assertIsInstance(g_opt, Options)

        self.mock_client.change_global_option.return_value = "OK"
        self.assertTrue(self.api.set_global_options({"max-concurrent-downloads": "10"}))

    def test_get_peers_and_servers(self):
        self.mock_client.get_peers.return_value = [{"ip": "1.2.3.4", "port": "6881"}]
        peers = self.api.get_peers("gid_peers")
        self.assertEqual(len(peers), 1)

        self.mock_client.get_servers.return_value = [
            {"servers": [{"uri": "http://mirror.com"}]}
        ]
        servers = self.api.get_servers("gid_servers")
        self.assertEqual(len(servers), 1)

    def test_change_uri_and_speed_limits(self):
        self.mock_client.change_uri.return_value = [1, 1]
        res = self.api.change_uri(
            "gid_uri", file_index=1, del_uris=["http://old"], add_uris=["http://new"]
        )
        self.assertEqual(res, [1, 1])

        self.mock_client.change_option.return_value = "OK"
        res_limit = self.api.change_download_speed_limits(
            "gid_limit", max_download="1M", max_upload="500K"
        )
        self.assertTrue(res_limit)

        self.assertTrue(self.api.change_download_speed_limits("gid_limit"))

    def test_retry_downloads(self):
        # Non-failed download
        mock_ok = MagicMock()
        mock_ok.has_failed = False
        res = self.api.retry_downloads([mock_ok])
        self.assertEqual(res, [])

        # Failed download
        mock_failed = MagicMock()
        mock_failed.has_failed = True
        mock_file = MagicMock()
        mock_file.uris = [{"uri": "http://example.com/file.zip"}]
        mock_failed.files = [mock_file]
        mock_failed.options = {}
        mock_failed.gid = "gid_fail"

        self.mock_client.add_uri.return_value = "gid_retried"
        self.mock_client.tell_status.return_value = {
            "gid": "gid_retried",
            "status": "active",
            "files": [],
        }
        res_retry = self.api.retry_downloads([mock_failed])
        self.assertEqual(res_retry, [True])

    def test_file_operations_remove_move_copy(self):
        with (
            tempfile.TemporaryDirectory() as src_dir,
            tempfile.TemporaryDirectory() as dst_dir,
        ):
            test_file = Path(src_dir) / "sample.txt"
            test_file.write_text("hello world")

            test_subdir = Path(src_dir) / "subdir"
            test_subdir.mkdir()
            (test_subdir / "sub.txt").write_text("sub")

            mock_dl = MagicMock()
            mock_dl.is_complete = True
            mock_dl.root_files_paths = [test_file, test_subdir]

            # Test copy
            with tempfile.TemporaryDirectory() as copy_dst:
                res_copy = ShushaAPI.copy_files([mock_dl], copy_dst)
                self.assertEqual(res_copy, [True])
                self.assertTrue((Path(copy_dst) / "sample.txt").exists())
                self.assertTrue((Path(copy_dst) / "subdir" / "sub.txt").exists())

            # Test move
            res_move = ShushaAPI.move_files([mock_dl], dst_dir)
            self.assertEqual(res_move, [True])
            self.assertTrue((Path(dst_dir) / "sample.txt").exists())

            # Test remove
            mock_dl_dst = MagicMock()
            mock_dl_dst.is_complete = True
            mock_dl_dst.root_files_paths = [
                Path(dst_dir) / "sample.txt",
                Path(dst_dir) / "subdir",
            ]
            res_rm = ShushaAPI.remove_files([mock_dl_dst], force=True)
            self.assertEqual(res_rm, [True, True])


if __name__ == "__main__":
    unittest.main()
