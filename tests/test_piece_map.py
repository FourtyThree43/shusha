import unittest
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.models.structs_downloads import Download
from shusha.views.piece_map import PieceMapWidget


class TestPieceMapWidget(unittest.TestCase):
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

    def test_piece_map_bitfield_rendering(self):
        if not self.has_display:
            self.skipTest("No display available for Tkinter GUI test")

        mock_dl = MagicMock(spec=Download)
        mock_dl.num_pieces = 16
        mock_dl.num_completed_pieces = 8
        mock_dl.piece_length = 1048576
        mock_dl.pieces_bool_array = [True, False] * 8

        widget = PieceMapWidget(self.root, download=mock_dl)
        self.assertIsNotNone(widget.canvas)
        self.assertIn("8 / 16", widget.info_label.cget("text"))

        widget.update_download(mock_dl)
        widget.redraw()
        widget.destroy()
