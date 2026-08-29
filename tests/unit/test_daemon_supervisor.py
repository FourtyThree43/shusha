"""
Unit tests for the aria2 daemon supervisor, discovery, and configuration.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.discovery import (
    find_aria2_executable,
    validate_executable,
)
from shusha.infrastructure.daemon.health import DaemonHealthStatus, probe_daemon_health
from shusha.infrastructure.daemon.manager import DaemonSupervisor
from shusha.infrastructure.daemon.process import DaemonProcess


class TestDaemonSupervisor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.download_dir = Path(self.temp_dir.name) / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.config = DaemonConfig(
            port=6800,
            secret="supersecret",
            download_dir=self.download_dir,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_daemon_config_arguments(self):
        args = self.config.build_cli_arguments()
        self.assertIn("--enable-rpc=true", args)
        self.assertIn("--rpc-listen-port=6800", args)
        self.assertIn("--rpc-secret=supersecret", args)

        # Redacted arguments should obscure secret
        redacted = self.config.build_redacted_arguments()
        self.assertIn("--rpc-secret=******", redacted)
        self.assertNotIn("--rpc-secret=supersecret", redacted)

    def test_daemon_conf_file_generation(self):
        conf_str = self.config.generate_conf_content()
        self.assertIn("enable-rpc=true", conf_str)
        self.assertIn("rpc-listen-port=6800", conf_str)
        self.assertIn("rpc-secret=supersecret", conf_str)

    def test_executable_discovery(self):
        exe = find_aria2_executable()
        # On this environment, aria2c is installed
        if exe:
            self.assertTrue(validate_executable(exe))
            self.assertTrue(exe.exists())

    @patch("subprocess.Popen")
    def test_daemon_process_lifecycle(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        exe_path = Path("/usr/bin/aria2c")
        if not exe_path.exists():
            exe_path = Path("/bin/sh")  # fallback dummy executable for test

        dp = DaemonProcess(executable_path=exe_path, config=self.config)
        started = dp.start()
        self.assertTrue(started)
        self.assertEqual(dp.pid, 12345)
        self.assertTrue(dp.is_running)

        stopped = dp.terminate()
        self.assertTrue(stopped)
        mock_proc.terminate.assert_called_once()

    @patch("shusha.infrastructure.daemon.manager.is_port_in_use")
    @patch("shusha.infrastructure.daemon.manager.find_aria2_executable")
    @patch("subprocess.Popen")
    def test_supervisor_start_and_stop(self, mock_popen, mock_find, mock_port):
        mock_port.side_effect = [
            False,
            True,
            True,
        ]  # 1st check: free, 2nd: started, 3rd: running
        mock_find.return_value = Path("/bin/sh")

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 54321
        mock_popen.return_value = mock_proc

        pid_file = Path(self.temp_dir.name) / "aria2.pid"
        supervisor = DaemonSupervisor(config=self.config, pid_file=pid_file)

        started = supervisor.start()
        self.assertTrue(started)
        self.assertTrue(pid_file.exists())
        self.assertEqual(pid_file.read_text(encoding="utf-8"), "54321")

        stopped = supervisor.stop()
        self.assertTrue(stopped)
        self.assertFalse(pid_file.exists())

    @patch("shusha.infrastructure.aria2.jsonrpc.JsonRpcTransport.call")
    def test_probe_daemon_health(self, mock_call):
        mock_call.return_value = {"version": "1.37.0", "enabledFeatures": []}
        report = probe_daemon_health(host="127.0.0.1", port=6800, secret="token")
        self.assertEqual(report.status, DaemonHealthStatus.HEALTHY)
        self.assertEqual(report.version, "1.37.0")
        self.assertIsNotNone(report.latency_ms)


if __name__ == "__main__":
    unittest.main()
