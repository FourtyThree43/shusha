import unittest
from unittest.mock import MagicMock, patch

from shusha.models.mirror_prober import MirrorProber, MirrorProbeResult


class TestMirrorProber(unittest.TestCase):
    def test_probe_result_dataclass(self):
        res = MirrorProbeResult(
            url="http://mirror1.example.org/ubuntu.iso",
            is_alive=True,
            latency_ms=45.2,
            supports_ranges=True,
            content_length=2000000,
            status_code=200,
        )
        self.assertEqual(res.host, "mirror1.example.org")
        self.assertTrue(res.is_alive)

    @patch("urllib.request.urlopen")
    def test_probe_single_mirror_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": "10485760",
        }
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = MirrorProber.probe_single_mirror(
            "http://fast.mirror.org/test.iso", timeout=1.0
        )
        self.assertTrue(res.is_alive)
        self.assertTrue(res.supports_ranges)
        self.assertEqual(res.content_length, 10485760)

    @patch("urllib.request.urlopen")
    def test_probe_single_mirror_failure(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Connection timed out")
        res = MirrorProber.probe_single_mirror(
            "http://dead.mirror.org/test.iso", timeout=1.0
        )
        self.assertFalse(res.is_alive)
        self.assertIn("timed out", str(res.error))

    @patch.object(MirrorProber, "probe_single_mirror")
    def test_probe_multiple_mirrors_and_sorting(self, mock_probe_single):
        def _mock_probe(url, timeout=3.0):
            if "fast" in url:
                return MirrorProbeResult(
                    url=url,
                    is_alive=True,
                    latency_ms=12.0,
                    supports_ranges=True,
                    content_length=100,
                    status_code=200,
                )
            elif "slow" in url:
                return MirrorProbeResult(
                    url=url,
                    is_alive=True,
                    latency_ms=150.0,
                    supports_ranges=True,
                    content_length=100,
                    status_code=200,
                )
            else:
                return MirrorProbeResult(
                    url=url,
                    is_alive=False,
                    latency_ms=9999.0,
                    supports_ranges=False,
                    content_length=None,
                    status_code=0,
                )

        mock_probe_single.side_effect = _mock_probe
        urls = [
            "http://slow.mirror.com/file",
            "http://dead.mirror.com/file",
            "http://fast.mirror.com/file",
        ]
        results = MirrorProber.probe_mirrors(urls)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].url, "http://fast.mirror.com/file")
        self.assertEqual(results[1].url, "http://slow.mirror.com/file")
        self.assertEqual(results[2].url, "http://dead.mirror.com/file")


if __name__ == "__main__":
    unittest.main()
