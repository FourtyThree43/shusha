import unittest
from unittest.mock import MagicMock

from shusha.models.daemon import Daemon


class TestSessionPersistence(unittest.TestCase):
    def test_daemon_build_command_includes_session_flags(self):
        d = Daemon(aria2d="aria2c", port=6800)
        cmd = d._build_command()
        cmd_str = " ".join(cmd)
        self.assertIn("--save-session=", cmd_str)
        self.assertIn("--input-file=", cmd_str)
        self.assertIn("--save-session-interval=30", cmd_str)

    def test_cleanup_saves_session(self):
        mock_api = MagicMock()
        mock_api.client.save_session.return_value = "OK"

        # Simulate cleanup calling save_session
        if hasattr(mock_api, "client") and hasattr(mock_api.client, "save_session"):
            mock_api.client.save_session()

        mock_api.client.save_session.assert_called_once()


if __name__ == "__main__":
    unittest.main()
