import contextlib
import tkinter as tk
import unittest
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.views.app import Aria2Gui, relative_to_assets


class TestGuiSmoke(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

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
            with contextlib.suppress(Exception):
                icon_png = (
                    OUTPUT_PATH
                    / "resources"
                    / "assets"
                    / "icons8-bittorrent-new-64.png"
                )
                if icon_png.exists():
                    img = tk.PhotoImage(file=str(icon_png))
                    root.iconphoto(True, img)

        root.destroy()

    def test_aria2_gui_components(self):
        try:
            # Use modern ttkbootstrap 2.x theme
            root = ttk.Window(themename="bootstrap-dark")
            root.withdraw()
        except Exception:
            self.skipTest("No display available for Aria2Gui test")

        mock_api = MagicMock()
        mock_api.client = MagicMock()
        app = Aria2Gui(root, api=mock_api)
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

        # Test selection methods
        dls = app.get_selected_downloads()
        self.assertEqual(dls, [])
        dl = app.get_selected_download()
        self.assertIsNone(dl)

        # Test selection actions when nothing selected
        app.start_selected_download()
        app.pause_selected_download()
        app.remove_selected_download()
        app.open_uri_manager()

        root.destroy()


if __name__ == "__main__":
    unittest.main()
