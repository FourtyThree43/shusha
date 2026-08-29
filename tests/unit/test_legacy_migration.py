"""
Unit tests for legacy configuration and database migration.
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.persistence.database import DatabaseManager
from shusha.infrastructure.persistence.legacy_migration import (
    migrate_legacy_settings,
    migrate_legacy_sqlite_downloads,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


class TestLegacyMigration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.target_db_path = self.temp_path / "shusha2.db"
        self.db_manager = DatabaseManager(self.target_db_path)
        self.download_repo = DownloadRepository(self.db_manager)
        self.settings_store = SettingsStore(self.db_manager)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_migrate_legacy_settings_json(self):
        legacy_json = self.temp_path / "settings.json"
        legacy_json.write_text(
            json.dumps(
                {
                    "download_dir": "/custom/downloads",
                    "theme": "united",
                    "max_active_downloads": 8,
                    "speed_limit_download": 500000,
                    "clipboard_watch": True,
                }
            ),
            encoding="utf-8",
        )

        migrated = migrate_legacy_settings(legacy_json, self.settings_store)
        self.assertTrue(migrated)

        loaded = self.settings_store.load_settings()
        self.assertEqual(loaded.download_dir, "/custom/downloads")
        self.assertEqual(loaded.theme, "united")
        self.assertEqual(loaded.max_active_downloads, 8)
        self.assertEqual(loaded.speed_limit_download, 500000)
        self.assertTrue(loaded.clipboard_watch)

    def test_migrate_legacy_sqlite_downloads(self):
        legacy_db = self.temp_path / "legacy.db"
        conn = sqlite3.connect(legacy_db)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE downloads (gid TEXT PRIMARY KEY, name TEXT, total_length INTEGER, completed_length INTEGER, state TEXT)"
        )
        cur.execute(
            "INSERT INTO downloads VALUES ('gid001', 'sample.iso', 1048576, 1048576, 'COMPLETE')"
        )
        cur.execute(
            "INSERT INTO downloads VALUES ('gid002', 'video.mp4', 5242880, 2621440, 'ACTIVE')"
        )
        conn.commit()
        conn.close()

        count = migrate_legacy_sqlite_downloads(legacy_db, self.download_repo)
        self.assertEqual(count, 2)

        all_dls = self.download_repo.list_all()
        self.assertEqual(len(all_dls), 2)
        names = {dl.name for dl in all_dls}
        self.assertIn("sample.iso", names)
        self.assertIn("video.mp4", names)


if __name__ == "__main__":
    unittest.main()
