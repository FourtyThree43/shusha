import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.controller.api import ShushaAPI
from shusha.models.structs_downloads import Download
from shusha.views.add_win import AddWindow
from shusha.views.torrent_win import TorrentFilesWindow


class TestTorrentFeatures(unittest.TestCase):
    def setUp(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def tearDown(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def test_api_add_torrent(self):
        mock_client = MagicMock()
        mock_client.add_torrent.return_value = "torrent123"
        api = ShushaAPI(client=mock_client)

        with tempfile.NamedTemporaryFile(suffix=".torrent") as f:
            f.write(b"d8:announce16:http://fake.torrent13:announce-liste")
            f.flush()
            result = api.add_torrent(f.name, options={"dir": "/tmp"})
            self.assertIsInstance(result, list)

    def test_api_add_metalink(self):
        mock_client = MagicMock()
        mock_client.add_metalink.return_value = "metalink123"
        api = ShushaAPI(client=mock_client)

        with tempfile.NamedTemporaryFile(suffix=".metalink") as f:
            f.write(b"<metalink></metalink>")
            f.flush()
            result = api.add_metalink(f.name, options={"dir": "/tmp"})
            self.assertIsInstance(result, list)

    def test_torrent_files_window_headless(self):
        try:
            root = ttk.Window(themename="darkly")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for TorrentFilesWindow test")

        mock_api = MagicMock()
        mock_download = MagicMock(spec=Download)
        mock_download.name = "MultiFileTorrent"
        mock_download.gid = "gid999"

        # Mock 3 files in torrent
        f1 = MagicMock()
        f1.index = "1"
        f1.path = Path("/downloads/file1.mp4")
        f1.length = 1048576
        f1.completed_length = 524288
        f1.selected = True

        f2 = MagicMock()
        f2.index = "2"
        f2.path = Path("/downloads/file2.srt")
        f2.length = 1024
        f2.completed_length = 1024
        f2.selected = True

        mock_download.files = [f1, f2]

        win = TorrentFilesWindow(master=root, api=mock_api, download=mock_download)
        self.assertIsInstance(win, ttk.Toplevel)

        # Test selecting/deselecting
        win._deselect_all()
        self.assertFalse(win.file_vars[1].get())
        self.assertFalse(win.file_vars[2].get())

        win.file_vars[1].set(True)
        win._apply_selection()

        mock_api.client.change_option.assert_called_with("gid999", {"select-file": "1"})
        root.destroy()

    def test_add_window_torrent_tab(self):
        try:
            root = ttk.Window(themename="darkly")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for AddWindow test")

        cb = MagicMock()
        win = AddWindow(callback=cb)
        win.torrent_file_var.set("/tmp/test.torrent")
        win.submit_torrent()

        cb.assert_called_once()
        args = cb.call_args[0]
        self.assertEqual(args[0][0].get(), "/tmp/test.torrent")
        root.destroy()


if __name__ == "__main__":
    unittest.main()
