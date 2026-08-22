import time
import unittest
from unittest.mock import MagicMock

from shusha.models.clipboard_watcher import ClipboardWatcher


class TestClipboardWatcher(unittest.TestCase):
    def test_is_downloadable_url(self):
        self.assertTrue(ClipboardWatcher.is_downloadable_url("http://example.com/file.zip"))
        self.assertTrue(ClipboardWatcher.is_downloadable_url("https://example.com/video.mp4"))
        self.assertTrue(ClipboardWatcher.is_downloadable_url("ftp://ftp.example.com/iso.iso"))
        self.assertTrue(ClipboardWatcher.is_downloadable_url("magnet:?xt=urn:btih:abcdef123456"))
        self.assertFalse(ClipboardWatcher.is_downloadable_url("just some plain text"))
        self.assertFalse(ClipboardWatcher.is_downloadable_url(""))
        self.assertFalse(ClipboardWatcher.is_downloadable_url("http://example.com/link with invalid spaces.zip"))

    def test_clipboard_watcher_polling_and_callback(self):
        mock_callback = MagicMock()
        mock_getter = MagicMock(return_value="https://example.com/test_clip.iso")

        watcher = ClipboardWatcher(
            on_url_detected=mock_callback,
            poll_interval=0.05,
            clipboard_getter=mock_getter,
        )

        watcher.start()
        self.assertTrue(watcher.is_running())
        time.sleep(0.15)
        watcher.stop()
        self.assertFalse(watcher.is_running())

        mock_callback.assert_called_with("https://example.com/test_clip.iso")

    def test_clipboard_watcher_pause_resume(self):
        watcher = ClipboardWatcher(poll_interval=0.1)
        self.assertFalse(watcher._paused)
        watcher.pause()
        self.assertTrue(watcher._paused)
        watcher.resume()
        self.assertFalse(watcher._paused)


if __name__ == "__main__":
    unittest.main()
