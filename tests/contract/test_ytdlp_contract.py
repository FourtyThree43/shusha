"""Contract test suite validation for YtDlpBackend (Epic E08 / RULE-008 / RULE-023)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shusha.backends import (
    BackendJobNotFoundError,
    BackendProtocol,
    YtDlpBackend,
)
from shusha.backends.ytdlp.adapter import YtDlpAdapter
from shusha.domain.capability import Capability
from shusha.domain.identifiers import make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState


@pytest.fixture
def mock_ytdlp_backend() -> BackendProtocol:
    """Fixture providing an initialized YtDlpBackend with mocked subprocess adapter."""
    adapter = MagicMock(spec=YtDlpAdapter)
    adapter.check_available.return_value = True
    adapter.get_version.return_value = "2025.01.01"
    adapter.executable = "yt-dlp"

    backend = YtDlpBackend(adapter=adapter)
    backend.initialize()
    return backend


class TestYtDlpContractConformance:
    """Validate YtDlpBackend conforms strictly to the authoritative BackendProtocol."""

    def test_identity_and_version(self, mock_ytdlp_backend: BackendProtocol) -> None:
        ident = mock_ytdlp_backend.identity
        assert ident.id == "ytdlp"
        assert ident.name != ""
        assert ident.version == "2025.01.01"
        assert "yt-dlp" in ident.vendor.lower()

    def test_backend_capabilities(self, mock_ytdlp_backend: BackendProtocol) -> None:
        caps = mock_ytdlp_backend.capabilities
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

    def test_lifecycle_and_ping(self, mock_ytdlp_backend: BackendProtocol) -> None:
        assert mock_ytdlp_backend.ping() is True
        diagnostics = mock_ytdlp_backend.get_diagnostics()
        assert diagnostics.healthy is True
        assert diagnostics.active_jobs == 0
        assert "version" in diagnostics.details

    def test_job_execution_lifecycle(self, mock_ytdlp_backend: BackendProtocol) -> None:
        # 1. Submit Job
        job = Job(
            id=make_job_id("test-contract-yt-001"),
            backend_id=mock_ytdlp_backend.identity.id,
            name="Streaming Media Video",
        )
        submitted = mock_ytdlp_backend.submit_job(job)
        assert submitted.state == DownloadState.ACTIVE

        # 2. Get Status
        status = mock_ytdlp_backend.get_job_status(job.id)
        assert status.id == job.id
        assert status.state == DownloadState.ACTIVE

        # 3. Pause Job
        paused = mock_ytdlp_backend.pause_job(job.id)
        assert paused.state == DownloadState.PAUSED

        # 4. Resume Job
        resumed = mock_ytdlp_backend.resume_job(job.id)
        assert resumed.state == DownloadState.ACTIVE

        # 5. Cancel Job
        cancelled = mock_ytdlp_backend.cancel_job(job.id)
        assert cancelled.state == DownloadState.REMOVED

        # 6. Remove Job
        mock_ytdlp_backend.remove_job(job.id)
        with pytest.raises(BackendJobNotFoundError):
            mock_ytdlp_backend.get_job_status(job.id)

    def test_nonexistent_job_raises_error(
        self, mock_ytdlp_backend: BackendProtocol
    ) -> None:
        with pytest.raises(BackendJobNotFoundError):
            mock_ytdlp_backend.get_job_status(make_job_id("does-not-exist"))

        with pytest.raises(BackendJobNotFoundError):
            mock_ytdlp_backend.pause_job(make_job_id("does-not-exist"))

    def test_supported_options_metadata(
        self, mock_ytdlp_backend: BackendProtocol
    ) -> None:
        options = mock_ytdlp_backend.get_supported_options()
        assert isinstance(options, list)
        assert len(options) > 0
        for opt in options:
            assert opt.name != ""
            assert opt.option_type is not None
