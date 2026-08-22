import unittest
from pathlib import Path

from shusha.models.category_manager import CategoryManager


class TestCategoryManager(unittest.TestCase):
    def test_get_category_by_extension(self):
        self.assertEqual(CategoryManager.get_category("movie.mp4"), "Video")
        self.assertEqual(CategoryManager.get_category("song.mp3"), "Audio")
        self.assertEqual(CategoryManager.get_category("bundle.zip"), "Archive")
        self.assertEqual(CategoryManager.get_category("document.pdf"), "Document")
        self.assertEqual(CategoryManager.get_category("installer.exe"), "Software")
        self.assertEqual(CategoryManager.get_category("photo.jpg"), "Image")
        self.assertEqual(CategoryManager.get_category("unknown.xyz"), "Other")
        self.assertEqual(CategoryManager.get_category(""), "Other")

    def test_get_category_by_url(self):
        self.assertEqual(
            CategoryManager.get_category("https://example.com/files/archive.tar.gz"),
            "Archive",
        )
        self.assertEqual(
            CategoryManager.get_category("http://media.org/stream/video.mkv?token=123"),
            "Video",
        )
        self.assertEqual(
            CategoryManager.get_category("magnet:?xt=urn:btih:abcdef"),
            "Archive",
        )

    def test_get_category_directory(self):
        base = Path("/home/user/Downloads")
        self.assertEqual(
            CategoryManager.get_category_directory(base, "Video", auto_subfolder=True),
            base / "Videos",
        )
        self.assertEqual(
            CategoryManager.get_category_directory(base, "Document", auto_subfolder=True),
            base / "Documents",
        )
        self.assertEqual(
            CategoryManager.get_category_directory(base, "Other", auto_subfolder=True),
            base,
        )
        self.assertEqual(
            CategoryManager.get_category_directory(base, "Video", auto_subfolder=False),
            base,
        )


if __name__ == "__main__":
    unittest.main()
