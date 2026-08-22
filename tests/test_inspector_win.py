import unittest
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.controller.api import ShushaAPI
from shusha.models.structs_downloads import Download
from shusha.views.batch_add_win import BatchAddWindow
from shusha.views.inspector_win import DownloadInspectorWindow


class TestInspectorAndBatchWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = ttk.Window(themename="bootstrap-dark")
            cls.root.withdraw()
            cls.has_display = True
        except Exception:
            cls.has_display = False

    @classmethod
    def tearDownClass(cls):
        if cls.has_display and hasattr(cls, "root") and cls.root:
            cls.root.destroy()

    def test_batch_add_window(self):
        if not self.has_display:
            self.skipTest("No display available for Tkinter GUI test")

        cb = MagicMock()
        win = BatchAddWindow(
            master=self.root,
            callback=cb,
            initial_text="https://example.com/file[1-3].zip",
        )
        urls = win._parse_preview()
        self.assertEqual(len(urls), 3)

        win._on_submit()
        cb.assert_called_once()
        self.assertEqual(len(cb.call_args[0][0]), 3)

    def test_inspector_window(self):
        if not self.has_display:
            self.skipTest("No display available for Tkinter GUI test")

        mock_api = MagicMock(spec=ShushaAPI)
        mock_api.get_peers.return_value = []
        mock_api.get_servers.return_value = []

        mock_dl = MagicMock(spec=Download)
        mock_dl.gid = "gid_insp_test"
        mock_dl.name = "InspectorTest.iso"
        mock_dl.status = "active"
        mock_dl.num_pieces = 10
        mock_dl.num_completed_pieces = 5
        mock_dl.piece_length = 524288
        mock_dl.pieces_bool_array = [True] * 5 + [False] * 5
        mock_dl.completed_length_string.return_value = "2.5 MB"
        mock_dl.total_length_string.return_value = "5.0 MB"
        mock_dl.download_speed_string.return_value = "1.0 MB/s"
        mock_dl.upload_speed_string.return_value = "100 KB/s"
        mock_dl.progress_string.return_value = "50.0%"
        mock_dl.eta_string.return_value = "3s"
        mock_dl.dir = None
        mock_dl.connections = 4
        mock_dl.error_message = None
        mock_dl.files = []
        mock_dl.download_speed = 1048576
        mock_dl.upload_speed = 102400

        win = DownloadInspectorWindow(master=self.root, api=mock_api, download=mock_dl)
        self.assertIsNotNone(win.notebook)
        self.assertIsNotNone(win.speed_widget)
        self.assertIsNotNone(win.piece_widget)
        win.destroy()
