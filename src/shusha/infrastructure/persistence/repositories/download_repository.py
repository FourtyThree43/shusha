"""
SQLite-backed Download repository for Shusha 2.
Translates database rows directly into immutable domain Download aggregates.
"""

import sqlite3

from shusha.domain.download import Download
from shusha.domain.download_file import DownloadFile
from shusha.domain.download_source import DownloadSource, SourceStatus
from shusha.domain.identifiers import CategoryId, DownloadId, Gid
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize, Duration, Uri
from shusha.infrastructure.persistence.database import DatabaseManager


class DownloadRepository:
    """Repository handling persistence for Download aggregates."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def _row_to_download(
        self, row: sqlite3.Row, files: list[DownloadFile], sources: list[DownloadSource]
    ) -> Download:
        gid = Gid(row["gid"])
        download_id = DownloadId(row["download_id"])
        state = DownloadState(row["state"])
        total_len_raw = row["total_length"]
        total_length = ByteSize(total_len_raw) if total_len_raw is not None else None
        completed_length = ByteSize(row["completed_length"])
        download_speed = BitRate(row["download_speed"])
        upload_speed = BitRate(row["upload_speed"])
        eta = Duration.calculate_eta(completed_length, total_length, download_speed)
        cat_id_raw = row["category_id"]
        category_id = CategoryId(cat_id_raw) if cat_id_raw else None

        return Download(
            gid=gid,
            download_id=download_id,
            name=row["name"],
            state=state,
            total_length=total_length,
            completed_length=completed_length,
            download_speed=download_speed,
            upload_speed=upload_speed,
            eta=eta,
            files=files,
            sources=sources,
            category_id=category_id,
            error_code=row["error_code"],
            error_message=row["error_message"],
            dir_path=row["dir_path"],
            is_torrent=bool(row["is_torrent"]),
            is_metalink=bool(row["is_metalink"]),
        )

    def _fetch_files_and_sources(
        self, conn: sqlite3.Connection, download_id: str
    ) -> tuple[list[DownloadFile], list[DownloadSource]]:
        # Fetch files
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM download_files WHERE download_id = ? ORDER BY file_index ASC;",
            (download_id,),
        )
        file_rows = cursor.fetchall()
        files: list[DownloadFile] = []
        for f_row in file_rows:
            files.append(
                DownloadFile(
                    index=f_row["file_index"],
                    path=f_row["path"],
                    length=ByteSize(f_row["length"]),
                    completed_length=ByteSize(f_row["completed_length"]),
                    selected=bool(f_row["selected"]),
                    uris=[],
                )
            )

        # Fetch sources
        cursor.execute(
            "SELECT * FROM download_sources WHERE download_id = ?;",
            (download_id,),
        )
        source_rows = cursor.fetchall()
        sources: list[DownloadSource] = []
        for s_row in source_rows:
            try:
                status = SourceStatus(s_row["status"].upper())
            except ValueError:
                status = SourceStatus.WAITING
            sources.append(
                DownloadSource(
                    uri=Uri.parse(s_row["uri"]),
                    status=status,
                )
            )

        return files, sources

    def save(self, download: Download) -> None:
        """Persist or update a Download aggregate along with its files and sources."""
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO downloads (
                    download_id, gid, name, state, total_length, completed_length,
                    download_speed, upload_speed, category_id, dir_path, is_torrent,
                    is_metalink, error_code, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(download_id) DO UPDATE SET
                    gid = excluded.gid,
                    name = excluded.name,
                    state = excluded.state,
                    total_length = excluded.total_length,
                    completed_length = excluded.completed_length,
                    download_speed = excluded.download_speed,
                    upload_speed = excluded.upload_speed,
                    category_id = excluded.category_id,
                    dir_path = excluded.dir_path,
                    is_torrent = excluded.is_torrent,
                    is_metalink = excluded.is_metalink,
                    error_code = excluded.error_code,
                    error_message = excluded.error_message;
                """,
                (
                    str(download.download_id),
                    str(download.gid),
                    download.name,
                    download.state.value,
                    download.total_length.bytes if download.total_length else None,
                    download.completed_length.bytes,
                    download.download_speed.bytes_per_sec,
                    download.upload_speed.bytes_per_sec,
                    str(download.category_id) if download.category_id else None,
                    download.dir_path,
                    1 if download.is_torrent else 0,
                    1 if download.is_metalink else 0,
                    download.error_code,
                    download.error_message,
                ),
            )

            # Update files
            cursor.execute(
                "DELETE FROM download_files WHERE download_id = ?;",
                (str(download.download_id),),
            )
            for f in download.files:
                cursor.execute(
                    """
                    INSERT INTO download_files (download_id, file_index, path, length, completed_length, selected)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        str(download.download_id),
                        f.index,
                        f.path,
                        f.length.bytes,
                        f.completed_length.bytes,
                        1 if f.selected else 0,
                    ),
                )

            # Update sources
            cursor.execute(
                "DELETE FROM download_sources WHERE download_id = ?;",
                (str(download.download_id),),
            )
            for s in download.sources:
                cursor.execute(
                    """
                    INSERT INTO download_sources (download_id, uri, status)
                    VALUES (?, ?, ?);
                    """,
                    (
                        str(download.download_id),
                        s.uri.raw_uri,
                        s.status.value,
                    ),
                )

    def get_by_id(self, download_id: DownloadId) -> Download | None:
        """Fetch download by ID."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE download_id = ?;", (str(download_id),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            files, sources = self._fetch_files_and_sources(conn, str(download_id))
            return self._row_to_download(row, files, sources)

    def get_by_gid(self, gid: Gid) -> Download | None:
        """Fetch download by aria2 GID."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads WHERE gid = ?;", (str(gid),))
            row = cursor.fetchone()
            if not row:
                return None
            files, sources = self._fetch_files_and_sources(conn, row["download_id"])
            return self._row_to_download(row, files, sources)

    def list_all(self) -> list[Download]:
        """List all downloads in database."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            downloads: list[Download] = []
            for row in rows:
                files, sources = self._fetch_files_and_sources(conn, row["download_id"])
                downloads.append(self._row_to_download(row, files, sources))
            return downloads

    def list_by_state(self, state: DownloadState) -> list[Download]:
        """Filter downloads by state."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE state = ? ORDER BY created_at DESC;",
                (state.value,),
            )
            rows = cursor.fetchall()
            downloads: list[Download] = []
            for row in rows:
                files, sources = self._fetch_files_and_sources(conn, row["download_id"])
                downloads.append(self._row_to_download(row, files, sources))
            return downloads

    def list_by_category(self, category_id: CategoryId) -> list[Download]:
        """Filter downloads by category."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE category_id = ? ORDER BY created_at DESC;",
                (str(category_id),),
            )
            rows = cursor.fetchall()
            downloads: list[Download] = []
            for row in rows:
                files, sources = self._fetch_files_and_sources(conn, row["download_id"])
                downloads.append(self._row_to_download(row, files, sources))
            return downloads

    def delete(self, download_id: DownloadId) -> bool:
        """Delete download record and cascaded files/sources."""
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM downloads WHERE download_id = ?;", (str(download_id),)
            )
            return cursor.rowcount > 0

    def search(self, query: str) -> list[Download]:
        """Search downloads by filename or directory."""
        q = f"%{query.strip()}%"
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM downloads WHERE name LIKE ? OR dir_path LIKE ? ORDER BY created_at DESC;",
                (q, q),
            )
            rows = cursor.fetchall()
            downloads: list[Download] = []
            for row in rows:
                files, sources = self._fetch_files_and_sources(conn, row["download_id"])
                downloads.append(self._row_to_download(row, files, sources))
            return downloads
