import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import ttkbootstrap as ttk

from shusha.models.settings import AppSettings
from shusha.models.utilities import dump_toml, save_configuration
from shusha.views.settings_win import SettingsWindow


class TestSettingsWindowAndConfig(unittest.TestCase):
    def setUp(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def tearDown(self):
        with contextlib.suppress(Exception):
            ttk.Style.instance = None

    def test_dump_toml(self):
        data = {
            "aria2": {
                "host": "127.0.0.1",
                "port": 6800,
                "continue": True,
            },
            "theme": "bootstrap-dark",
        }
        res = dump_toml(data)
        self.assertIn("[aria2]", res)
        self.assertIn('host = "127.0.0.1"', res)
        self.assertIn("port = 6800", res)
        self.assertIn("continue = true", res)
        self.assertIn('theme = "bootstrap-dark"', res)

    def test_save_configuration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "config.toml"
            cfg_data = {
                "USER": {
                    "download_dir": "/tmp/downloads",
                    "aria2": {"port": 6800},
                }
            }
            success = save_configuration(cfg_data, config_path=cfg_path)
            self.assertTrue(success)
            self.assertTrue(cfg_path.exists())
            content = cfg_path.read_text(encoding="utf-8")
            self.assertIn("[aria2]", content)
            self.assertIn("6800", content)

    def test_app_settings_setters(self):
        settings = AppSettings()
        settings.set_download_dir("/tmp/test_dl")
        self.assertEqual(settings.get_download_dir(), "/tmp/test_dl")

        settings.set_logs_dir("/tmp/test_logs")
        self.assertEqual(settings.get_logs_dir(), "/tmp/test_logs")

        settings.set_aria2_config(host="192.168.1.50", port=6801, secret="supertoken")
        self.assertEqual(settings.get_aria2_host(), "192.168.1.50")
        self.assertEqual(settings.get_aria2_port(), 6801)
        self.assertEqual(settings.get_aria2_secret(), "supertoken")

    def test_settings_window_headless(self):
        try:
            root = ttk.Window(themename="bootstrap-dark")
            root.withdraw()
        except Exception:
            self.skipTest("Display not available for Tkinter SettingsWindow test")

        mock_api = MagicMock()
        mock_callback = MagicMock()

        win = SettingsWindow(master=root, api=mock_api, on_saved=mock_callback)
        self.assertIsInstance(win, ttk.Toplevel)

        # Test value modification and save
        win.max_concurrent_var.set("10")
        win._save_and_apply()

        # Verify callback was called
        mock_callback.assert_called_once()
        root.destroy()


if __name__ == "__main__":
    unittest.main()
