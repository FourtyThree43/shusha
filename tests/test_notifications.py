import unittest
from unittest.mock import patch

from shusha.models.utilities import send_desktop_notification


class TestNotifications(unittest.TestCase):
    @patch("shutil.which", return_value="/usr/bin/notify-send")
    @patch("subprocess.Popen")
    def test_send_desktop_notification_linux(self, mock_popen, mock_which):
        with patch("sys.platform", "linux"):
            res = send_desktop_notification("Test Title", "Test Message")
            self.assertTrue(res)
            mock_popen.assert_called_once_with(
                ["/usr/bin/notify-send", "Test Title", "Test Message"]
            )

    @patch("subprocess.Popen")
    def test_send_desktop_notification_darwin(self, mock_popen):
        with patch("sys.platform", "darwin"):
            res = send_desktop_notification("Test Title", "Test Message")
            self.assertTrue(res)
            mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_send_desktop_notification_windows(self, mock_popen):
        with patch("sys.platform", "win32"):
            res = send_desktop_notification("Test Title", "Test Message")
            self.assertTrue(res)
            mock_popen.assert_called_once()

    def test_send_desktop_notification_fallback(self):
        with patch("sys.platform", "unknown_os"):
            res = send_desktop_notification("Title", "Message")
            self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
