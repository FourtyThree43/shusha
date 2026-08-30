"""Persistence layer for Shusha: SQLite database management and repositories."""

from shusha.infrastructure.persistence.contracts import (
    ArtifactRepository,
    CategoryRepositoryProtocol,
    CredentialRepositoryProtocol,
    JobGroupRepository,
    JobRepository,
    SettingsRepositoryProtocol,
)
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.migrations import apply_migrations
from shusha.infrastructure.persistence.repositories import (
    CategoryRepository,
    DownloadRepository,
    SqliteArtifactRepository,
    SqliteCredentialRepository,
    SqliteJobGroupRepository,
    SqliteJobRepository,
    SqliteSettingsRepository,
)

__all__ = [
    "ArtifactRepository",
    "CategoryRepository",
    "CategoryRepositoryProtocol",
    "CredentialRepositoryProtocol",
    "DatabaseManager",
    "DownloadRepository",
    "JobGroupRepository",
    "JobRepository",
    "SettingsRepositoryProtocol",
    "SqliteArtifactRepository",
    "SqliteCredentialRepository",
    "SqliteJobGroupRepository",
    "SqliteJobRepository",
    "SqliteSettingsRepository",
    "apply_migrations",
]
