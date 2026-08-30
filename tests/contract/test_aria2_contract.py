"""Contract test suite validation for Aria2Backend (Epic E07)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shusha.backends.aria2 import Aria2Backend
from shusha.backends.contract import BackendProtocol
from shusha.domain.download import Download
from shusha.domain.identifiers import make_download_id, make_gid, make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState
from shusha.domain.statistics import GlobalStatistics
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.aria2.client import Aria2Client, VersionInfo


@pytest.fixture
def mock_aria2_backend() -> BackendProtocol:
    """Fixture providing an initialized Aria2Backend with mocked RPC transport."""
    client = MagicMock(spec=Aria2Client)
    client.get_version.return_value = VersionInfo(
        version="1.37.0",
        enabled_features=["BitTorrent", "GZip", "HTTPS", "MessageDigest"],
    )
    client.get_global_stat.return_value = GlobalStatistics(
        download_speed=BitRate(1_000_000),
        upload_speed=BitRate(50_000),
        num_active=1,
        num_waiting=0,
        num_stopped=0,
        num_stopped_total=0,
    )
    client.add_uri.return_value = make_gid("0000000000000001")

    # Mock tell_status
    client.tell_status.return_value = Download(
        gid=make_gid("0000000000000001"),
        download_id=make_download_id("d-mock"),
        name="contract_test.bin",
        state=DownloadState.ACTIVE,
        total_length=ByteSize(1000),
        completed_length=ByteSize(500),
    )

    backend = Aria2Backend(client=client)
    backend.initialize()
    return backend


class TestAria2ContractConformance:
    """Validate Aria2Backend conforms strictly to BackendProtocol."""

    def test_identity_and_capabilities(
        self, mock_aria2_backend: BackendProtocol
    ) -> None:
        assert mock_aria2_backend.identity.id == "aria2"
        assert len(mock_aria2_backend.capabilities) >= 20
        assert mock_aria2_backend.ping() is True

    def test_lifecycle_and_diagnostics(
        self, mock_aria2_backend: BackendProtocol
    ) -> None:
        diag = mock_aria2_backend.get_diagnostics()
        assert diag.healthy is True
        assert diag.active_jobs == 1

    def test_job_submission_and_status(
        self, mock_aria2_backend: BackendProtocol
    ) -> None:
        job = Job(
            id=make_job_id("job-contract-aria2"),
            backend_id=mock_aria2_backend.identity.id,
            name="contract_test.bin",
        )
        submitted = mock_aria2_backend.submit_job(job)
        assert submitted.state == DownloadState.ACTIVE

        status = mock_aria2_backend.get_job_status(job.id)
        assert status.id == job.id
        assert status.state == DownloadState.ACTIVE
        assert status.progress.completed_length == ByteSize(500)
