"""
Application use cases for Shusha 2.
"""

from shusha.application.use_cases.category_use_cases import (
    AssignCategoryUseCase,
    CategoryDTO,
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    UpdateCategoryUseCase,
)
from shusha.application.use_cases.download_use_cases import (
    AddDownloadRequest,
    AddDownloadUseCase,
    ChangeDownloadOptionsUseCase,
    DownloadInspection,
    InspectDownloadUseCase,
    PauseDownloadUseCase,
    RemoveDownloadUseCase,
    ResumeDownloadUseCase,
)
from shusha.application.use_cases.queue_use_cases import (
    QueueAction,
    ReorderQueueUseCase,
    SetQueueLimitsUseCase,
)

__all__ = [
    "AddDownloadRequest",
    "AddDownloadUseCase",
    "AssignCategoryUseCase",
    "CategoryDTO",
    "ChangeDownloadOptionsUseCase",
    "CreateCategoryUseCase",
    "DeleteCategoryUseCase",
    "DownloadInspection",
    "InspectDownloadUseCase",
    "PauseDownloadUseCase",
    "QueueAction",
    "RemoveDownloadUseCase",
    "ReorderQueueUseCase",
    "ResumeDownloadUseCase",
    "SetQueueLimitsUseCase",
    "UpdateCategoryUseCase",
]
