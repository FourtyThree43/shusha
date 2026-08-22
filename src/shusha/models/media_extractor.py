"""Media playlist and HLS / M3U8 stream parser for Shusha-DM.

Parses M3U8 master playlists, media manifests, and extracts stream resolutions,
bandwidth rates, audio channels, and segment chunk sequences.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


@dataclass
class StreamQuality:
    """Represents an available media stream variant in an M3U8 master playlist."""

    bandwidth: int
    resolution: str  # e.g. "1920x1080"
    codecs: str
    url: str
    name: str = ""

    @property
    def resolution_label(self) -> str:
        if self.resolution:
            height = self.resolution.split("x")[-1]
            return f"{height}p ({self.resolution})"
        return f"{self.bandwidth // 1000} kbps"


class MediaExtractor:
    """Extracts stream variants and segment chunks from M3U8 / HLS manifests."""

    STREAM_INF_REGEX = re.compile(
        r"#EXT-X-STREAM-INF:([^\n]+)\n([^\n]+)",
        re.MULTILINE,
    )
    ATTR_REGEX = re.compile(r'([A-Z0-9\-]+)=(?:(?:"([^"]*)")|([^,]+))')

    @classmethod
    def is_m3u8(cls, url_or_content: str) -> bool:
        """Check if URL or content is an M3U8 playlist."""
        if not url_or_content:
            return False
        clean = url_or_content.strip()
        if clean.startswith("#EXTM3U"):
            return True
        path = clean.split("?")[0].lower()
        return path.endswith(".m3u8")

    @classmethod
    def parse_master_playlist(
        cls,
        playlist_content: str,
        base_url: str = "",
    ) -> list[StreamQuality]:
        """Parse master M3U8 playlist into available stream quality variants.

        Args:
            playlist_content: Raw M3U8 text.
            base_url: Base URL to resolve relative stream links.

        Returns:
            List of StreamQuality objects sorted from highest to lowest bitrate.
        """
        variants: list[StreamQuality] = []
        matches = cls.STREAM_INF_REGEX.findall(playlist_content)

        for attr_str, stream_uri in matches:
            attrs: dict[str, str] = {}
            for k, val_quoted, val_unquoted in cls.ATTR_REGEX.findall(attr_str):
                attrs[k] = val_quoted or val_unquoted

            bandwidth = int(attrs.get("BANDWIDTH", "0"))
            resolution = attrs.get("RESOLUTION", "")
            codecs = attrs.get("CODECS", "")
            name = attrs.get("NAME", "")

            full_url = urljoin(base_url, stream_uri.strip()) if base_url else stream_uri.strip()

            variants.append(
                StreamQuality(
                    bandwidth=bandwidth,
                    resolution=resolution,
                    codecs=codecs,
                    url=full_url,
                    name=name,
                )
            )

        # Sort descending by bandwidth
        variants.sort(key=lambda s: s.bandwidth, reverse=True)
        return variants

    @classmethod
    def parse_media_segments(
        cls,
        media_playlist_content: str,
        base_url: str = "",
    ) -> list[str]:
        """Extract individual TS/AAC segment chunk URLs from media playlist.

        Args:
            media_playlist_content: Raw media playlist content.
            base_url: Base URL to resolve relative chunk paths.

        Returns:
            List of absolute or relative segment URLs.
        """
        segments: list[str] = []
        lines = media_playlist_content.strip().split("\n")

        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue
            seg_url = urljoin(base_url, trimmed) if base_url else trimmed
            segments.append(seg_url)

        return segments
