"""Media inspection engine querying yt-dlp metadata without downloading (Epic E08-I02)."""

from __future__ import annotations

import logging
from typing import Any

from shusha.backends.ytdlp.adapter import YtDlpAdapter
from shusha.backends.ytdlp.media import (
    MediaChapter,
    MediaFormat,
    MediaMetadata,
    MediaSubtitle,
    MediaThumbnail,
)
from shusha.domain.values import ByteSize, Duration

logger = logging.getLogger(__name__)


class MediaInspector:
    """High-level inspector for media streaming URLs and playlists."""

    def __init__(self, adapter: YtDlpAdapter | None = None) -> None:
        self._adapter = adapter or YtDlpAdapter()

    @property
    def adapter(self) -> YtDlpAdapter:
        """Underlying subprocess adapter."""
        return self._adapter

    def inspect(
        self,
        url: str,
        *,
        flat_playlist: bool = False,
        timeout: float | None = None,
    ) -> MediaMetadata:
        """Inspect media URL and return strongly typed MediaMetadata domain model."""
        raw_data = self._adapter.extract_info(
            url, flat_playlist=flat_playlist, timeout=timeout
        )
        return self.parse_metadata(raw_data, original_url=url)

    def parse_metadata(
        self, data: dict[str, Any], original_url: str = ""
    ) -> MediaMetadata:
        """Convert raw yt-dlp JSON dictionary to typed MediaMetadata aggregate."""
        is_playlist = data.get("_type") == "playlist" or "entries" in data
        entries = data.get("entries")

        media_id = str(data.get("id") or "")
        title = str(data.get("title") or ("Playlist" if is_playlist else "Untitled"))
        extractor = str(data.get("extractor") or "")
        extractor_key = data.get("extractor_key")
        webpage_url = data.get("webpage_url") or original_url or None

        duration_sec: float | None = None
        raw_duration = data.get("duration")
        if raw_duration is not None:
            try:
                duration_sec = float(raw_duration)
            except ValueError, TypeError:
                duration_sec = None

        duration: Duration | None = None
        if duration_sec is not None and duration_sec >= 0:
            duration = Duration(int(duration_sec))

        uploader = data.get("uploader")
        uploader_id = data.get("uploader_id")
        uploader_url = data.get("uploader_url")
        upload_date = data.get("upload_date")
        description = data.get("description")

        view_count: int | None = None
        if data.get("view_count") is not None:
            try:
                view_count = int(data["view_count"])
            except ValueError, TypeError:
                view_count = None

        like_count: int | None = None
        if data.get("like_count") is not None:
            try:
                like_count = int(data["like_count"])
            except ValueError, TypeError:
                like_count = None

        thumbnail = data.get("thumbnail")

        # 1. Parse Thumbnails
        thumbnails: list[MediaThumbnail] = []
        for t in data.get("thumbnails", []):
            if isinstance(t, dict) and t.get("url"):
                thumbnails.append(
                    MediaThumbnail(
                        url=str(t["url"]),
                        id=str(t["id"]) if t.get("id") else None,
                        width=int(t["width"]) if t.get("width") else None,
                        height=int(t["height"]) if t.get("height") else None,
                        resolution=str(t["resolution"])
                        if t.get("resolution")
                        else None,
                    )
                )

        # 2. Parse Formats
        formats: list[MediaFormat] = []
        for f in data.get("formats", []):
            if not isinstance(f, dict):
                continue
            fmt_id = str(f.get("format_id") or "")
            if not fmt_id:
                continue

            width = int(f["width"]) if f.get("width") else None
            height = int(f["height"]) if f.get("height") else None
            res_str = (
                str(f["resolution"])
                if f.get("resolution")
                else (f"{width}x{height}" if width and height else None)
            )

            fps: float | None = None
            if f.get("fps") is not None:
                try:
                    fps = float(f["fps"])
                except ValueError, TypeError:
                    fps = None

            filesize: ByteSize | None = None
            f_size = f.get("filesize") or f.get("filesize_approx")
            if f_size is not None:
                try:
                    size_int = int(f_size)
                    if size_int >= 0:
                        filesize = ByteSize(size_int)
                except ValueError, TypeError:
                    filesize = None

            tbr: float | None = None
            if f.get("tbr") is not None:
                try:
                    tbr = float(f["tbr"])
                except ValueError, TypeError:
                    tbr = None

            vbr: float | None = None
            if f.get("vbr") is not None:
                try:
                    vbr = float(f["vbr"])
                except ValueError, TypeError:
                    vbr = None

            abr: float | None = None
            if f.get("abr") is not None:
                try:
                    abr = float(f["abr"])
                except ValueError, TypeError:
                    abr = None

            asr: int | None = None
            if f.get("asr") is not None:
                try:
                    asr = int(f["asr"])
                except ValueError, TypeError:
                    asr = None

            formats.append(
                MediaFormat(
                    format_id=fmt_id,
                    ext=str(f.get("ext") or "mp4"),
                    resolution=res_str,
                    width=width,
                    height=height,
                    fps=fps,
                    vcodec=str(f["vcodec"]) if f.get("vcodec") else None,
                    acodec=str(f["acodec"]) if f.get("acodec") else None,
                    filesize=filesize,
                    tbr=tbr,
                    vbr=vbr,
                    abr=abr,
                    asr=asr,
                    format_note=str(f["format_note"]) if f.get("format_note") else None,
                    container=str(f["container"]) if f.get("container") else None,
                    url=str(f["url"]) if f.get("url") else None,
                )
            )

        # 3. Parse Subtitles & Captions
        subtitles_map: dict[str, list[MediaSubtitle]] = {}
        for lang, tracks in data.get("subtitles", {}).items():
            if isinstance(tracks, list):
                sub_list: list[MediaSubtitle] = []
                for trk in tracks:
                    if isinstance(trk, dict):
                        sub_list.append(
                            MediaSubtitle(
                                language=str(lang),
                                ext=str(trk.get("ext") or "vtt"),
                                url=str(trk["url"]) if trk.get("url") else None,
                                name=str(trk["name"]) if trk.get("name") else None,
                                is_auto_generated=False,
                            )
                        )
                if sub_list:
                    subtitles_map[str(lang)] = sub_list

        for lang, tracks in data.get("automatic_captions", {}).items():
            if isinstance(tracks, list):
                auto_list = subtitles_map.setdefault(str(lang), [])
                for trk in tracks:
                    if isinstance(trk, dict):
                        auto_list.append(
                            MediaSubtitle(
                                language=str(lang),
                                ext=str(trk.get("ext") or "vtt"),
                                url=str(trk["url"]) if trk.get("url") else None,
                                name=str(trk["name"]) if trk.get("name") else None,
                                is_auto_generated=True,
                            )
                        )

        # 4. Parse Chapters
        chapters: list[MediaChapter] = []
        for c in data.get("chapters", []):
            if isinstance(c, dict):
                try:
                    chapters.append(
                        MediaChapter(
                            title=str(c.get("title") or ""),
                            start_time=float(c.get("start_time") or 0.0),
                            end_time=float(c.get("end_time") or 0.0),
                        )
                    )
                except ValueError, TypeError:
                    continue

        playlist_count: int | None = None
        if isinstance(entries, list):
            playlist_count = len(entries)
        elif data.get("playlist_count") is not None:
            try:
                playlist_count = int(data["playlist_count"])
            except ValueError, TypeError:
                playlist_count = None

        playlist_id = str(data.get("playlist_id") or media_id) if is_playlist else None
        playlist_title = (
            str(data.get("playlist_title") or title) if is_playlist else None
        )

        # 5. Extract string-safe metadata map
        raw_meta: dict[str, str] = {}
        for k in ("extractor", "webpage_url", "uploader", "upload_date", "view_count"):
            if k in data and data[k] is not None:
                raw_meta[k] = str(data[k])

        return MediaMetadata(
            id=media_id,
            title=title,
            extractor=extractor,
            extractor_key=str(extractor_key) if extractor_key else None,
            webpage_url=webpage_url,
            duration=duration,
            duration_seconds=duration_sec,
            uploader=str(uploader) if uploader else None,
            uploader_id=str(uploader_id) if uploader_id else None,
            uploader_url=str(uploader_url) if uploader_url else None,
            upload_date=str(upload_date) if upload_date else None,
            description=str(description) if description else None,
            view_count=view_count,
            like_count=like_count,
            thumbnail=str(thumbnail) if thumbnail else None,
            thumbnails=thumbnails,
            formats=formats,
            subtitles=subtitles_map,
            chapters=chapters,
            is_playlist=is_playlist,
            playlist_count=playlist_count,
            playlist_id=playlist_id,
            playlist_title=playlist_title,
            raw_data=raw_meta,
        )
