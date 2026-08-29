import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shusha.cli import build_parser, handle_cli
from shusha.domain.identifiers import DownloadId


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_version_flag(self):
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(["--version"])
        self.assertEqual(cm.exception.code, 0)

    @patch("shusha.cli.build_app_context")
    def test_daemon_subcommands(self, mock_build_ctx):
        mock_ctx = MagicMock()
        mock_ctx.daemon_supervisor.start.return_value = True
        mock_ctx.daemon_supervisor.stop.return_value = True
        mock_ctx.daemon_supervisor.get_health.return_value = MagicMock(
            status=MagicMock(value="HEALTHY"), version="1.37.0", latency_ms=2
        )
        mock_build_ctx.return_value = mock_ctx

        # Start
        args = self.parser.parse_args(["daemon", "start"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.daemon_supervisor.start.assert_called_once()

        # Stop
        args = self.parser.parse_args(["daemon", "stop"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.daemon_supervisor.stop.assert_called_once()

        # Status
        args = self.parser.parse_args(["daemon", "status"])
        self.assertEqual(handle_cli(args), 0)

    @patch("shusha.cli.build_app_context")
    def test_add_and_list_subcommands(self, mock_build_ctx):
        mock_ctx = MagicMock()
        mock_ctx.add_download_uc.execute.return_value = [DownloadId("dl-100")]
        mock_ctx.download_repo.list_all.return_value = []
        mock_build_ctx.return_value = mock_ctx

        args = self.parser.parse_args(
            ["add", "http://example.com/test.zip", "--split", "4"]
        )
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.add_download_uc.execute.assert_called_once()

        args = self.parser.parse_args(["list"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.download_repo.list_all.assert_called_once()

    @patch("shusha.cli.build_app_context")
    def test_pause_resume_remove_subcommands(self, mock_build_ctx):
        mock_ctx = MagicMock()
        mock_build_ctx.return_value = mock_ctx

        # Pause
        args = self.parser.parse_args(["pause", "dl-123"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.pause_download_uc.execute.assert_called_once_with(
            DownloadId("dl-123"), force=False
        )

        # Resume
        args = self.parser.parse_args(["resume", "dl-123"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.resume_download_uc.execute.assert_called_once_with(
            DownloadId("dl-123")
        )

        # Remove
        args = self.parser.parse_args(["remove", "dl-123", "--files"])
        self.assertEqual(handle_cli(args), 0)
        mock_ctx.remove_download_uc.execute.assert_called_once_with(
            DownloadId("dl-123"), delete_files=True, force=False
        )

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
