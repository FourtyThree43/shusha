import unittest

import ttkbootstrap as ttk

from shusha.views.speed_graph import SpeedGraphWidget


class TestSpeedGraphWidget(unittest.TestCase):
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

    def test_speed_graph_data_accumulation(self):
        if not self.has_display:
            self.skipTest("No display available for Tkinter GUI test")

        widget = SpeedGraphWidget(self.root, max_points=10)
        widget.add_data_point(1048576, 262144)
        self.assertEqual(widget.down_history[-1], 1048576)
        self.assertEqual(widget.up_history[-1], 262144)
        self.assertIn("1.0 MB/s", widget.down_label.cget("text"))

        widget.redraw()
        widget.destroy()
