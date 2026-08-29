"""Bandwidth Scheduler for automated time-based speed throttling.

This module allows users to configure automated speed limit windows (e.g. daytime limits
during remote work hours, unlimited at night).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)


@dataclass
class ScheduleRule:
    """Represents a scheduled bandwidth throttling rule."""

    name: str
    enabled: bool
    start_hour: int  # 0-23
    start_minute: int  # 0-59
    end_hour: int  # 0-23
    end_minute: int  # 0-59
    days_of_week: list[int]  # 0=Monday, 6=Sunday
    max_download_limit: str  # e.g. "1M", "500K", "0" (unlimited)
    max_upload_limit: str  # e.g. "200K", "0"

    def is_active(self, now: datetime.datetime | None = None) -> bool:
        """Check whether this rule is currently in effect."""
        if not self.enabled:
            return False

        current = now or datetime.datetime.now()
        if current.weekday() not in self.days_of_week:
            return False

        current_minutes = current.hour * 60 + current.minute
        start_min = self.start_hour * 60 + self.start_minute
        end_min = self.end_hour * 60 + self.end_minute

        if start_min <= end_min:
            return start_min <= current_minutes <= end_min
        else:
            # Over-midnight schedule (e.g. 22:00 to 06:00)
            return current_minutes >= start_min or current_minutes <= end_min


class BandwidthScheduler:
    """Manages evaluation and application of scheduled bandwidth limits."""

    def __init__(self, rules: list[ScheduleRule] | None = None) -> None:
        self.rules: list[ScheduleRule] = rules or []
        self._last_applied_rule: str | None = None

    def add_rule(self, rule: ScheduleRule) -> None:
        """Add a new scheduling rule."""
        self.rules.append(rule)

    def evaluate(self, now: datetime.datetime | None = None) -> tuple[str, str] | None:
        """Evaluate active rules and return (max_download, max_upload) limits if applicable.

        Returns:
            Tuple `(max_download_limit, max_upload_limit)` for the first active rule, or None.
        """
        current = now or datetime.datetime.now()
        for rule in self.rules:
            if rule.is_active(current):
                return rule.max_download_limit, rule.max_upload_limit
        return None

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Serialize rules to dictionary list for TOML settings persistence."""
        return [
            {
                "name": r.name,
                "enabled": r.enabled,
                "start_hour": r.start_hour,
                "start_minute": r.start_minute,
                "end_hour": r.end_hour,
                "end_minute": r.end_minute,
                "days_of_week": r.days_of_week,
                "max_download_limit": r.max_download_limit,
                "max_upload_limit": r.max_upload_limit,
            }
            for r in self.rules
        ]

    @classmethod
    def from_dict_list(cls, data: list[dict[str, Any]]) -> BandwidthScheduler:
        """Deserialize rules from configuration dictionaries."""
        rules: list[ScheduleRule] = []
        for d in data:
            try:
                rules.append(
                    ScheduleRule(
                        name=str(d.get("name", "Rule")),
                        enabled=bool(d.get("enabled", True)),
                        start_hour=int(d.get("start_hour", 8)),
                        start_minute=int(d.get("start_minute", 0)),
                        end_hour=int(d.get("end_hour", 18)),
                        end_minute=int(d.get("end_minute", 0)),
                        days_of_week=list(d.get("days_of_week", [0, 1, 2, 3, 4, 5, 6])),
                        max_download_limit=str(d.get("max_download_limit", "1M")),
                        max_upload_limit=str(d.get("max_upload_limit", "256K")),
                    )
                )
            except Exception as e:
                logger.log(f"Failed to parse schedule rule: {e}", level="debug")
        return cls(rules=rules)
