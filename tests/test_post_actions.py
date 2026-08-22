import unittest
from unittest.mock import patch

from shusha.models.post_actions import PostActions


class TestPostActions(unittest.TestCase):
    def test_play_alert_sound(self):
        # Should execute without throwing unhandled exceptions
        with patch("subprocess.Popen"):
            PostActions.play_alert_sound()

    def test_execute_completion_command(self):
        with patch("subprocess.Popen") as mock_popen:
            cmd = "notify-send '{file}' '{gid}'"
            res = PostActions.execute_completion_command(
                cmd,
                file_path="/tmp/test.iso",
                dir_path="/tmp",
                gid="12345",
            )
            self.assertTrue(res)
            mock_popen.assert_called_once()
            called_cmd = mock_popen.call_args[0][0]
            self.assertEqual(called_cmd, "notify-send '/tmp/test.iso' '12345'")

    def test_empty_command(self):
        res = PostActions.execute_completion_command("")
        self.assertFalse(res)

    def test_shutdown_and_sleep_system(self):
        with patch("subprocess.Popen") as mock_popen:
            self.assertTrue(PostActions.shutdown_system())
            self.assertTrue(PostActions.sleep_system())
            self.assertEqual(mock_popen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
