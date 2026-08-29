"""
Legacy Migration Engine for Shusha 2.
Safely migrates configurations, categories, and download records from legacy Shusha 1.x installations.
"""

import json
import logging
import sqlite3
from dataclasses import replace
from pathlib import Path

from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId, Gid
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.configuration.settings_store import SettingsStore
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)

logger = logging.getLogger(__name__)


def migrate_legacy_settings(
    legacy_json_path: Path,
    target_settings_store: SettingsStore,
) -> bool:
    """Migrate settings from legacy JSON file into Shusha 2 SQLite store."""
    if not legacy_json_path.exists():
        return False

    try:
        raw = json.loads(legacy_json_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return False

        current = target_settings_store.load_settings()
        updated = replace(
            current,
            download_dir=str(raw.get("download_dir", current.download_dir)),
            theme=str(raw.get("theme", current.theme)),
            max_active_downloads=int(
                raw.get("max_active_downloads", current.max_active_downloads)
            ),
            speed_limit_download=int(
                raw.get("speed_limit_download", current.speed_limit_download)
            ),
            speed_limit_upload=int(
                raw.get("speed_limit_upload", current.speed_limit_upload)
            ),
            clipboard_watch=bool(raw.get("clipboard_watch", current.clipboard_watch)),
        )
        target_settings_store.save_settings(updated)
        logger.info("Migrated legacy settings from %s", legacy_json_path)
        return True
    except Exception as e:
        logger.warning("Failed to migrate legacy settings: %s", e)
        return False


def migrate_legacy_sqlite_downloads(
    legacy_db_path: Path,
    target_download_repo: DownloadRepository,
) -> int:
    """Migrate download records from legacy SQLite table structure to new repository."""
    if not legacy_db_path.exists():
        return 0

    migrated_count = 0
    try:
        conn = sqlite3.connect(legacy_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if legacy 'downloads' table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'"
        )
        if not cursor.fetchone():
            conn.close()
            return 0

        cursor.execute("SELECT * FROM downloads")
        rows = cursor.fetchall()
        for row in rows:
            row_dict = dict(row)
            gid_val = str(row_dict.get("gid", "")).strip()
            if not gid_val:
                continue

            dl_id = DownloadId(f"legacy-{gid_val}")
            name = str(row_dict.get("name", f"Download {gid_val}"))
            total_len = int(row_dict.get("total_length", 0) or 0)
            completed_len = int(row_dict.get("completed_length", 0) or 0)
            state_raw = str(row_dict.get("state", "COMPLETED")).upper()

            try:
                state_enum = DownloadState(state_raw)
            except ValueError:
                state_enum = DownloadState.COMPLETED

            dl = Download(
                gid=Gid(gid_val),
                download_id=dl_id,
                name=name,
                state=state_enum,
                total_length=ByteSize(total_len) if total_len > 0 else None,
                completed_length=ByteSize(completed_len),
                download_speed=BitRate(0),
                upload_speed=BitRate(0),
            )
            target_download_repo.save(dl)
            migrated_count += 1

        conn.close()
        logger.info(
            "Migrated %d legacy downloads from %s", migrated_count, legacy_db_path
        )
    except Exception as e:
        logger.warning("Error migrating legacy database: %s", e)

    return migrated_count
