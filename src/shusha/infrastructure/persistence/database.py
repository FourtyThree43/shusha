"""
SQLite Database Connection Manager for Shusha 2.
Enforces WAL mode, foreign keys, secure permissions (0600), and automated migrations.
"""

import contextlib
import os
import sqlite3
from collections.abc import Generator
from pathlib import Path

from shusha.infrastructure.persistence.migrations import apply_migrations


class DatabaseManager:
    """Manages SQLite connections and schema lifecycles."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self.file_path: Path | None = (
            Path(db_path) if str(db_path) != ":memory:" else None
        )
        self._initialized = False

    @property
    def connection_target(self) -> str:
        return str(self.file_path) if self.file_path is not None else ":memory:"

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        if self.file_path is not None:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            # Create file with 0600 permissions if not exists
            if not self.file_path.exists():
                self.file_path.touch(mode=0o600, exist_ok=True)
            else:
                with contextlib.suppress(Exception):
                    os.chmod(self.file_path, 0o600)

        with self.get_connection() as conn:
            apply_migrations(conn)

        self._initialized = True

    def get_connection(self) -> sqlite3.Connection:
        """Create a configured SQLite connection."""
        conn = sqlite3.connect(
            self.connection_target,
            timeout=10.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.file_path is not None:
            conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    @contextlib.contextmanager
    def session(self) -> Generator[sqlite3.Connection]:
        """Context manager providing an active database connection with migration check."""
        self._ensure_initialized()
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextlib.contextmanager
    def transaction(self) -> Generator[sqlite3.Connection]:
        """Context manager providing an atomic database transaction with auto-commit/rollback."""
        self._ensure_initialized()
        conn = self.get_connection()
        try:
            with conn:
                yield conn
        finally:
            conn.close()
