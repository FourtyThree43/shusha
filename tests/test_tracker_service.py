import unittest
from unittest.mock import MagicMock, patch

from shusha.models.tracker_service import DEFAULT_FALLBACK_TRACKERS, TrackerService


class TestTrackerService(unittest.TestCase):
    def test_get_trackers_fallback(self):
        trackers = TrackerService.get_trackers(force_refresh=False)
        self.assertTrue(len(trackers) > 0)
        self.assertIn(DEFAULT_FALLBACK_TRACKERS[0], trackers)

    def test_get_trackers_csv(self):
        csv = TrackerService.get_trackers_csv()
        self.assertIn(",", csv)
        self.assertIn("announce", csv)

    @patch("urllib.request.urlopen")
    def test_fetch_latest_trackers_sync(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"""
        # Best trackers
        udp://tracker.custom.org:6969/announce
        http://tracker.custom.org:80/announce
        """
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        trackers = TrackerService.fetch_latest_trackers_sync(
            sources=["http://fake.trackers.list/best.txt"]
        )
        self.assertIn("udp://tracker.custom.org:6969/announce", trackers)
        self.assertIn("http://tracker.custom.org:80/announce", trackers)
