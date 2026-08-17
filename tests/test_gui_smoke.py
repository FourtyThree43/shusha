import contextlib
import tkinter as tk
import unittest

import ttkbootstrap as ttk

from shusha.views.app import Aria2Gui, relative_to_assets


class TestGuiSmoke(unittest.TestCase):
    def setUp(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def tearDown(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def test_relative_to_assets(self):
        asset_path = relative_to_assets("icons8-add-64.png")
        self.assertTrue(str(asset_path).endswith("icons8-add-64.png"))

    def test_gui_smoke_or_headless(self):
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
            has_display = True
        except Exception:
            has_display = False

        if not has_display:
            self.skipTest("No X11/Wayland display available for Tk GUI smoke test")

    def test_icon_loading_safety(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except Exception:
            self.skipTest("No display available for icon loading test")

        from shusha.ShushaDM import ICON_PATH, OUTPUT_PATH

        try:
            root.iconbitmap(str(ICON_PATH))
        except Exception:
            icon_png = (
                OUTPUT_PATH / "resources" / "assets" / "icons8-bittorrent-new-64.png"
            )
            if icon_png.exists():
                img = tk.PhotoImage(file=str(icon_png))
                root.iconphoto(True, img)

        root.destroy()

    def test_aria2_gui_components(self):
        try:
            root = ttk.Window(themename="darkly")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for Aria2Gui test")

        app = Aria2Gui(root)
        self.assertIsNotNone(app.dt)
        self.assertIsNotNone(app.category_combo)
        self.assertIn("Download Speed", app.stats_vars)

        # Test category change
        app.category_combo.set("Active")
        app.on_category_changed()
        self.assertEqual(app.active_category, "Active")

        # Test context menu exists
        self.assertIsNotNone(app.context_menu)

        # Test queue actions
        app.start_queue()
        app.pause_queue()
        app.clear_queue()

        # Test tray actions
        app.minimize_to_tray()
        app.restore_from_tray()

        # Test logs directory opening
        app.open_logs_directory()

        root.destroy()


if __name__ == "__main__":
    unittest.main()
