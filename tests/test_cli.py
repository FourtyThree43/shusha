import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shusha.cli import build_parser, handle_cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_version_flag(self):
        args = self.parser.parse_args(["--version"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args)
            self.assertEqual(ret, 0)
            self.assertIn("Shusha", mock_out.getvalue())

    @patch("shusha.cli.ShushaAPI")
    def test_daemon_subcommands(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.start_server.return_value = 1234
        mock_api.is_server_running.return_value = True
        mock_api_cls.return_value = mock_api

        # Start
        args = self.parser.parse_args(["daemon", "start"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.start_server.assert_called_once()

        # Stop
        args = self.parser.parse_args(["daemon", "stop"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.stop_server.assert_called_once()

        # Status
        args = self.parser.parse_args(["daemon", "status"])
        self.assertEqual(handle_cli(args), 0)

    @patch("shusha.cli.ShushaAPI")
    def test_add_and_list_subcommands(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.add_uris.return_value = MagicMock(name="test.zip", gid="111")
        mock_api.get_downloads.return_value = []
        mock_api_cls.return_value = mock_api

        args = self.parser.parse_args(
            ["add", "http://example.com/test.zip", "--split", "4"]
        )
        self.assertEqual(handle_cli(args), 0)
        mock_api.add_uris.assert_called_once()

        args = self.parser.parse_args(["list"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.get_downloads.assert_called_once()

    @patch("shusha.cli.ShushaAPI")
    def test_pause_resume_remove_subcommands(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api_cls.return_value = mock_api

        # Pause
        args = self.parser.parse_args(["pause", "gid123"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.pause.assert_called_once_with("gid123")

        # Resume
        args = self.parser.parse_args(["resume", "gid123"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.resume.assert_called_once_with("gid123")

        # Remove
        args = self.parser.parse_args(["remove", "gid123", "--files"])
        self.assertEqual(handle_cli(args), 0)
        mock_api.remove.assert_called_once_with("gid123", files=True)

    def test_hash_subcommand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "data.bin"
            fpath.write_bytes(b"Test Hash Content")

            args = self.parser.parse_args(["hash", str(fpath)])
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                ret = handle_cli(args)
                self.assertEqual(ret, 0)
                self.assertIn("MD5", mock_out.getvalue())
                self.assertIn("SHA256", mock_out.getvalue())


if __name__ == "__main__":
    unittest.main()
