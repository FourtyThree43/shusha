import unittest
from unittest.mock import MagicMock, patch

from shusha.models.daemon import Daemon


class TestDaemon(unittest.TestCase):
    def test_daemon_init_defaults(self):
        d = Daemon(host="127.0.0.1", port=6801, timeout=30.0)
        self.assertEqual(d.host, "127.0.0.1")
        self.assertEqual(d.port, 6801)
        self.assertEqual(d.timeout, 30.0)
        self.assertIn("127.0.0.1", str(d))
        self.assertIn("6801", repr(d))

    def test_build_command(self):
        d = Daemon(aria2d="aria2c", port=6800)
        cmd = d._build_command()
        self.assertTrue(len(cmd) > 0)
        self.assertEqual(cmd[0], "aria2c")

    @patch("subprocess.Popen")
    def test_start_and_stop_server(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        d = Daemon(aria2d="aria2c")
        with patch("time.sleep"):
            pid = d.start_server()
            self.assertEqual(pid, 9999)
            self.assertEqual(d.process, mock_proc)

            d.stop_server()
            mock_proc.terminate.assert_called_once()
            self.assertIsNone(d.process)


if __name__ == "__main__":
    unittest.main()
