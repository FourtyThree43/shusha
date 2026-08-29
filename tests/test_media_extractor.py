import unittest

from shusha.models.media_extractor import MediaExtractor


class TestMediaExtractor(unittest.TestCase):
    def test_is_m3u8(self):
        self.assertTrue(MediaExtractor.is_m3u8("https://example.com/playlist.m3u8"))
        self.assertTrue(
            MediaExtractor.is_m3u8("https://example.com/video/master.m3u8?token=xyz")
        )
        self.assertTrue(MediaExtractor.is_m3u8("#EXTM3U\n#EXT-X-VERSION:3"))
        self.assertFalse(MediaExtractor.is_m3u8("https://example.com/video.mp4"))
        self.assertFalse(MediaExtractor.is_m3u8(""))

    def test_parse_master_playlist(self):
        sample_master = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.4d401e,mp4a.40.2"
360p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=842x480,CODECS="avc1.4d401f,mp4a.40.2"
480p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2"
1080p.m3u8
"""
        streams = MediaExtractor.parse_master_playlist(
            sample_master, base_url="https://video.example.com/stream/"
        )
        self.assertEqual(len(streams), 3)

        # Sorted by bandwidth descending
        self.assertEqual(streams[0].resolution, "1920x1080")
        self.assertEqual(streams[0].url, "https://video.example.com/stream/1080p.m3u8")
        self.assertEqual(streams[0].resolution_label, "1080p (1920x1080)")

        self.assertEqual(streams[1].resolution, "842x480")
        self.assertEqual(streams[2].resolution, "640x360")

    def test_parse_media_segments(self):
        sample_media = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
segment0.ts
#EXTINF:10.0,
segment1.ts
#EXTINF:5.0,
segment2.ts
#EXT-X-ENDLIST
"""
        segments = MediaExtractor.parse_media_segments(
            sample_media, base_url="https://cdn.example.com/hls/"
        )
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0], "https://cdn.example.com/hls/segment0.ts")
        self.assertEqual(segments[1], "https://cdn.example.com/hls/segment1.ts")
        self.assertEqual(segments[2], "https://cdn.example.com/hls/segment2.ts")


if __name__ == "__main__":
    unittest.main()
