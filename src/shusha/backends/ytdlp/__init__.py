"""yt-dlp download and media extraction backend package (Epic E08)."""

from shusha.backends.ytdlp.adapter import YtDlpAdapter
from shusha.backends.ytdlp.backend import YTDLP_CAPABILITIES, YtDlpBackend
from shusha.backends.ytdlp.inspector import MediaInspector
from shusha.backends.ytdlp.media import (
    MediaChapter,
    MediaFormat,
    MediaMetadata,
    MediaSubtitle,
    MediaThumbnail,
)

__all__ = [
    "YTDLP_CAPABILITIES",
    "MediaChapter",
    "MediaFormat",
    "MediaInspector",
    "MediaMetadata",
    "MediaSubtitle",
    "MediaThumbnail",
    "YtDlpAdapter",
    "YtDlpBackend",
]
