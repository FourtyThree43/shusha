"""Common Contract Test Suite for Shusha Backends (E06-I02).

Any backend implementation (FakeBackend, Aria2Backend, YtDlpBackend) must pass this suite.
"""

from __future__ import annotations

import pytest

from shusha.backends import (
    BackendJobNotFoundError,
    BackendProtocol,
    FakeBackend,
)
from shusha.domain.identifiers import make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState


@pytest.fixture
def fake_backend() -> BackendProtocol:
    """Fixture providing an initialized FakeBackend instance."""
    backend = FakeBackend()
    backend.initialize()
    return backend


class TestBackendContract:
    """Authoritative contract validation for any BackendProtocol implementation."""

    def test_backend_identity_and_version(self, fake_backend: BackendProtocol) -> None:
        ident = fake_backend.identity
        assert ident.id != ""
        assert ident.name != ""
        assert ident.version != ""

    def test_backend_capabilities(self, fake_backend: BackendProtocol) -> None:
        caps = fake_backend.capabilities
        assert len(caps) > 0

    def test_backend_lifecycle_and_ping(self, fake_backend: BackendProtocol) -> None:
        assert fake_backend.ping() is True
        diagnostics = fake_backend.get_diagnostics()
        assert diagnostics.healthy is True

    def test_job_execution_lifecycle(self, fake_backend: BackendProtocol) -> None:
        # 1. Submit Job
        job = Job(
            id=make_job_id("test-contract-001"),
            backend_id=fake_backend.identity.id,
            name="archive.tar.gz",
        )
        submitted = fake_backend.submit_job(job)
        assert submitted.state == DownloadState.ACTIVE

        # 2. Get Status
        status = fake_backend.get_job_status(job.id)
        assert status.id == job.id
        assert status.state == DownloadState.ACTIVE

        # 3. Pause Job
        paused = fake_backend.pause_job(job.id)
        assert paused.state == DownloadState.PAUSED

        # 4. Resume Job
        resumed = fake_backend.resume_job(job.id)
        assert resumed.state == DownloadState.ACTIVE

        # 5. Cancel Job
        cancelled = fake_backend.cancel_job(job.id)
        assert cancelled.state == DownloadState.REMOVED

        # 6. Remove Job
        fake_backend.remove_job(job.id)
        with pytest.raises(BackendJobNotFoundError):
            fake_backend.get_job_status(job.id)

    def test_nonexistent_job_raises_error(self, fake_backend: BackendProtocol) -> None:
        with pytest.raises(BackendJobNotFoundError):
            fake_backend.get_job_status(make_job_id("does-not-exist"))

        with pytest.raises(BackendJobNotFoundError):
            fake_backend.pause_job(make_job_id("does-not-exist"))

    def test_supported_options_metadata(self, fake_backend: BackendProtocol) -> None:
        options = fake_backend.get_supported_options()
        assert isinstance(options, list)
        for opt in options:
            assert opt.name != ""
            assert opt.option_type is not None
