"""
Unit tests for presentation dialogs, bencoding, torrent generation, and batch expansion.
"""

import tempfile
import unittest
from pathlib import Path

from shusha.presentation.views.batch_add_dialog import expand_batch_pattern
from shusha.presentation.views.create_torrent_dialog import (
    bencode,
    generate_torrent_file,
)


class TestBatchPatternExpansion(unittest.TestCase):
    def test_numeric_range_expansion(self):
        pattern = "https://example.com/archive_[01-03].zip"
        expanded = expand_batch_pattern(pattern)
        self.assertEqual(
            expanded,
            [
                "https://example.com/archive_01.zip",
                "https://example.com/archive_02.zip",
                "https://example.com/archive_03.zip",
            ],
        )

    def test_single_digit_range_expansion(self):
        pattern = "https://example.com/part[1-3].bin"
        expanded = expand_batch_pattern(pattern)
        self.assertEqual(
            expanded,
            [
                "https://example.com/part1.bin",
                "https://example.com/part2.bin",
                "https://example.com/part3.bin",
            ],
        )

    def test_alphabetical_range_expansion(self):
        pattern = "ftp://files.org/chunk_[a-c].iso"
        expanded = expand_batch_pattern(pattern)
        self.assertEqual(
            expanded,
            [
                "ftp://files.org/chunk_a.iso",
                "ftp://files.org/chunk_b.iso",
                "ftp://files.org/chunk_c.iso",
            ],
        )

    def test_no_pattern(self):
        url = "https://example.com/single.tar.gz"
        self.assertEqual(expand_batch_pattern(url), [url])


class TestTorrentCreation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bencode_primitives(self):
        # Integer
        self.assertEqual(bencode(42), b"i42e")
        self.assertEqual(bencode(-7), b"i-7e")
        self.assertEqual(bencode(0), b"i0e")

        # String / Bytes
        self.assertEqual(bencode("spam"), b"4:spam")
        self.assertEqual(bencode(b"raw"), b"3:raw")

        # List
        self.assertEqual(bencode(["spam", 42]), b"l4:spami42ee")

        # Dictionary (keys must be sorted alphabetically)
        self.assertEqual(
            bencode({"b": 2, "a": 1}),
            b"d1:ai1e1:bi2ee",
        )

    def test_generate_single_file_torrent(self):
        sample_file = Path(self.temp_dir.name) / "ubuntu-24.iso"
        # 128KB dummy content
        sample_file.write_bytes(b"A" * (128 * 1024))

        torrent_bytes = generate_torrent_file(
            source_path=sample_file,
            piece_size=32 * 1024,
            trackers=["udp://tracker.example.com:6969/announce"],
            comment="Test Ubuntu ISO",
            created_by="Shusha Unit Test",
        )

        self.assertTrue(torrent_bytes.startswith(b"d"))
        self.assertTrue(torrent_bytes.endswith(b"e"))
        self.assertIn(b"ubuntu-24.iso", torrent_bytes)
        self.assertIn(b"udp://tracker.example.com:6969/announce", torrent_bytes)

    def test_generate_directory_torrent(self):
        sample_dir = Path(self.temp_dir.name) / "album"
        sample_dir.mkdir(parents=True, exist_ok=True)
        (sample_dir / "track1.flac").write_bytes(b"1" * 65536)
        (sample_dir / "track2.flac").write_bytes(b"2" * 65536)

        torrent_bytes = generate_torrent_file(
            source_path=sample_dir,
            piece_size=32 * 1024,
            trackers=["http://tracker.music.org/announce"],
        )

        self.assertTrue(torrent_bytes.startswith(b"d"))
        self.assertIn(b"album", torrent_bytes)
        self.assertIn(b"track1.flac", torrent_bytes)
        self.assertIn(b"track2.flac", torrent_bytes)


if __name__ == "__main__":
    unittest.main()
