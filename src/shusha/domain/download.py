"""
Download aggregate entity in the Shusha 2 domain.
"""

from dataclasses import dataclass, field, replace

from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import CategoryId, DownloadId, Gid
from shusha.domain.states import DownloadState, validate_transition
from shusha.domain.values import Bitfield, BitRate, ByteSize, Duration, Percentage


@dataclass(frozen=True, slots=True, kw_only=True)
class Download:
    """Core Download domain entity."""

    gid: Gid
    download_id: DownloadId
    name: str
    state: DownloadState
    total_length: ByteSize | None = None
    completed_length: ByteSize = field(default_factory=lambda: ByteSize(0))
    download_speed: BitRate = field(default_factory=lambda: BitRate(0))
    upload_speed: BitRate = field(default_factory=lambda: BitRate(0))
    eta: Duration | None = None
    files: list[DownloadFile] = field(default_factory=list)
    sources: list[DownloadSource] = field(default_factory=list)
    category_id: CategoryId | None = None
    bitfield: Bitfield | None = None
    error_code: int | None = None
    error_message: str | None = None
    connections: int = 0
    dir_path: str = ""
    is_torrent: bool = False
    is_metalink: bool = False

    @property
    def progress(self) -> Percentage:
        """Calculate download progress percentage."""
        return Percentage.from_progress(self.completed_length, self.total_length)

    @property
    def is_active(self) -> bool:
        return self.state == DownloadState.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.state == DownloadState.COMPLETED

    @property
    def is_paused(self) -> bool:
        return self.state == DownloadState.PAUSED

    @property
    def is_failed(self) -> bool:
        return self.state == DownloadState.FAILED

    def transition_to(self, new_state: DownloadState) -> Download:
        """Enforce domain invariants and state transition rules."""
        validate_transition(self.state, new_state)
        return replace(self, state=new_state)

    def assign_category(self, category_id: CategoryId | None) -> Download:
        """Assign or change the category associated with this download."""
        return replace(self, category_id=category_id)

    def update_progress(
        self,
        completed_length: ByteSize,
        total_length: ByteSize | None,
        download_speed: BitRate,
        upload_speed: BitRate,
        connections: int = 0,
        bitfield: Bitfield | None = None,
    ) -> Download:
        """Produce updated download entity with fresh metrics and ETA."""
        eta = Duration.calculate_eta(completed_length, total_length, download_speed)
        return replace(
            self,
            completed_length=completed_length,
            total_length=total_length,
            download_speed=download_speed,
            upload_speed=upload_speed,
            eta=eta,
            connections=connections,
            bitfield=bitfield or self.bitfield,
        )
