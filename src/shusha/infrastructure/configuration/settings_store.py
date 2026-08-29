"""
Persistent application settings repository and domain settings models for Shusha 2.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from shusha.infrastructure.persistence.database import DatabaseManager


@dataclass(slots=True)
class AppSettings:
    """Strongly typed application configuration settings."""

    theme: str = "darkly"
    download_dir: str = field(default_factory=lambda: str(Path.home() / "Downloads"))
    aria2_host: str = "127.0.0.1"
    aria2_port: int = 6800
    auto_start_daemon: bool = True
    custom_aria2_path: str | None = None
    max_active_downloads: int = 5
    speed_limit_download: int = 0
    speed_limit_upload: int = 0
    clipboard_watch: bool = False
    sound_notifications: bool = True
    close_to_tray: bool = False


class SettingsStore:
    """Store for persisting application preferences in SQLite."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_value(self, key: str, default: Any = None) -> Any:
        """Fetch raw JSON setting by key."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value_json FROM settings WHERE key = ?;", (key,))
            row = cursor.fetchone()
            if not row:
                return default
            return json.loads(row["value_json"])

    def set_value(self, key: str, value: Any) -> None:
        """Persist a raw JSON setting by key."""
        val_json = json.dumps(value)
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settings (key, value_json, updated_at)
                VALUES (?, ?, datetime('now', 'utc'))
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at;
                """,
                (key, val_json),
            )

    def load_settings(self) -> AppSettings:
        """Load full typed application settings."""
        stored = self.get_value("app_settings", default={})
        if not isinstance(stored, dict):
            stored = {}

        defaults = asdict(AppSettings())
        defaults.update(stored)
        return AppSettings(**defaults)

    def save_settings(self, settings: AppSettings) -> None:
        """Save full typed application settings."""
        self.set_value("app_settings", asdict(settings))
