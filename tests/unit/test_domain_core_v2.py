"""Unit tests for Shusha 2 Core Domain Models (Epic E02)."""

from __future__ import annotations

from pathlib import Path

from shusha.domain.acquisition import (
    AcquisitionRequest,
    AcquisitionStatus,
    DetectedKind,
    Provenance,
    SelectionPolicy,
    SourceKind,
)
from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.capability import Capability, CapabilitySet
from shusha.domain.credentials import (
    CredentialKind,
    CredentialReference,
    CredentialScope,
)
from shusha.domain.identifiers import (
    make_acquisition_id,
    make_artifact_id,
    make_backend_id,
    make_credential_id,
    make_job_group_id,
    make_job_id,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.job_group import JobGroup, JobGroupKind
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Percentage


class TestJobModel:
    """Tests for core Job entity (E02-I01)."""

    def test_job_creation_and_properties(self) -> None:
        job = Job(
            id=make_job_id("job-001"),
            backend_id=make_backend_id("aria2"),
            name="ubuntu-24.04-desktop-amd64.iso",
            state=DownloadState.QUEUED,
            progress=JobProgress(
                total_length=ByteSize(2_000_000_000),
                completed_length=ByteSize(1_000_000_000),
                download_speed=BitRate(50_000_000),
            ),
            backend_data={"aria2_gid": "0000000000000001"},
        )
        assert job.id == "job-001"
        assert job.backend_id == "aria2"
        assert not job.is_active
        assert not job.is_completed
        assert job.progress.percentage == Percentage(50.0)
        assert job.backend_data["aria2_gid"] == "0000000000000001"

    def test_job_lifecycle_transitions(self) -> None:
        job = Job(
            id=make_job_id("job-002"),
            backend_id=make_backend_id("yt-dlp"),
            name="Video download",
            state=DownloadState.STARTING,
        )
        active_job = job.transition_to(DownloadState.ACTIVE)
        assert active_job.is_active
        assert active_job.timestamps.started_at is not None

        paused_job = active_job.transition_to(DownloadState.PAUSED)
        assert paused_job.is_paused

        resumed_job = paused_job.transition_to(DownloadState.ACTIVE)
        assert resumed_job.is_active

        completed_job = resumed_job.transition_to(DownloadState.COMPLETED)
        assert completed_job.is_completed
        assert completed_job.timestamps.finished_at is not None


class TestArtifactModel:
    """Tests for Artifact entity (E02-I02)."""

    def test_artifact_file_and_directory(self, tmp_path: Path) -> None:
        test_file = tmp_path / "sample.mp4"
        test_file.write_bytes(b"dummy video data")

        artifact = Artifact(
            id=make_artifact_id("art-001"),
            job_id=make_job_id("job-001"),
            kind=ArtifactKind.FILE,
            name="sample.mp4",
            path=test_file,
            size=ByteSize(16),
            status=ArtifactStatus.VERIFIED,
        )
        assert artifact.kind == ArtifactKind.FILE
        assert artifact.is_verified
        assert artifact.is_available
        assert artifact.size == ByteSize(16)

    def test_artifact_collection_kind(self) -> None:
        artifact = Artifact(
            id=make_artifact_id("art-002"),
            job_id=make_job_id("job-002"),
            kind=ArtifactKind.PLAYLIST,
            name="Music Album Playlist",
            path="/downloads/music_album",
            status=ArtifactStatus.PENDING,
        )
        assert artifact.kind == ArtifactKind.PLAYLIST
        assert not artifact.is_verified


class TestJobGroupModel:
    """Tests for JobGroup entity (E02-I03)."""

    def test_job_group_progress_calculation(self) -> None:
        group = JobGroup(
            id=make_job_group_id("grp-001"),
            name="Season 1 Batch",
            kind=JobGroupKind.BATCH,
            job_ids=(
                make_job_id("j1"),
                make_job_id("j2"),
                make_job_id("j3"),
                make_job_id("j4"),
            ),
            total_jobs=4,
            completed_jobs=2,
            failed_jobs=0,
            total_length=ByteSize(400),
            completed_length=ByteSize(200),
        )
        assert not group.is_finished
        assert group.progress == Percentage(50.0)

        finished_group = JobGroup(
            id=make_job_group_id("grp-002"),
            name="Album",
            kind=JobGroupKind.PLAYLIST,
            total_jobs=3,
            completed_jobs=3,
            failed_jobs=0,
        )
        assert finished_group.is_finished
        assert finished_group.progress == Percentage(100.0)


class TestAcquisitionRequestModel:
    """Tests for AcquisitionRequest entity (E02-I04)."""

    def test_acquisition_request_creation(self) -> None:
        prov = Provenance(
            origin_url="https://youtube.com/watch?v=12345",
            source_application="chrome-extension",
        )
        req = AcquisitionRequest(
            id=make_acquisition_id("acq-001"),
            source_kind=SourceKind.BROWSER,
            raw_input="https://youtube.com/watch?v=12345",
            detected_kind=DetectedKind.MEDIA_STREAM,
            status=AcquisitionStatus.RESOLVED,
            preferred_backend=make_backend_id("yt-dlp"),
            selection_policy=SelectionPolicy.AUTOMATIC,
            provenance=prov,
        )
        assert req.is_resolved
        assert req.source_kind == SourceKind.BROWSER
        assert req.detected_kind == DetectedKind.MEDIA_STREAM
        assert req.preferred_backend == "yt-dlp"
        assert req.provenance.source_application == "chrome-extension"


class TestCapabilityModel:
    """Tests for Capability vocabulary and CapabilitySet (E02-I05)."""

    def test_capability_set_queries(self) -> None:
        caps = CapabilitySet.from_iterable(
            [
                Capability.HTTP,
                Capability.HTTPS,
                Capability.PAUSE_RESUME,
                Capability.SEGMENTATION,
                Capability.TORRENT,
                "metalink",
            ]
        )
        assert caps.has(Capability.HTTP)
        assert caps.has("https")
        assert caps.has("metalink")
        assert not caps.has(Capability.MEDIA_EXTRACTION)

        assert caps.supports_all([Capability.HTTP, Capability.TORRENT])
        assert not caps.supports_all([Capability.HTTP, Capability.PLAYLIST])
        assert caps.supports_any([Capability.PLAYLIST, Capability.TORRENT])
        assert not caps.supports_any([Capability.PLAYLIST, Capability.SUBTITLES])

        assert len(caps) == 6
        assert "http" in caps.to_list()


class TestCredentialReferenceModel:
    """Tests for CredentialReference entity (E02-I06)."""

    def test_credential_reference_domain_matching(self) -> None:
        cred = CredentialReference(
            id=make_credential_id("cred-001"),
            kind=CredentialKind.HTTP_AUTH,
            store_key="keyring:shusha:example.com",
            scope=CredentialScope.DOMAIN,
            domain_pattern="*.example.com",
            label="Example CDN Credentials",
        )
        assert cred.kind == CredentialKind.HTTP_AUTH
        assert cred.matches_domain("downloads.example.com")
        assert cred.matches_domain("static.example.com")
        assert not cred.matches_domain("otherdomain.org")

        global_cred = CredentialReference(
            id=make_credential_id("cred-002"),
            kind=CredentialKind.RPC_SECRET,
            store_key="keyring:shusha:aria2_rpc",
            scope=CredentialScope.GLOBAL,
            label="Aria2 RPC Secret",
        )
        assert global_cred.matches_domain("anywhere.org")
