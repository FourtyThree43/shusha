import tempfile
import unittest
from pathlib import Path

from shusha.models.torrent_creator import TorrentCreator, bencode


class TestTorrentCreator(unittest.TestCase):
    def test_bencode_primitives(self):
        self.assertEqual(bencode(42), b"i42e")
        self.assertEqual(bencode("hello"), b"5:hello")
        self.assertEqual(bencode(b"world"), b"5:world")
        self.assertEqual(bencode(["a", 1]), b"l1:ai1ee")
        self.assertEqual(bencode({"key": "value"}), b"d3:key5:valuee")

    def test_create_single_file_torrent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "test_data.bin"
            sample_file.write_bytes(b"A" * 1024 * 600)  # 600 KiB

            out_torrent, magnet_uri = TorrentCreator.create_torrent_file(
                target_path=sample_file,
                piece_length=256 * 1024,
                trackers=["http://tracker.example.com/announce"],
                comment="Unit test torrent",
            )

            self.assertTrue(out_torrent.exists())
            self.assertTrue(out_torrent.name.endswith(".torrent"))
            self.assertTrue(magnet_uri.startswith("magnet:?xt=urn:btih:"))
            self.assertIn("dn=test_data.bin", magnet_uri)
            self.assertIn("tr=http%3A//tracker.example.com/announce", magnet_uri)

    def test_create_multi_file_directory_torrent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_dir = Path(tmpdir) / "album"
            sample_dir.mkdir(parents=True, exist_ok=True)
            (sample_dir / "track1.mp3").write_bytes(b"12345" * 1000)
            (sample_dir / "track2.mp3").write_bytes(b"67890" * 1000)

            out_torrent, magnet_uri = TorrentCreator.create_torrent_file(
                target_path=sample_dir,
                piece_length=512 * 1024,
                trackers=["http://tracker.example.com/announce"],
            )

            self.assertTrue(out_torrent.exists())
            self.assertTrue(magnet_uri.startswith("magnet:?xt=urn:btih:"))
            self.assertIn("dn=album", magnet_uri)


if __name__ == "__main__":
    unittest.main()
