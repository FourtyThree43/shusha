"""
Schedule windows and automated speed limits in Shusha 2.
"""

from dataclasses import dataclass
from datetime import datetime, time

from shusha.domain.values import BitRate


@dataclass(frozen=True, slots=True)
class ScheduleWindow:
    """A recurring time window for automated downloading or speed throttling."""

    day_of_week: int  # 0 = Monday, 6 = Sunday, or -1 = Daily
    start_time: time
    end_time: time
    speed_limit: BitRate | None = None  # None = Unlimited
    pause_all: bool = False

    def is_active_at(self, dt: datetime) -> bool:
        """Check if this schedule window applies at the given datetime."""
        if self.day_of_week != -1 and dt.weekday() != self.day_of_week:
            return False

        t = dt.time()
        if self.start_time <= self.end_time:
            return self.start_time <= t <= self.end_time
        # Window spans midnight (e.g. 23:00 to 06:00)
        return t >= self.start_time or t <= self.end_time
