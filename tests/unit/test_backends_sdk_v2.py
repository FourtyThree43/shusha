"""Unit tests for Backend SDK, Registry, Error Model, and Options (Epic E05)."""

from __future__ import annotations

import pytest

from shusha.backends import (
    BackendCapabilityUnsupportedError,
    BackendDiagnostics,
    BackendIdentity,
    BackendJobNotFoundError,
    BackendOptionSpec,
    BackendOptionValidationError,
    BackendProtocol,
    BackendRegistry,
    OptionMutability,
    OptionScope,
    OptionType,
)
from shusha.domain.acquisition import (
    AcquisitionRequest,
    DetectedKind,
    SourceKind,
)
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.identifiers import (
    JobId,
    make_acquisition_id,
    make_backend_id,
    make_job_id,
)
from shusha.domain.job import Job
from shusha.domain.states import DownloadState


class DummyBackend:
    """Mock backend implementing BackendProtocol for testing."""

    def __init__(
        self,
        backend_id: str,
        name: str,
        capabilities: list[Capability | str],
    ) -> None:
        self._identity = BackendIdentity(
            id=make_backend_id(backend_id),
            name=name,
            version="1.0.0",
        )
        self._capabilities = CapabilitySet.from_iterable(capabilities)
        self._jobs: dict[JobId, Job] = {}

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    def initialize(self, config: dict | None = None) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def ping(self) -> bool:
        return True

    def submit_job(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job

    def pause_job(self, job_id: JobId) -> Job:
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.PAUSED)
        self._jobs[job_id] = updated
        return updated

    def resume_job(self, job_id: JobId) -> Job:
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.ACTIVE)
        self._jobs[job_id] = updated
        return updated

    def cancel_job(self, job_id: JobId) -> Job:
        job = self.get_job_status(job_id)
        updated = job.transition_to(DownloadState.REMOVED)
        self._jobs[job_id] = updated
        return updated

    def remove_job(self, job_id: JobId, delete_files: bool = False) -> None:
        if job_id in self._jobs:
            del self._jobs[job_id]

    def get_job_status(self, job_id: JobId) -> Job:
        if job_id not in self._jobs:
            raise BackendJobNotFoundError(job_id, backend_id=self.identity.id)
        return self._jobs[job_id]

    def get_diagnostics(self) -> BackendDiagnostics:
        return BackendDiagnostics(healthy=True, active_jobs=len(self._jobs))

    def get_supported_options(self) -> list[BackendOptionSpec]:
        return [
            BackendOptionSpec(
                name="max-connection-per-server",
                option_type=OptionType.INT,
                default_value=16,
            )
        ]


class TestBackendProtocolAndSDK:
    """Tests for BackendProtocol adherence (E05-I01)."""

    def test_dummy_backend_implements_protocol(self) -> None:
        backend = DummyBackend(
            "dummy", "Dummy Engine", [Capability.HTTP, Capability.TORRENT]
        )
        assert isinstance(backend, BackendProtocol)
        assert backend.identity.id == "dummy"
        assert backend.capabilities.has(Capability.TORRENT)
        assert backend.ping() is True


class TestBackendRegistry:
    """Tests for BackendRegistry (E05-I02)."""

    def test_register_and_select_by_capability(self) -> None:
        registry = BackendRegistry()

        b_aria2 = DummyBackend(
            "aria2",
            "aria2 engine",
            [Capability.HTTP, Capability.TORRENT, Capability.METALINK],
        )
        b_ytdlp = DummyBackend(
            "yt-dlp",
            "yt-dlp engine",
            [Capability.MEDIA_EXTRACTION, Capability.PLAYLIST],
        )

        registry.register(b_aria2, default=True)
        registry.register(b_ytdlp)

        assert registry.get(make_backend_id("aria2")) is b_aria2
        assert registry.get(make_backend_id("yt-dlp")) is b_ytdlp
        assert registry.get_default() is b_aria2

        torrent_backends = registry.find_by_capability(Capability.TORRENT)
        assert len(torrent_backends) == 1
        assert torrent_backends[0] is b_aria2

        media_backends = registry.find_by_capability(Capability.MEDIA_EXTRACTION)
        assert len(media_backends) == 1
        assert media_backends[0] is b_ytdlp

    def test_routing_acquisition_requests(self) -> None:
        registry = BackendRegistry()
        b_aria2 = DummyBackend(
            "aria2",
            "aria2 engine",
            [Capability.HTTP, Capability.TORRENT, Capability.METALINK],
        )
        b_ytdlp = DummyBackend(
            "yt-dlp",
            "yt-dlp engine",
            [Capability.MEDIA_EXTRACTION, Capability.PLAYLIST],
        )
        registry.register(b_aria2, default=True)
        registry.register(b_ytdlp)

        # 1. Magnet -> aria2
        req_magnet = AcquisitionRequest(
            id=make_acquisition_id("acq-1"),
            source_kind=SourceKind.CLIPBOARD,
            raw_input="magnet:?xt=urn:btih:123",
            detected_kind=DetectedKind.MAGNET_URI,
        )
        assert registry.select_for_request(req_magnet) is b_aria2

        # 2. Media stream -> yt-dlp
        req_media = AcquisitionRequest(
            id=make_acquisition_id("acq-2"),
            source_kind=SourceKind.BROWSER,
            raw_input="https://youtube.com/watch?v=123",
            detected_kind=DetectedKind.MEDIA_STREAM,
        )
        assert registry.select_for_request(req_media) is b_ytdlp

        # 3. Direct preference -> yt-dlp
        req_pref = AcquisitionRequest(
            id=make_acquisition_id("acq-3"),
            source_kind=SourceKind.MANUAL,
            raw_input="https://example.com/file.zip",
            preferred_backend=make_backend_id("yt-dlp"),
        )
        assert registry.select_for_request(req_pref) is b_ytdlp


class TestBackendErrorModel:
    """Tests for Backend Error hierarchy (E05-I03)."""

    def test_backend_exceptions(self) -> None:
        err = BackendJobNotFoundError(
            make_job_id("j-999"), backend_id=make_backend_id("aria2")
        )
        assert "j-999" in str(err)
        assert err.backend_id == "aria2"

        cap_err = BackendCapabilityUnsupportedError(
            "Not supported", capability="media_extraction"
        )
        assert cap_err.capability == "media_extraction"

        val_err = BackendOptionValidationError(
            "max-connections", "abc", "Must be integer"
        )
        assert val_err.option_name == "max-connections"


class TestBackendOptionModel:
    """Tests for BackendOptionSpec (E05-I04)."""

    def test_option_validation(self) -> None:
        int_spec = BackendOptionSpec(
            name="split",
            option_type=OptionType.INT,
            default_value=5,
            scope=OptionScope.JOB,
            mutability=OptionMutability.DYNAMIC,
        )
        assert int_spec.validate(10) == "10"
        assert int_spec.validate("8") == "8"
        with pytest.raises(BackendOptionValidationError):
            int_spec.validate("not_a_number")

        bool_spec = BackendOptionSpec(
            name="continue",
            option_type=OptionType.BOOL,
            default_value=True,
        )
        assert bool_spec.validate(True) == "true"
        assert bool_spec.validate("yes") == "true"
        assert bool_spec.validate(False) == "false"
        assert bool_spec.validate("0") == "false"

        choice_spec = BackendOptionSpec(
            name="file-allocation",
            option_type=OptionType.CHOICE,
            allowed_values=("none", "prealloc", "trunc", "falloc"),
        )
        assert choice_spec.validate("falloc") == "falloc"
        with pytest.raises(BackendOptionValidationError):
            choice_spec.validate("invalid_choice")
