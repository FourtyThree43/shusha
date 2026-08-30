"""SQLite implementation of SettingsRepositoryProtocol (E04-I02)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from shusha.infrastructure.persistence.contracts import SettingsRepositoryProtocol


class SqliteSettingsRepository(SettingsRepositoryProtocol):
    """Stores key-value application configuration in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch setting value by key."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value_json FROM settings WHERE key = ?;", (key,))
        row = cursor.fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        """Upsert a setting key and value."""
        cursor = self.conn.cursor()
        val_json = json.dumps(value)
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
        self.conn.commit()

    def delete(self, key: str) -> bool:
        """Remove a setting entry."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM settings WHERE key = ?;", (key,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_all(self) -> dict[str, Any]:
        """Fetch all stored key-value pairs."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value_json FROM settings;")
        result: dict[str, Any] = {}
        for key, val_json in cursor.fetchall():
            try:
                result[key] = json.loads(val_json)
            except Exception:
                result[key] = val_json
        return result
