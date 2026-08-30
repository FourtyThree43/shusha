"""Strongly typed domain identifiers for Shusha."""

from __future__ import annotations

from typing import NewType

Gid = NewType("Gid", str)
DownloadId = NewType("DownloadId", str)
JobId = NewType("JobId", str)
JobGroupId = NewType("JobGroupId", str)
ArtifactId = NewType("ArtifactId", str)
AcquisitionId = NewType("AcquisitionId", str)
CredentialId = NewType("CredentialId", str)
BackendId = NewType("BackendId", str)
CategoryId = NewType("CategoryId", str)
ProfileId = NewType("ProfileId", str)
HistoryId = NewType("HistoryId", str)
TaskId = NewType("TaskId", str)
SessionId = NewType("SessionId", str)
ConnectionId = NewType("ConnectionId", str)
PeerId = NewType("PeerId", str)


def make_gid(val: str) -> Gid:
    """Create and validate an aria2 16-character hex GID."""
    clean = val.strip()
    if not clean:
        raise ValueError("GID cannot be empty.")
    return Gid(clean)


def make_download_id(val: str) -> DownloadId:
    """Create a domain download identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("DownloadId cannot be empty.")
    return DownloadId(clean)


def make_job_id(val: str) -> JobId:
    """Create a domain job identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("JobId cannot be empty.")
    return JobId(clean)


def make_job_group_id(val: str) -> JobGroupId:
    """Create a domain job group identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("JobGroupId cannot be empty.")
    return JobGroupId(clean)


def make_artifact_id(val: str) -> ArtifactId:
    """Create a domain artifact identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("ArtifactId cannot be empty.")
    return ArtifactId(clean)


def make_acquisition_id(val: str) -> AcquisitionId:
    """Create an acquisition request identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("AcquisitionId cannot be empty.")
    return AcquisitionId(clean)


def make_credential_id(val: str) -> CredentialId:
    """Create a credential reference identifier."""
    clean = val.strip()
    if not clean:
        raise ValueError("CredentialId cannot be empty.")
    return CredentialId(clean)


def make_backend_id(val: str) -> BackendId:
    """Create a backend identifier."""
    clean = val.strip().lower()
    if not clean:
        raise ValueError("BackendId cannot be empty.")
    return BackendId(clean)


def make_category_id(val: str) -> CategoryId:
    """Create a category identifier."""
    clean = val.strip().lower()
    if not clean:
        raise ValueError("CategoryId cannot be empty.")
    return CategoryId(clean)
