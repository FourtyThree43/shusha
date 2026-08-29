"""
Unit tests for Shusha 2 CLI commands, parser, and diagnostic tools.
"""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shusha.cli import build_parser, handle_cli
from shusha.infrastructure.os_integration.desktop_entry import (
    generate_desktop_entry,
    install_desktop_entry,
)


class TestCliCommands(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_help(self):
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_version(self):
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_args(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_doctor(self):
        args = self.parser.parse_args(["doctor"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args)
            self.assertEqual(ret, 0)
            self.assertIn("System Diagnostics", mock_out.getvalue())

        args_json = self.parser.parse_args(["doctor", "--json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args_json)
            self.assertEqual(ret, 0)
            data = json.loads(mock_out.getvalue())
            self.assertIn("system", data)
            self.assertIn("aria2", data)

    def test_cli_daemon_status(self):
        args = self.parser.parse_args(["daemon", "status"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args)
            self.assertIn(ret, (0, 1))
            self.assertIn("Daemon Status:", mock_out.getvalue())

    def test_cli_list(self):
        args = self.parser.parse_args(["list"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args)
            self.assertEqual(ret, 0)

        args_json = self.parser.parse_args(["list", "--format", "json"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            ret = handle_cli(args_json)
            self.assertEqual(ret, 0)
            parsed = json.loads(mock_out.getvalue())
            self.assertIsInstance(parsed, list)

    def test_desktop_entry_generation_and_installation(self):
        entry_content = generate_desktop_entry(exec_command="shusha")
        self.assertIn("[Desktop Entry]", entry_content)
        self.assertIn("Exec=shusha %U", entry_content)
        self.assertIn("MimeType=", entry_content)

        target_dir = Path(self.temp_dir.name) / "applications"
        installed_path = install_desktop_entry(target_dir=target_dir)
        self.assertTrue(installed_path.exists())
        self.assertEqual(installed_path.name, "shusha.desktop")


if __name__ == "__main__":
    unittest.main()
