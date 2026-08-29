"""
Application context providing dependency injection for presentation views.
"""

from dataclasses import dataclass

from shusha.application.services.sync_coordinator import SyncCoordinator
from shusha.application.use_cases.category_use_cases import (
    AssignCategoryUseCase,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    UpdateCategoryUseCase,
)
from shusha.application.use_cases.download_use_cases import (
    AddDownloadUseCase,
    ChangeDownloadOptionsUseCase,
    InspectDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.application.use_cases.queue_use_cases import (
    ReorderQueueUseCase,
    SetQueueLimitsUseCase,
)
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.daemon.manager import DaemonSupervisor
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


@dataclass(slots=True)
class AppContext:
    """Strongly typed service locator and DI container for UI views."""

    client: Aria2Client
    daemon_supervisor: DaemonSupervisor
    download_repo: DownloadRepository
    category_repo: CategoryRepository
    settings_store: SettingsStore
    sync_coordinator: SyncCoordinator

    # Use cases
    add_download_uc: AddDownloadUseCase
    pause_download_uc: PauseDownloadUseCase
    resume_download_uc: ResumeDownloadUseCase
    remove_download_uc: RemoveDownloadUseCase
    inspect_download_uc: InspectDownloadUseCase
    change_options_uc: ChangeDownloadOptionsUseCase
    create_category_uc: CreateCategoryUseCase
    update_category_uc: UpdateCategoryUseCase
    delete_category_uc: DeleteCategoryUseCase
    assign_category_uc: AssignCategoryUseCase
    reorder_queue_uc: ReorderQueueUseCase
    set_queue_limits_uc: SetQueueLimitsUseCase
