"""Versioned SQLite Schema Migrations for Shusha."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

type MigrationFn = Callable[[sqlite3.Connection], None]


def migration_v1_initial_schema(conn: sqlite3.Connection) -> None:
    """Initial schema version 1: downloads, files, sources, categories, settings."""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        download_dir TEXT NOT NULL,
        extensions_json TEXT NOT NULL DEFAULT '[]',
        host_patterns_json TEXT NOT NULL DEFAULT '[]',
        icon_name TEXT NOT NULL DEFAULT 'folder'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS downloads (
        download_id TEXT PRIMARY KEY,
        gid TEXT NOT NULL,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        total_length INTEGER,
        completed_length INTEGER NOT NULL DEFAULT 0,
        download_speed INTEGER NOT NULL DEFAULT 0,
        upload_speed INTEGER NOT NULL DEFAULT 0,
        category_id TEXT REFERENCES categories(id) ON DELETE SET NULL,
        dir_path TEXT NOT NULL DEFAULT '',
        is_torrent INTEGER NOT NULL DEFAULT 0,
        is_metalink INTEGER NOT NULL DEFAULT 0,
        error_code INTEGER,
        error_message TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        completed_at TEXT
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_gid ON downloads(gid);")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_downloads_state ON downloads(state);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_downloads_category ON downloads(category_id);"
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS download_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        download_id TEXT NOT NULL REFERENCES downloads(download_id) ON DELETE CASCADE,
        file_index INTEGER NOT NULL,
        path TEXT NOT NULL,
        length INTEGER NOT NULL DEFAULT 0,
        completed_length INTEGER NOT NULL DEFAULT 0,
        selected INTEGER NOT NULL DEFAULT 1
    );
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_download_id ON download_files(download_id);"
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS download_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        download_id TEXT NOT NULL REFERENCES downloads(download_id) ON DELETE CASCADE,
        uri TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'WAITING'
    );
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sources_download_id ON download_sources(download_id);"
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
    );
    """)


def migration_v2_multi_backend_schema(conn: sqlite3.Connection) -> None:
    """Schema version 2: Multi-backend jobs, job_groups, artifacts, credential_references."""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_groups (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'batch',
        total_jobs INTEGER NOT NULL DEFAULT 0,
        completed_jobs INTEGER NOT NULL DEFAULT 0,
        failed_jobs INTEGER NOT NULL DEFAULT 0,
        total_length INTEGER,
        completed_length INTEGER NOT NULL DEFAULT 0,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        backend_id TEXT NOT NULL,
        name TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'QUEUED',
        group_id TEXT REFERENCES job_groups(id) ON DELETE SET NULL,
        source_uri TEXT NOT NULL DEFAULT '',
        category_id TEXT REFERENCES categories(id) ON DELETE SET NULL,
        total_length INTEGER,
        completed_length INTEGER NOT NULL DEFAULT 0,
        download_speed INTEGER NOT NULL DEFAULT 0,
        upload_speed INTEGER NOT NULL DEFAULT 0,
        error_message TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        backend_data_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        started_at TEXT,
        finished_at TEXT
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_backend ON jobs(backend_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_group ON jobs(group_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category_id);")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        kind TEXT NOT NULL DEFAULT 'file',
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        size INTEGER,
        checksum TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        mime_type TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
    );
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_artifacts_job_id ON artifacts(job_id);"
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credential_references (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        store_key TEXT NOT NULL,
        scope TEXT NOT NULL DEFAULT 'domain',
        label TEXT NOT NULL DEFAULT '',
        domain_pattern TEXT,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
    );
    """)


MIGRATIONS: dict[int, MigrationFn] = {
    1: migration_v1_initial_schema,
    2: migration_v2_multi_backend_schema,
}


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply all pending database migrations in a transaction.

    Returns the final schema version number.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version;")
    current_version = cursor.fetchone()[0]

    target_version = max(MIGRATIONS.keys()) if MIGRATIONS else 0

    if current_version < target_version:
        for version in range(current_version + 1, target_version + 1):
            if version in MIGRATIONS:
                migration_fn = MIGRATIONS[version]
                migration_fn(conn)
                cursor.execute(f"PRAGMA user_version = {version};")
                conn.commit()

    return target_version
