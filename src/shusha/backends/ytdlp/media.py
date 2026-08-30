"""Backend-neutral media metadata and format domain models (Epic E08)."""

from __future__ import annotations

from dataclasses import dataclass, field

from shusha.domain.values import ByteSize, Duration


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaThumbnail:
    """Represents a thumbnail image for media content."""

    url: str
    id: str | None = None
    width: int | None = None
    height: int | None = None
    resolution: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaSubtitle:
    """Represents a subtitle / closed-caption track."""

    language: str
    ext: str = "vtt"
    url: str | None = None
    name: str | None = None
    is_auto_generated: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaChapter:
    """Represents a timed chapter marker in a media stream."""

    title: str
    start_time: float
    end_time: float


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaFormat:
    """Represents an individual audio, video, or multiplexed format stream."""

    format_id: str
    ext: str
    resolution: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    vcodec: str | None = None
    acodec: str | None = None
    filesize: ByteSize | None = None
    tbr: float | None = None
    vbr: float | None = None
    abr: float | None = None
    asr: int | None = None
    format_note: str | None = None
    container: str | None = None
    url: str | None = None

    @property
    def is_video(self) -> bool:
        """Return True if this stream contains video frames."""
        return self.vcodec is not None and self.vcodec.lower() != "none"

    @property
    def is_audio_only(self) -> bool:
        """Return True if this stream is purely audio."""
        has_audio = self.acodec is not None and self.acodec.lower() != "none"
        no_video = self.vcodec is None or self.vcodec.lower() == "none"
        return has_audio and no_video

    @property
    def is_video_only(self) -> bool:
        """Return True if this stream is video without an audio track."""
        has_video = self.vcodec is not None and self.vcodec.lower() != "none"
        no_audio = self.acodec is None or self.acodec.lower() == "none"
        return has_video and no_audio


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaMetadata:
    """Strongly typed, backend-neutral metadata container for media assets."""

    id: str
    title: str
    extractor: str = ""
    extractor_key: str | None = None
    webpage_url: str | None = None
    duration: Duration | None = None
    duration_seconds: float | None = None
    uploader: str | None = None
    uploader_id: str | None = None
    uploader_url: str | None = None
    upload_date: str | None = None
    description: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    thumbnail: str | None = None
    thumbnails: list[MediaThumbnail] = field(default_factory=list)
    formats: list[MediaFormat] = field(default_factory=list)
    subtitles: dict[str, list[MediaSubtitle]] = field(default_factory=dict)
    chapters: list[MediaChapter] = field(default_factory=list)
    is_playlist: bool = False
    playlist_count: int | None = None
    playlist_id: str | None = None
    playlist_title: str | None = None
    raw_data: dict[str, str] = field(default_factory=dict)
