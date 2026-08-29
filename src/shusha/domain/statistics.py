"""
Aggregated transfer metrics and session statistics.
"""

from dataclasses import dataclass, field

from shusha.domain.values import BitRate, ByteSize


@dataclass(frozen=True, slots=True)
class GlobalStatistics:
    """Real-time engine and queue statistics."""

    download_speed: BitRate
    upload_speed: BitRate
    num_active: int
    num_waiting: int
    num_stopped: int
    num_stopped_total: int
    total_downloaded: ByteSize = field(default_factory=lambda: ByteSize(0))
    total_uploaded: ByteSize = field(default_factory=lambda: ByteSize(0))
