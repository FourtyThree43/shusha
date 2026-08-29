"""
Download queue ordering and concurrency policy.
"""

from dataclasses import dataclass, field

from shusha.domain.identifiers import DownloadId


@dataclass(slots=True)
class DownloadQueue:
    """Manages ordered download execution and concurrency boundaries."""

    max_active_downloads: int = 5
    items: list[DownloadId] = field(default_factory=list)

    def move_to_top(self, download_id: DownloadId) -> None:
        if download_id in self.items:
            self.items.remove(download_id)
            self.items.insert(0, download_id)

    def move_to_bottom(self, download_id: DownloadId) -> None:
        if download_id in self.items:
            self.items.remove(download_id)
            self.items.append(download_id)

    def move_up(self, download_id: DownloadId) -> None:
        if download_id in self.items:
            idx = self.items.index(download_id)
            if idx > 0:
                self.items[idx], self.items[idx - 1] = (
                    self.items[idx - 1],
                    self.items[idx],
                )

    def move_down(self, download_id: DownloadId) -> None:
        if download_id in self.items:
            idx = self.items.index(download_id)
            if idx < len(self.items) - 1:
                self.items[idx], self.items[idx + 1] = (
                    self.items[idx + 1],
                    self.items[idx],
                )
