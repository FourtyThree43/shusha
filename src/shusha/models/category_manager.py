"""Download category classification and directory organization manager.

Categorizes downloads by file extension into predefined groups:
- Video (mp4, mkv, avi, mov, flv, webm, etc.)
- Audio (mp3, flac, wav, aac, ogg, m4a, etc.)
- Archive (zip, rar, 7z, tar, gz, bz2, xz, iso, etc.)
- Document (pdf, epub, doc, docx, xls, xlsx, ppt, pptx, txt, etc.)
- Software (exe, msi, dmg, pkg, deb, rpm, AppImage, apk, etc.)
- Image (jpg, jpeg, png, gif, webp, svg, bmp, etc.)
- Other (all other filetypes)
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    "Video": {
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpg",
        "mpeg", "3gp", "ts", "m2ts", "vob", "ogv",
    },
    "Audio": {
        "mp3", "flac", "wav", "aac", "ogg", "m4a", "wma", "opus", "aiff",
        "mid", "midi", "alac",
    },
    "Archive": {
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "tgz",
        "tbz2", "z", "lz", "lzma", "cab", "dmg",
    },
    "Document": {
        "pdf", "epub", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt",
        "rtf", "odt", "ods", "odp", "csv", "md", "mobi", "azw3",
    },
    "Software": {
        "exe", "msi", "pkg", "deb", "rpm", "appimage", "apk", "jar",
        "run", "bin", "sh", "bat", "cmd", "ps1",
    },
    "Image": {
        "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico",
        "tiff", "tif", "psd", "ai", "raw", "heic", "avif",
    },
}


class CategoryManager:
    """Classifies URLs and filenames into categories and resolves destination subdirectories."""

    @classmethod
    def get_category(cls, filename_or_url: str) -> str:
        """Determine category from filename or URL.

        Args:
            filename_or_url: Filename or URL string.

        Returns:
            Category name: 'Video', 'Audio', 'Archive', 'Document', 'Software', 'Image', or 'Other'.
        """
        if not filename_or_url:
            return "Other"

        clean_str = filename_or_url.strip()
        if clean_str.startswith("magnet:"):
            return "Archive"

        # If it's a URL, parse the path component
        if "://" in clean_str:
            parsed = urlparse(clean_str)
            path_str = parsed.path
        else:
            path_str = clean_str

        # Extract filename and extension
        filename = Path(path_str).name
        if not filename or "." not in filename:
            return "Other"

        ext = filename.rsplit(".", 1)[-1].lower()

        for category, extensions in CATEGORY_EXTENSIONS.items():
            if ext in extensions:
                return category

        return "Other"

    @classmethod
    def get_category_directory(
        cls,
        base_dir: str | Path,
        category: str,
        auto_subfolder: bool = True,
    ) -> Path:
        """Resolve download path for a given category.

        Args:
            base_dir: Root download directory.
            category: Category name.
            auto_subfolder: If True, appends category subfolder (e.g. ~/Downloads/Videos).

        Returns:
            Path to category destination directory.
        """
        base_path = Path(base_dir)
        if not auto_subfolder or category == "Other":
            return base_path

        category_folder_map = {
            "Video": "Videos",
            "Audio": "Audio",
            "Archive": "Archives",
            "Document": "Documents",
            "Software": "Programs",
            "Image": "Images",
        }

        folder_name = category_folder_map.get(category, category)
        target_path = base_path / folder_name
        return target_path
