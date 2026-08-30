"""Unit tests for yt-dlp Reference Backend Adapter, Media Models, and Inspector (Epic E08)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shusha.backends.errors import (
    BackendConnectionError,
    BackendExecutionError,
    BackendJobNotFoundError,
    BackendTimeoutError,
)
from shusha.backends.options import OptionType
from shusha.backends.ytdlp import (
    MediaInspector,
    MediaMetadata,
    YtDlpAdapter,
    YtDlpBackend,
)
from shusha.domain.capability import Capability
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState
from shusha.domain.values import ByteSize, Duration

SAMPLE_YTDLP_JSON = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "extractor": "youtube",
    "extractor_key": "Youtube",
    "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "duration": 213,
    "uploader": "RickAstleyVEVO",
    "uploader_id": "RickAstleyVEVO",
    "uploader_url": "https://www.youtube.com/user/RickAstleyVEVO",
    "upload_date": "20091025",
    "description": "The official video for Never Gonna Give You Up",
    "view_count": 1500000000,
    "like_count": 16000000,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "thumbnails": [
        {
            "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            "id": "hqdefault",
            "width": 480,
            "height": 360,
            "resolution": "480x360",
        },
        {
            "url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "id": "maxresdefault",
            "width": 1920,
            "height": 1080,
            "resolution": "1920x1080",
        },
    ],
    "formats": [
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "filesize": 3450000,
            "abr": 128.0,
            "asr": 44100,
            "format_note": "medium",
        },
        {
            "format_id": "137",
            "ext": "mp4",
            "resolution": "1920x1080",
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "vcodec": "avc1.640028",
            "acodec": "none",
            "filesize": 45000000,
            "tbr": 4000.0,
            "vbr": 3900.0,
            "format_note": "1080p",
        },
        {
            "format_id": "22",
            "ext": "mp4",
            "resolution": "1280x720",
            "width": 1280,
            "height": 720,
            "fps": 30.0,
            "vcodec": "avc1.64001F",
            "acodec": "mp4a.40.2",
            "filesize": 25000000,
            "tbr": 2000.0,
            "format_note": "720p",
        },
    ],
    "subtitles": {
        "en": [
            {
                "ext": "vtt",
                "url": "https://example.com/en.vtt",
                "name": "English",
            }
        ]
    },
    "automatic_captions": {
        "es": [
            {
                "ext": "vtt",
                "url": "https://example.com/es.vtt",
                "name": "Spanish (auto)",
            }
        ]
    },
    "chapters": [
        {
            "title": "Intro",
            "start_time": 0.0,
            "end_time": 18.0,
        },
        {
            "title": "Verse 1",
            "start_time": 18.0,
            "end_time": 45.0,
        },
    ],
}


class TestYtDlpAdapter:
    """Tests for YtDlpAdapter process runner (E08-I01)."""

    def test_adapter_discovery_and_version(self) -> None:
        adapter = YtDlpAdapter(executable="/usr/bin/yt-dlp", default_timeout=30.0)
        assert adapter.executable == "/usr/bin/yt-dlp"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["/usr/bin/yt-dlp", "--version"],
                returncode=0,
                stdout="2025.02.15\n",
                stderr="",
            )
            assert adapter.check_available() is True
            assert adapter.get_version() == "2025.02.15"

    def test_check_available_handles_missing_binary(self) -> None:
        adapter = YtDlpAdapter(executable="nonexistent-binary-yt-dlp")
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert adapter.check_available() is False
            assert adapter.get_version() == "unknown"

    def test_extract_info_builds_safe_command_with_delimiter(self) -> None:
        adapter = YtDlpAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(SAMPLE_YTDLP_JSON),
                stderr="",
            )
            res = adapter.extract_info("https://example.com/video")
            assert res["id"] == "dQw4w9WgXcQ"

            mock_run.assert_called_once()
            called_cmd = mock_run.call_args[0][0]
            # Must contain --dump-json, --no-warnings, --no-download
            assert "--dump-json" in called_cmd
            assert "--no-warnings" in called_cmd
            assert "--no-download" in called_cmd
            # Must place "--" right before the URL to prevent option injection
            assert called_cmd[-2] == "--"
            assert called_cmd[-1] == "https://example.com/video"

    def test_extract_info_flat_playlist(self) -> None:
        adapter = YtDlpAdapter()
        line1 = json.dumps({"id": "v1", "title": "Vid 1", "playlist_id": "pl1"})
        line2 = json.dumps({"id": "v2", "title": "Vid 2", "playlist_id": "pl1"})

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=f"{line1}\n{line2}\n",
                stderr="",
            )
            res = adapter.extract_info(
                "https://example.com/playlist", flat_playlist=True
            )
            assert res["_type"] == "playlist"
            assert len(res["entries"]) == 2
            assert res["entries"][0]["id"] == "v1"
            assert res["entries"][1]["id"] == "v2"

    def test_extract_info_error_handling(self) -> None:
        adapter = YtDlpAdapter()

        # 1. Empty URL
        with pytest.raises(BackendExecutionError, match="cannot be empty"):
            adapter.extract_info("   ")

        # 2. Timeout
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="yt-dlp", timeout=10),
            ),
            pytest.raises(BackendTimeoutError, match="timed out"),
        ):
            adapter.extract_info("https://example.com/video", timeout=10)

        # 3. Executable not found
        with (
            patch("subprocess.run", side_effect=FileNotFoundError),
            pytest.raises(BackendConnectionError, match="not found"),
        ):
            adapter.extract_info("https://example.com/video")

        # 4. Exit code != 0
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="ERROR: Video unavailable",
            )
            with pytest.raises(BackendExecutionError, match="Video unavailable"):
                adapter.extract_info("https://example.com/video")

    def test_build_download_args(self) -> None:
        adapter = YtDlpAdapter()
        cmd = adapter.build_download_args(
            "https://example.com/video",
            output_dir=Path("/downloads"),
            format_id="bestvideo[height<=1080]+bestaudio",
            extract_audio=True,
            audio_format="mp3",
            audio_quality="320k",
            write_subtitles=True,
            subtitle_langs=["en", "es"],
            write_thumbnail=True,
            embed_thumbnail=True,
            embed_metadata=True,
            rate_limit="2M",
        )
        assert cmd[0] == "yt-dlp"
        assert "-P" in cmd
        assert "/downloads" in cmd
        assert "-f" in cmd
        assert "bestvideo[height<=1080]+bestaudio" in cmd
        assert "-x" in cmd
        assert "--audio-format" in cmd
        assert "mp3" in cmd
        assert "--audio-quality" in cmd
        assert "320k" in cmd
        assert "--write-subs" in cmd
        assert "--sub-langs" in cmd
        assert "en,es" in cmd
        assert "--write-thumbnail" in cmd
        assert "--embed-thumbnail" in cmd
        assert "--embed-metadata" in cmd
        assert "-r" in cmd
        assert "2M" in cmd
        assert cmd[-2] == "--"
        assert cmd[-1] == "https://example.com/video"


class TestMediaInspector:
    """Tests for MediaInspector metadata queries (E08-I02)."""

    def test_inspect_and_parse_full_metadata(self) -> None:
        mock_adapter = MagicMock(spec=YtDlpAdapter)
        mock_adapter.extract_info.return_value = SAMPLE_YTDLP_JSON

        inspector = MediaInspector(adapter=mock_adapter)
        meta = inspector.inspect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert isinstance(meta, MediaMetadata)
        assert meta.id == "dQw4w9WgXcQ"
        assert meta.title == "Rick Astley - Never Gonna Give You Up"
        assert meta.extractor == "youtube"
        assert meta.duration == Duration(213)
        assert meta.duration_seconds == 213.0
        assert meta.uploader == "RickAstleyVEVO"
        assert meta.view_count == 1500000000
        assert meta.like_count == 16000000
        assert len(meta.thumbnails) == 2
        assert meta.thumbnails[1].resolution == "1920x1080"

        # Formats
        assert len(meta.formats) == 3
        f_audio = meta.formats[0]
        assert f_audio.format_id == "140"
        assert f_audio.is_audio_only is True
        assert f_audio.is_video is False
        assert f_audio.filesize == ByteSize(3450000)

        f_video = meta.formats[1]
        assert f_video.format_id == "137"
        assert f_video.is_video_only is True
        assert f_video.is_video is True
        assert f_video.resolution == "1920x1080"
        assert f_video.fps == 30.0

        f_muxed = meta.formats[2]
        assert f_muxed.format_id == "22"
        assert f_muxed.is_video is True
        assert f_muxed.is_audio_only is False
        assert f_muxed.is_video_only is False

        # Subtitles
        assert "en" in meta.subtitles
        assert meta.subtitles["en"][0].is_auto_generated is False
        assert "es" in meta.subtitles
        assert meta.subtitles["es"][0].is_auto_generated is True

        # Chapters
        assert len(meta.chapters) == 2
        assert meta.chapters[0].title == "Intro"
        assert meta.chapters[0].start_time == 0.0
        assert meta.chapters[0].end_time == 18.0

    def test_inspect_playlist_metadata(self) -> None:
        mock_adapter = MagicMock(spec=YtDlpAdapter)
        mock_adapter.extract_info.return_value = {
            "_type": "playlist",
            "id": "PLrEnWoR732-DN6gmmsn0kEvf9v8t6s1",
            "title": "Music Playlist",
            "entries": [
                {"id": "s1", "title": "Song 1"},
                {"id": "s2", "title": "Song 2"},
                {"id": "s3", "title": "Song 3"},
            ],
        }

        inspector = MediaInspector(adapter=mock_adapter)
        meta = inspector.inspect("https://example.com/playlist", flat_playlist=True)

        assert meta.is_playlist is True
        assert meta.playlist_count == 3
        assert meta.playlist_id == "PLrEnWoR732-DN6gmmsn0kEvf9v8t6s1"
        assert meta.playlist_title == "Music Playlist"


class TestYtDlpBackendAdapter:
    """Tests for YtDlpBackend implementation (E08-I03, E08-I04, E08-I05)."""

    @pytest.fixture
    def mock_adapter(self) -> MagicMock:
        adapter = MagicMock(spec=YtDlpAdapter)
        adapter.check_available.return_value = True
        adapter.get_version.return_value = "2025.01.01"
        adapter.executable = "yt-dlp"
        return adapter

    def test_backend_identity_and_capabilities(self, mock_adapter: MagicMock) -> None:
        backend = YtDlpBackend(adapter=mock_adapter)
        assert backend.identity.id == "ytdlp"
        assert backend.identity.name == "yt-dlp Media Backend"
        assert backend.identity.version == "2025.01.01"

        caps = backend.capabilities
        assert caps.has(Capability.MEDIA_EXTRACTION)
        assert caps.has(Capability.FORMAT_SELECTION)
        assert caps.has(Capability.PLAYLIST)
        assert caps.has(Capability.SUBTITLES)
        assert caps.has(Capability.METADATA)
        assert caps.has(Capability.POST_PROCESSING)
        assert caps.has(Capability.HTTP)
        assert caps.has(Capability.HTTPS)
        assert caps.has(Capability.BASIC_DOWNLOAD)
        assert caps.has(Capability.CANCEL)

        assert backend.ping() is True

    def test_job_submission_and_lifecycle(self, mock_adapter: MagicMock) -> None:
        backend = YtDlpBackend(adapter=mock_adapter)
        backend.initialize()

        job = Job(
            id=make_job_id("job-yt-1"),
            backend_id=backend.identity.id,
            name="Rick Astley Video",
            source=DownloadSource.from_str(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ),
            metadata={"format": "137+140"},
        )

        submitted = backend.submit_job(job)
        assert submitted.state == DownloadState.ACTIVE
        assert submitted.backend_data["selected_format"] == "137+140"
        assert submitted.backend_data["backend_engine"] == "ytdlp"

        # Status
        status = backend.get_job_status(job.id)
        assert status.id == job.id
        assert status.state == DownloadState.ACTIVE

        # Pause
        paused = backend.pause_job(job.id)
        assert paused.state == DownloadState.PAUSED

        # Resume
        resumed = backend.resume_job(job.id)
        assert resumed.state == DownloadState.ACTIVE

        # Cancel
        cancelled = backend.cancel_job(job.id)
        assert cancelled.state == DownloadState.REMOVED

        # Remove
        backend.remove_job(job.id)
        with pytest.raises(BackendJobNotFoundError):
            backend.get_job_status(job.id)

    def test_get_diagnostics(self, mock_adapter: MagicMock) -> None:
        backend = YtDlpBackend(adapter=mock_adapter)
        backend.initialize()

        diag = backend.get_diagnostics()
        assert diag.healthy is True
        assert diag.active_jobs == 0
        assert diag.details["executable"] == "yt-dlp"
        assert diag.details["version"] == "2025.01.01"

    def test_supported_options_catalogue(self, mock_adapter: MagicMock) -> None:
        backend = YtDlpBackend(adapter=mock_adapter)
        options = backend.get_supported_options()

        opt_map = {o.name: o for o in options}
        assert "format" in opt_map
        assert "audio-format" in opt_map
        assert opt_map["audio-format"].option_type == OptionType.CHOICE
        assert "mp3" in (opt_map["audio-format"].allowed_values or ())

        assert "extract-audio" in opt_map
        assert opt_map["extract-audio"].option_type == OptionType.BOOL

        assert "write-subs" in opt_map
        assert "embed-metadata" in opt_map
        assert "output-template" in opt_map
