"""Unit and integration tests for Persistence Repositories and Migrations (Epic E04)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.credentials import (
    CredentialKind,
    CredentialReference,
    CredentialScope,
)
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import (
    make_artifact_id,
    make_backend_id,
    make_credential_id,
    make_job_group_id,
    make_job_id,
)
from shusha.domain.job import Job, JobProgress
from shusha.domain.job_group import JobGroup, JobGroupKind
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Checksum
from shusha.infrastructure.persistence.migrations import apply_migrations
from shusha.infrastructure.persistence.repositories import (
    SqliteArtifactRepository,
    SqliteCredentialRepository,
    SqliteJobGroupRepository,
    SqliteJobRepository,
    SqliteSettingsRepository,
)


def _create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


class TestPersistenceMigrations:
    """Tests for SQLite versioned schema migrations (E04-I03)."""

    def test_apply_migrations_creates_all_tables(self) -> None:
        conn = sqlite3.connect(":memory:")
        version = apply_migrations(conn)
        assert version == 2

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "categories",
            "downloads",
            "download_files",
            "download_sources",
            "settings",
            "jobs",
            "job_groups",
            "artifacts",
            "credential_references",
        }
        for table in expected_tables:
            assert table in tables


class TestSqliteJobRepository:
    """Tests for SqliteJobRepository (E04-I02)."""

    def test_save_and_retrieve_job(self) -> None:
        conn = _create_test_db()
        repo = SqliteJobRepository(conn)

        job = Job(
            id=make_job_id("job-alpha"),
            backend_id=make_backend_id("aria2"),
            name="Fedora-Workstation-40.iso",
            state=DownloadState.ACTIVE,
            source=DownloadSource.from_str(
                "https://download.fedoraproject.org/fedora.iso"
            ),
            progress=JobProgress(
                total_length=ByteSize(2_000_000_000),
                completed_length=ByteSize(1_000_000_000),
                download_speed=BitRate(10_000_000),
                upload_speed=BitRate(500_000),
            ),
            metadata={"priority": "high"},
            backend_data={"aria2_gid": "1234567890abcdef"},
        )

        repo.save(job)
        assert repo.count() == 1

        fetched = repo.get(make_job_id("job-alpha"))
        assert fetched is not None
        assert fetched.id == "job-alpha"
        assert fetched.backend_id == "aria2"
        assert fetched.name == "Fedora-Workstation-40.iso"
        assert fetched.state == DownloadState.ACTIVE
        assert fetched.progress.percentage.value == 50.0
        assert fetched.metadata == {"priority": "high"}
        assert fetched.backend_data == {"aria2_gid": "1234567890abcdef"}

    def test_list_with_filtering_and_pagination(self) -> None:
        conn = _create_test_db()
        repo = SqliteJobRepository(conn)

        j1 = Job(
            id=make_job_id("j1"),
            backend_id=make_backend_id("aria2"),
            name="file1.zip",
            state=DownloadState.ACTIVE,
        )
        j2 = Job(
            id=make_job_id("j2"),
            backend_id=make_backend_id("yt-dlp"),
            name="video.mp4",
            state=DownloadState.COMPLETED,
        )
        j3 = Job(
            id=make_job_id("j3"),
            backend_id=make_backend_id("aria2"),
            name="file2.zip",
            state=DownloadState.COMPLETED,
        )

        repo.save(j1)
        repo.save(j2)
        repo.save(j3)

        assert len(repo.list_jobs()) == 3
        assert len(repo.list_jobs(state=DownloadState.ACTIVE)) == 1
        assert len(repo.list_jobs(backend_id=make_backend_id("yt-dlp"))) == 1
        assert len(repo.list_jobs(limit=2)) == 2

    def test_delete_job(self) -> None:
        conn = _create_test_db()
        repo = SqliteJobRepository(conn)
        job = Job(
            id=make_job_id("j-del"),
            backend_id=make_backend_id("aria2"),
            name="temporary.bin",
        )
        repo.save(job)
        assert repo.delete(make_job_id("j-del")) is True
        assert repo.get(make_job_id("j-del")) is None


class TestSqliteArtifactRepository:
    """Tests for SqliteArtifactRepository (E04-I02)."""

    def test_save_and_list_artifacts_for_job(self) -> None:
        conn = _create_test_db()
        job_repo = SqliteJobRepository(conn)
        artifact_repo = SqliteArtifactRepository(conn)

        job = Job(
            id=make_job_id("job-art"),
            backend_id=make_backend_id("aria2"),
            name="media",
        )
        job_repo.save(job)

        art1 = Artifact(
            id=make_artifact_id("art-1"),
            job_id=make_job_id("job-art"),
            kind=ArtifactKind.FILE,
            name="track1.flac",
            path=Path("/music/track1.flac"),
            size=ByteSize(25_000_000),
            checksum=Checksum(
                algorithm="sha256",
                digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ),
            status=ArtifactStatus.VERIFIED,
        )
        art2 = Artifact(
            id=make_artifact_id("art-2"),
            job_id=make_job_id("job-art"),
            kind=ArtifactKind.FILE,
            name="cover.jpg",
            path=Path("/music/cover.jpg"),
            size=ByteSize(500_000),
        )

        artifact_repo.save(art1)
        artifact_repo.save(art2)

        fetched_arts = artifact_repo.list_for_job(make_job_id("job-art"))
        assert len(fetched_arts) == 2
        assert fetched_arts[0].name == "track1.flac"
        assert fetched_arts[0].is_verified


class TestSqliteJobGroupRepository:
    """Tests for SqliteJobGroupRepository (E04-I02)."""

    def test_save_and_retrieve_group_with_child_jobs(self) -> None:
        conn = _create_test_db()
        group_repo = SqliteJobGroupRepository(conn)
        job_repo = SqliteJobRepository(conn)

        gid = make_job_group_id("grp-batch-1")
        group = JobGroup(
            id=gid,
            name="Dataset Batch",
            kind=JobGroupKind.BATCH,
            total_jobs=2,
            completed_jobs=1,
            total_length=ByteSize(2000),
            completed_length=ByteSize(1000),
        )
        group_repo.save(group)

        j1 = Job(
            id=make_job_id("j1"),
            backend_id=make_backend_id("aria2"),
            name="p1",
            group_id=gid,
        )
        j2 = Job(
            id=make_job_id("j2"),
            backend_id=make_backend_id("aria2"),
            name="p2",
            group_id=gid,
        )
        job_repo.save(j1)
        job_repo.save(j2)

        fetched = group_repo.get(gid)
        assert fetched is not None
        assert fetched.name == "Dataset Batch"
        assert fetched.job_ids == (make_job_id("j1"), make_job_id("j2"))
        assert fetched.progress.value == 50.0


class TestSqliteSettingsAndCredentialRepositories:
    """Tests for Settings and Credential Reference persistence."""

    def test_settings_repository(self) -> None:
        conn = _create_test_db()
        settings_repo = SqliteSettingsRepository(conn)

        settings_repo.set("theme", "dark")
        settings_repo.set("max_concurrent", 10)

        assert settings_repo.get("theme") == "dark"
        assert settings_repo.get("max_concurrent") == 10
        assert settings_repo.get("nonexistent", default="fallback") == "fallback"

        all_settings = settings_repo.get_all()
        assert all_settings["theme"] == "dark"
        assert all_settings["max_concurrent"] == 10

    def test_credential_repository(self) -> None:
        conn = _create_test_db()
        cred_repo = SqliteCredentialRepository(conn)

        cred = CredentialReference(
            id=make_credential_id("cred-1"),
            kind=CredentialKind.RPC_SECRET,
            store_key="keyring:aria2_secret",
            scope=CredentialScope.GLOBAL,
            label="Aria2 RPC",
        )
        cred_repo.save(cred)

        fetched = cred_repo.get(make_credential_id("cred-1"))
        assert fetched is not None
        assert fetched.store_key == "keyring:aria2_secret"
        assert fetched.matches_domain("anywhere.com")
