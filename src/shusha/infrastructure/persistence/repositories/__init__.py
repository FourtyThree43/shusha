"""Repository implementations for Shusha domain models."""

from shusha.infrastructure.persistence.repositories.artifact_repository import (
    SqliteArtifactRepository,
)
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.credential_repository import (
    SqliteCredentialRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)
from shusha.infrastructure.persistence.repositories.job_group_repository import (
    SqliteJobGroupRepository,
)
from shusha.infrastructure.persistence.repositories.job_repository import (
    SqliteJobRepository,
)
from shusha.infrastructure.persistence.repositories.settings_repository import (
    SqliteSettingsRepository,
)

__all__ = [
    "CategoryRepository",
    "DownloadRepository",
    "SqliteArtifactRepository",
    "SqliteCredentialRepository",
    "SqliteJobGroupRepository",
    "SqliteJobRepository",
    "SqliteSettingsRepository",
]
