import unittest

from shusha.models.batch_parser import (
    expand_pattern_url,
    extract_urls,
    is_downloadable_url,
)


class TestBatchParser(unittest.TestCase):
    def test_extract_urls_simple(self):
        text = """
        Check out these files:
        https://example.com/file1.zip
        http://example.org/image.iso
        """
        urls = extract_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.com/file1.zip", urls)
        self.assertIn("http://example.org/image.iso", urls)

    def test_extract_magnet_links(self):
        magnet = "magnet:?xt=urn:btih:3b245504d603a1a6b0805342c3cd3ef10f9b6e23&dn=Ubuntu"
        text = f"Download link: {magnet}"
        urls = extract_urls(text)
        self.assertEqual(urls, [magnet])

    def test_numeric_range_expansion(self):
        pattern = "http://example.com/archive_part[01-04].rar"
        expanded = expand_pattern_url(pattern)
        self.assertEqual(len(expanded), 4)
        self.assertEqual(expanded[0], "http://example.com/archive_part01.rar")
        self.assertEqual(expanded[1], "http://example.com/archive_part02.rar")
        self.assertEqual(expanded[2], "http://example.com/archive_part03.rar")
        self.assertEqual(expanded[3], "http://example.com/archive_part04.rar")

    def test_alpha_range_expansion(self):
        pattern = "http://example.com/img_[a-c].png"
        expanded = expand_pattern_url(pattern)
        self.assertEqual(
            expanded,
            [
                "http://example.com/img_a.png",
                "http://example.com/img_b.png",
                "http://example.com/img_c.png",
            ],
        )

    def test_nested_range_expansion(self):
        pattern = "http://example.com/[1-2]/[a-b].zip"
        expanded = expand_pattern_url(pattern)
        self.assertEqual(len(expanded), 4)
        self.assertIn("http://example.com/1/a.zip", expanded)
        self.assertIn("http://example.com/1/b.zip", expanded)
        self.assertIn("http://example.com/2/a.zip", expanded)
        self.assertIn("http://example.com/2/b.zip", expanded)

    def test_is_downloadable_url(self):
        self.assertTrue(is_downloadable_url("https://example.com/file.zip"))
        self.assertTrue(is_downloadable_url("ftp://server.org/data.tar"))
        self.assertTrue(is_downloadable_url("magnet:?xt=urn:btih:12345"))
        self.assertFalse(is_downloadable_url("not a url"))
        self.assertFalse(is_downloadable_url("javascript:alert(1)"))
