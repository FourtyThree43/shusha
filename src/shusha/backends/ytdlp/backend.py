"""Authoritative yt-dlp reference backend adapter (Epic E08-I01..I05)."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from shusha.backends.contract import (
    BackendDiagnostics,
    BackendIdentity,
    BackendProtocol,
)
from shusha.backends.errors import (
    BackendJobNotFoundError,
)
from shusha.backends.options import (
    BackendOptionSpec,
    OptionMutability,
    OptionScope,
    OptionType,
)
from shusha.backends.ytdlp.adapter import YtDlpAdapter
from shusha.backends.ytdlp.inspector import MediaInspector
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.identifiers import (
    BackendId,
    JobId,
    make_backend_id,
)
from shusha.domain.job import Job
from shusha.domain.states import DownloadState

logger = logging.getLogger(__name__)

YTDLP_CAPABILITIES = CapabilitySet.from_iterable(
    [
        Capability.MEDIA_EXTRACTION,
        Capability.FORMAT_SELECTION,
        Capability.PLAYLIST,
        Capability.SUBTITLES,
        Capability.METADATA,
        Capability.POST_PROCESSING,
        Capability.HTTP,
        Capability.HTTPS,
        Capability.BASIC_DOWNLOAD,
        Capability.CANCEL,
    ]
)


class YtDlpBackend(BackendProtocol):
    """Full-featured backend adapter for yt-dlp media extraction and downloads."""

    def __init__(
        self,
        adapter: YtDlpAdapter | None = None,
        inspector: MediaInspector | None = None,
        backend_id: str = "ytdlp",
    ) -> None:
        self._adapter = adapter or YtDlpAdapter()
        self._inspector = inspector or MediaInspector(adapter=self._adapter)
        self._backend_id: BackendId = make_backend_id(backend_id)
        self._jobs: dict[JobId, Job] = {}
        self._initialized = False

    @property
    def identity(self) -> BackendIdentity:
        """Return backend identity descriptor."""
        ver = self._adapter.get_version()
        return BackendIdentity(
            id=self._backend_id,
            name="yt-dlp Media Backend",
            version=ver if ver != "unknown" else "2025.01.01",
            description="Media acquisition and extraction engine for audio, video, and streaming platforms",
            vendor="yt-dlp project",
        )

    @property
    def capabilities(self) -> CapabilitySet:
        """Return supported capabilities."""
        return YTDLP_CAPABILITIES

    @property
    def inspector(self) -> MediaInspector:
        """Access the media inspector component."""
        return self._inspector

    @property
    def adapter(self) -> YtDlpAdapter:
        """Access the subprocess adapter component."""
        return self._adapter

    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize adapter configuration and verify environment."""
        if config:
            exec_path = config.get("executable") or config.get("executable_path")
            timeout = config.get("timeout")
            if exec_path:
                self._adapter = YtDlpAdapter(
                    executable=str(exec_path),
                    default_timeout=float(timeout) if timeout else 60.0,
                )
                self._inspector = MediaInspector(adapter=self._adapter)
        self._initialized = True

    def shutdown(self) -> None:
        """Gracefully release background resources and cancel running operations."""
        self._initialized = False

    def ping(self) -> bool:
        """Verify that the yt-dlp binary is accessible and executable."""
        return self._adapter.check_available()

    def submit_job(self, job: Job) -> Job:
        """Enqueue and transition a media download job to ACTIVE state."""
        source_url = (
            job.source.uri.raw_uri
            if job.source
            else (job.request.raw_input if job.request else "")
        )

        backend_data = dict(job.backend_data)
        backend_data["backend_engine"] = "ytdlp"
        if source_url:
            backend_data["target_url"] = source_url

        if "format" in job.metadata:
            backend_data["selected_format"] = job.metadata["format"]

        updated = job.transition_to(DownloadState.ACTIVE)
        updated = replace(
            updated,
            backend_data=backend_data,
        )
        self._jobs[job.id] = updated
        return updated

    def pause_job(self, job_id: JobId) -> Job:
        """Pause a job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.PAUSED)
        self._jobs[job_id] = updated
        return updated

    def resume_job(self, job_id: JobId) -> Job:
        """Resume a paused job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.ACTIVE)
        self._jobs[job_id] = updated
        return updated

    def cancel_job(self, job_id: JobId) -> Job:
        """Cancel an ongoing job."""
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.REMOVED)
        self._jobs[job_id] = updated
        return updated

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        """Remove a job from tracking."""
        if job_id not in self._jobs:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
        del self._jobs[job_id]

    def get_job_status(self, job_id: JobId) -> Job:
        """Retrieve current tracked status for a Job."""
        if job_id not in self._jobs:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
        return self._jobs[job_id]

    def get_diagnostics(self) -> BackendDiagnostics:
        """Return diagnostic health snapshot and runtime metrics."""
        is_healthy = self.ping()
        active_count = sum(1 for j in self._jobs.values() if j.is_active)
        return BackendDiagnostics(
            healthy=is_healthy,
            active_jobs=active_count,
            details={
                "executable": self._adapter.executable,
                "version": self._adapter.get_version(),
                "active_jobs": str(active_count),
                "total_jobs": str(len(self._jobs)),
            },
        )

    def get_supported_options(self) -> list[BackendOptionSpec]:
        """Return the supported option specifications for yt-dlp backend."""
        return [
            BackendOptionSpec(
                name="format",
                short_name="f",
                option_type=OptionType.STRING,
                default_value="bestvideo+bestaudio/best",
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Video/audio format selection selector (e.g. 'bestvideo+bestaudio/best')",
            ),
            BackendOptionSpec(
                name="extract-audio",
                short_name="x",
                option_type=OptionType.BOOL,
                default_value=False,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Convert video files to audio-only",
            ),
            BackendOptionSpec(
                name="audio-format",
                option_type=OptionType.CHOICE,
                default_value="mp3",
                allowed_values=(
                    "mp3",
                    "aac",
                    "flac",
                    "m4a",
                    "opus",
                    "vorbis",
                    "wav",
                ),
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Target format when audio extraction is enabled",
            ),
            BackendOptionSpec(
                name="audio-quality",
                option_type=OptionType.CHOICE,
                default_value="0",
                allowed_values=(
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "128k",
                    "192k",
                    "256k",
                    "320k",
                ),
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Audio quality bit rate or VBR quality level",
            ),
            BackendOptionSpec(
                name="write-subs",
                option_type=OptionType.BOOL,
                default_value=False,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Download subtitle files alongside the video",
            ),
            BackendOptionSpec(
                name="sub-langs",
                option_type=OptionType.STRING,
                default_value="all",
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Languages of subtitles to download (comma-separated or regex)",
            ),
            BackendOptionSpec(
                name="write-thumbnail",
                option_type=OptionType.BOOL,
                default_value=False,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Download and write thumbnail image to disk",
            ),
            BackendOptionSpec(
                name="embed-thumbnail",
                option_type=OptionType.BOOL,
                default_value=False,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Embed thumbnail in the audio/video file as cover art",
            ),
            BackendOptionSpec(
                name="embed-subs",
                option_type=OptionType.BOOL,
                default_value=False,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Embed subtitles into the output video container",
            ),
            BackendOptionSpec(
                name="embed-metadata",
                option_type=OptionType.BOOL,
                default_value=True,
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Embed metadata like title, artist, and chapter markers into file",
            ),
            BackendOptionSpec(
                name="download-archive",
                option_type=OptionType.PATH,
                default_value=None,
                scope=OptionScope.BOTH,
                mutability=OptionMutability.STATIC,
                description="Path to record file containing downloaded video IDs to prevent re-downloads",
            ),
            BackendOptionSpec(
                name="output-template",
                short_name="o",
                option_type=OptionType.STRING,
                default_value="%(title)s.%(ext)s",
                scope=OptionScope.JOB,
                mutability=OptionMutability.STATIC,
                description="Output filename template specification",
            ),
            BackendOptionSpec(
                name="rate-limit",
                short_name="r",
                option_type=OptionType.STRING,
                default_value=None,
                scope=OptionScope.BOTH,
                mutability=OptionMutability.STATIC,
                description="Maximum download rate cap (e.g. '500K' or '2.5M')",
            ),
        ]
