"""SQLite implementation of JobRepository (E04-I02)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from shusha.domain.download_source import DownloadSource
from shusha.domain.identifiers import (
    BackendId,
    CategoryId,
    JobId,
    make_backend_id,
    make_category_id,
    make_job_group_id,
    make_job_id,
)
from shusha.domain.job import Job, JobProgress, JobTimestamps
from shusha.domain.states import DownloadState
from shusha.domain.values import BitRate, ByteSize
from shusha.infrastructure.persistence.contracts import JobRepository


class SqliteJobRepository(JobRepository):
    """Stores and queries Job aggregate entities in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, job: Job) -> None:
        """Upsert a Job entity."""
        cursor = self.conn.cursor()
        total_len = (
            job.progress.total_length.bytes if job.progress.total_length else None
        )
        started_str = (
            job.timestamps.started_at.isoformat() if job.timestamps.started_at else None
        )
        finished_str = (
            job.timestamps.finished_at.isoformat()
            if job.timestamps.finished_at
            else None
        )
        created_str = job.timestamps.created_at.isoformat()
        source_uri = job.source.uri.raw_uri if job.source else ""

        cursor.execute(
            """
            INSERT INTO jobs (
                id, backend_id, name, state, group_id, source_uri, category_id,
                total_length, completed_length, download_speed, upload_speed,
                error_message, metadata_json, backend_data_json,
                created_at, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                backend_id = excluded.backend_id,
                name = excluded.name,
                state = excluded.state,
                group_id = excluded.group_id,
                source_uri = excluded.source_uri,
                category_id = excluded.category_id,
                total_length = excluded.total_length,
                completed_length = excluded.completed_length,
                download_speed = excluded.download_speed,
                upload_speed = excluded.upload_speed,
                error_message = excluded.error_message,
                metadata_json = excluded.metadata_json,
                backend_data_json = excluded.backend_data_json,
                started_at = excluded.started_at,
                finished_at = excluded.finished_at;
            """,
            (
                str(job.id),
                str(job.backend_id),
                job.name,
                job.state.value,
                str(job.group_id) if job.group_id else None,
                source_uri,
                str(job.category_id) if job.category_id else None,
                total_len,
                job.progress.completed_length.bytes,
                job.progress.download_speed.bytes_per_sec,
                job.progress.upload_speed.bytes_per_sec,
                job.error_message,
                json.dumps(job.metadata),
                json.dumps(job.backend_data),
                created_str,
                started_str,
                finished_str,
            ),
        )
        self.conn.commit()

    def get(self, job_id: JobId) -> Job | None:
        """Fetch a Job by its ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, backend_id, name, state, group_id, source_uri, category_id,
                   total_length, completed_length, download_speed, upload_speed,
                   error_message, metadata_json, backend_data_json,
                   created_at, started_at, finished_at
            FROM jobs WHERE id = ?;
            """,
            (str(job_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_jobs(
        self,
        state: DownloadState | None = None,
        backend_id: BackendId | None = None,
        category_id: CategoryId | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filters and pagination."""
        cursor = self.conn.cursor()
        conditions: list[str] = []
        params: list[str | int] = []

        if state is not None:
            conditions.append("state = ?")
            params.append(state.value)
        if backend_id is not None:
            conditions.append("backend_id = ?")
            params.append(str(backend_id))
        if category_id is not None:
            conditions.append("category_id = ?")
            params.append(str(category_id))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT id, backend_id, name, state, group_id, source_uri, category_id,
                   total_length, completed_length, download_speed, upload_speed,
                   error_message, metadata_json, backend_data_json,
                   created_at, started_at, finished_at
            FROM jobs {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        return [self._row_to_job(r) for r in cursor.fetchall()]

    def delete(self, job_id: JobId) -> bool:
        """Delete a job by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?;", (str(job_id),))
        self.conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """Return total number of jobs."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs;")
        return cursor.fetchone()[0]

    def _row_to_job(self, row: tuple) -> Job:
        (
            jid,
            bid,
            name,
            state_str,
            gid,
            source_uri,
            cat_id,
            total_len,
            comp_len,
            dl_speed,
            ul_speed,
            err_msg,
            meta_json,
            bdata_json,
            created_str,
            started_str,
            finished_str,
        ) = row

        created_dt = (
            datetime.fromisoformat(created_str) if created_str else datetime.now(UTC)
        )
        started_dt = datetime.fromisoformat(started_str) if started_str else None
        finished_dt = datetime.fromisoformat(finished_str) if finished_str else None

        source = DownloadSource.from_str(source_uri) if source_uri else None

        progress = JobProgress(
            total_length=ByteSize(total_len) if total_len is not None else None,
            completed_length=ByteSize(comp_len or 0),
            download_speed=BitRate(dl_speed or 0),
            upload_speed=BitRate(ul_speed or 0),
        )

        timestamps = JobTimestamps(
            created_at=created_dt,
            started_at=started_dt,
            finished_at=finished_dt,
        )

        return Job(
            id=make_job_id(jid),
            backend_id=make_backend_id(bid),
            name=name,
            state=DownloadState(state_str),
            group_id=make_job_group_id(gid) if gid else None,
            source=source,
            category_id=make_category_id(cat_id) if cat_id else None,
            progress=progress,
            timestamps=timestamps,
            error_message=err_msg,
            metadata=json.loads(meta_json or "{}"),
            backend_data=json.loads(bdata_json or "{}"),
        )
