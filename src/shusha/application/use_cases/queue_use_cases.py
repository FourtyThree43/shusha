"""
Queue manipulation and prioritization use cases for Shusha 2.
"""

from enum import StrEnum

from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.identifiers import DownloadId
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


class QueueAction(StrEnum):
    TOP = "TOP"
    UP = "UP"
    DOWN = "DOWN"
    BOTTOM = "BOTTOM"


class ReorderQueueUseCase:
    """Modifies the position of a waiting download in the aria2 execution queue."""

    def __init__(self, client: Aria2Client, download_repo: DownloadRepository) -> None:
        self.client = client
        self.download_repo = download_repo

    def execute(self, download_id: DownloadId, action: QueueAction) -> int:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        match action:
            case QueueAction.TOP:
                return self.client.change_position(dl.gid, 0, "POS_SET")
            case QueueAction.BOTTOM:
                return self.client.change_position(dl.gid, 0, "POS_END")
            case QueueAction.UP:
                return self.client.change_position(dl.gid, -1, "POS_CUR")
            case QueueAction.DOWN:
                return self.client.change_position(dl.gid, 1, "POS_CUR")


class SetQueueLimitsUseCase:
    """Updates daemon concurrency limits and bandwidth throttles."""

    def __init__(self, client: Aria2Client) -> None:
        self.client = client

    def execute(
        self,
        max_concurrent_downloads: int | None = None,
        max_download_speed: str | None = None,
        max_upload_speed: str | None = None,
    ) -> bool:
        options: dict[str, str] = {}
        if max_concurrent_downloads is not None:
            options["max-concurrent-downloads"] = str(max_concurrent_downloads)
        if max_download_speed is not None:
            options["max-overall-download-limit"] = max_download_speed
        if max_upload_speed is not None:
            options["max-overall-upload-limit"] = max_upload_speed

        if options:
            return self.client.change_global_option(options)
        return True
