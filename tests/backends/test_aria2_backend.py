"""Unit tests for aria2 Reference Backend Adapter and Option Binding (Epic E07)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shusha.backends.aria2 import Aria2Backend, Aria2Supervisor, load_aria2_options
from shusha.backends.contract import BackendProtocol
from shusha.backends.errors import BackendJobNotFoundError
from shusha.backends.options import OptionType
from shusha.domain.capability import Capability
from shusha.domain.download import Download
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import make_download_id, make_gid, make_job_id
from shusha.domain.job import Job
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.aria2.client import Aria2Client, VersionInfo


class TestAria2OptionBinding:
    """Tests for authoritative aria2 option catalogue binding (E07-I07)."""

    def test_load_all_198_aria2_options(self) -> None:
        options = load_aria2_options()
        assert len(options) == 198

        opt_map = {o.name: o for o in options}
        assert "dir" in opt_map
        assert opt_map["dir"].option_type == OptionType.PATH

        assert "max-connection-per-server" in opt_map
        assert opt_map["max-connection-per-server"].option_type == OptionType.INT
        assert opt_map["max-connection-per-server"].default_value == "1"

        assert "file-allocation" in opt_map
        assert opt_map["file-allocation"].option_type == OptionType.CHOICE
        assert opt_map["file-allocation"].allowed_values is not None
        assert "falloc" in opt_map["file-allocation"].allowed_values

        assert "rpc-secret" in opt_map
        assert opt_map["rpc-secret"].security_sensitive is True


class TestAria2Supervisor:
    """Tests for Aria2Supervisor (E07-I03)."""

    def test_supervisor_executable_discovery(self) -> None:
        sup = Aria2Supervisor(
            executable_path="/usr/bin/aria2c", port=6800, secret="test-secret"
        )
        assert sup.executable_path == "/usr/bin/aria2c"
        assert sup.port == 6800
        assert sup.secret == "test-secret"
        assert sup.is_running() is False


class TestAria2BackendAdapter:
    """Tests for Aria2Backend (E07-I04, E07-I05, E07-I06)."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        client = MagicMock(spec=Aria2Client)
        client.get_version.return_value = VersionInfo(
            version="1.37.0",
            enabled_features=["BitTorrent", "GZip", "HTTPS", "MessageDigest"],
        )
        return client

    def test_aria2_backend_implements_protocol(self, mock_client: MagicMock) -> None:
        backend = Aria2Backend(client=mock_client)
        assert isinstance(backend, BackendProtocol)
        assert backend.identity.id == "aria2"
        assert backend.capabilities.has(Capability.TORRENT)
        assert backend.capabilities.has(Capability.HTTP)
        assert backend.capabilities.has(Capability.MAGNET)

    def test_submit_and_status_job_workflow(self, mock_client: MagicMock) -> None:
        backend = Aria2Backend(client=mock_client)
        mock_client.add_uri.return_value = make_gid("2089b05ecca3d829")

        job = Job(
            id=make_job_id("job-aria2-1"),
            backend_id=backend.identity.id,
            name="debian.iso",
            source=DownloadSource.from_str("https://cdimage.debian.org/debian.iso"),
        )

        submitted = backend.submit_job(job)
        assert submitted.state == DownloadState.ACTIVE
        assert submitted.backend_data["aria2_gid"] == "2089b05ecca3d829"
        mock_client.add_uri.assert_called_once()

        mock_download = Download(
            gid=make_gid("2089b05ecca3d829"),
            download_id=make_download_id("deb-1"),
            name="debian.iso",
            state=DownloadState.ACTIVE,
            total_length=ByteSize(600_000_000),
            completed_length=ByteSize(300_000_000),
            download_speed=BitRate(10_000_000),
        )
        mock_client.tell_status.return_value = mock_download

        status = backend.get_job_status(job.id)
        assert status.state == DownloadState.ACTIVE
        assert status.progress.completed_length == ByteSize(300_000_000)
        assert status.progress.percentage.value == 50.0

    def test_pause_resume_cancel_operations(self, mock_client: MagicMock) -> None:
        backend = Aria2Backend(client=mock_client)
        mock_client.add_uri.return_value = make_gid("1111222233334444")

        job = Job(
            id=make_job_id("j-op"),
            backend_id=backend.identity.id,
            name="archive.zip",
            source=DownloadSource.from_str("https://example.com/archive.zip"),
        )
        backend.submit_job(job)

        mock_download = Download(
            gid=make_gid("1111222233334444"),
            download_id=make_download_id("d1"),
            name="archive.zip",
            state=DownloadState.PAUSED,
        )
        mock_client.tell_status.return_value = mock_download

        paused = backend.pause_job(job.id)
        assert paused.state == DownloadState.PAUSED
        mock_client.pause.assert_called_once()

        mock_download_active = Download(
            gid=make_gid("1111222233334444"),
            download_id=make_download_id("d1"),
            name="archive.zip",
            state=DownloadState.ACTIVE,
        )
        mock_client.tell_status.return_value = mock_download_active

        resumed = backend.resume_job(job.id)
        assert resumed.state == DownloadState.ACTIVE
        mock_client.unpause.assert_called_once()

        backend.cancel_job(job.id)
        mock_client.remove.assert_called_once()

        backend.remove_job(job.id)
        with pytest.raises(BackendJobNotFoundError):
            backend.get_job_status(job.id)
