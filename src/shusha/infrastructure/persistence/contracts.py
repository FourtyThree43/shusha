"""Typed repository protocols for domain persistence (E04-I01)."""

from __future__ import annotations

from typing import Any, Protocol

from shusha.domain.artifact import Artifact
from shusha.domain.category import Category
from shusha.domain.credentials import CredentialReference
from shusha.domain.identifiers import (
    ArtifactId,
    BackendId,
    CategoryId,
    CredentialId,
    JobGroupId,
    JobId,
)
from shusha.domain.job import Job
from shusha.domain.job_group import JobGroup
from shusha.domain.states import DownloadState


class JobRepository(Protocol):
    """Persistence contract for Job entities."""

    def save(self, job: Job) -> None: ...

    def get(self, job_id: JobId) -> Job | None: ...

    def list_jobs(
        self,
        state: DownloadState | None = None,
        backend_id: BackendId | None = None,
        category_id: CategoryId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]: ...

    def delete(self, job_id: JobId) -> bool: ...

    def count(self) -> int: ...


class JobGroupRepository(Protocol):
    """Persistence contract for JobGroup entities."""

    def save(self, group: JobGroup) -> None: ...

    def get(self, group_id: JobGroupId) -> JobGroup | None: ...

    def list_groups(self) -> list[JobGroup]: ...

    def delete(self, group_id: JobGroupId) -> bool: ...


class ArtifactRepository(Protocol):
    """Persistence contract for Artifact entities."""

    def save(self, artifact: Artifact) -> None: ...

    def get(self, artifact_id: ArtifactId) -> Artifact | None: ...

    def list_for_job(self, job_id: JobId) -> list[Artifact]: ...

    def delete(self, artifact_id: ArtifactId) -> bool: ...


class CategoryRepositoryProtocol(Protocol):
    """Persistence contract for Category entities."""

    def save(self, category: Category) -> None: ...

    def get(self, category_id: CategoryId) -> Category | None: ...

    def list_all(self) -> list[Category]: ...

    def delete(self, category_id: CategoryId) -> bool: ...


class SettingsRepositoryProtocol(Protocol):
    """Persistence contract for key-value application settings."""

    def get(self, key: str, default: Any = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...

    def delete(self, key: str) -> bool: ...

    def get_all(self) -> dict[str, Any]: ...


class CredentialRepositoryProtocol(Protocol):
    """Persistence contract for credential references."""

    def save(self, credential: CredentialReference) -> None: ...

    def get(self, credential_id: CredentialId) -> CredentialReference | None: ...

    def list_all(self) -> list[CredentialReference]: ...

    def delete(self, credential_id: CredentialId) -> bool: ...
