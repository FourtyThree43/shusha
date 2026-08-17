import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shusha.models.utilities import open_path_in_file_manager


class TestPathOpening(unittest.TestCase):
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_linux_xdg_open(self, mock_popen, mock_which):
        mock_which.side_effect = lambda cmd: (
            "/usr/bin/xdg-open" if cmd == "xdg-open" else None
        )
        with patch.object(sys, "platform", "linux"):
            res = open_path_in_file_manager("/tmp/test_dir")
            self.assertTrue(res)
            mock_popen.assert_called_once_with(["/usr/bin/xdg-open", "/tmp/test_dir"])

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_linux_gio_fallback(self, mock_popen, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/gio" if cmd == "gio" else None
        with patch.object(sys, "platform", "linux"):
            res = open_path_in_file_manager("/tmp/test_dir")
            self.assertTrue(res)
            mock_popen.assert_called_once_with(
                ["/usr/bin/gio", "open", "/tmp/test_dir"]
            )

    @patch("shutil.which")
    def test_open_linux_no_launcher_graceful(self, mock_which):
        mock_which.return_value = None
        with patch.object(sys, "platform", "linux"):
            res = open_path_in_file_manager("/tmp/test_dir")
            self.assertFalse(res)

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_darwin(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/open"
        with patch.object(sys, "platform", "darwin"):
            res = open_path_in_file_manager("/tmp/test_dir")
            self.assertTrue(res)
            mock_popen.assert_called_once_with(["open", "/tmp/test_dir"])

    def test_open_windows(self):
        mock_startfile = MagicMock()
        with (
            patch.object(sys, "platform", "win32"),
            patch.object(os, "startfile", mock_startfile, create=True),
        ):
            res = open_path_in_file_manager(Path("/tmp/test_dir"))
            self.assertTrue(res)
            mock_startfile.assert_called_once_with("/tmp/test_dir")


if __name__ == "__main__":
    unittest.main()
