"""SQLite implementation of JobGroupRepository (E04-I02)."""

from __future__ import annotations

import json
import sqlite3

from shusha.domain.identifiers import JobGroupId, JobId, make_job_group_id, make_job_id
from shusha.domain.job_group import JobGroup, JobGroupKind
from shusha.domain.values import ByteSize
from shusha.infrastructure.persistence.contracts import JobGroupRepository


class SqliteJobGroupRepository(JobGroupRepository):
    """Stores and queries JobGroup batches and playlists in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, group: JobGroup) -> None:
        """Upsert a JobGroup entity."""
        cursor = self.conn.cursor()
        total_len = group.total_length.bytes if group.total_length else None

        cursor.execute(
            """
            INSERT INTO job_groups (
                id, name, kind, total_jobs, completed_jobs, failed_jobs,
                total_length, completed_length, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                kind = excluded.kind,
                total_jobs = excluded.total_jobs,
                completed_jobs = excluded.completed_jobs,
                failed_jobs = excluded.failed_jobs,
                total_length = excluded.total_length,
                completed_length = excluded.completed_length,
                metadata_json = excluded.metadata_json;
            """,
            (
                str(group.id),
                group.name,
                group.kind.value,
                group.total_jobs,
                group.completed_jobs,
                group.failed_jobs,
                total_len,
                group.completed_length.bytes,
                json.dumps(group.metadata),
            ),
        )
        self.conn.commit()

    def get(self, group_id: JobGroupId) -> JobGroup | None:
        """Fetch a JobGroup by ID and hydrate its constituent job IDs."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, name, kind, total_jobs, completed_jobs, failed_jobs,
                   total_length, completed_length, metadata_json
            FROM job_groups WHERE id = ?;
            """,
            (str(group_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Fetch child job IDs
        cursor.execute(
            "SELECT id FROM jobs WHERE group_id = ? ORDER BY created_at ASC;",
            (str(group_id),),
        )
        job_ids = tuple(make_job_id(r[0]) for r in cursor.fetchall())

        return self._row_to_group(row, job_ids)

    def list_groups(self) -> list[JobGroup]:
        """List all JobGroups."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, name, kind, total_jobs, completed_jobs, failed_jobs,
                   total_length, completed_length, metadata_json
            FROM job_groups ORDER BY created_at DESC;
            """
        )
        rows = cursor.fetchall()
        result: list[JobGroup] = []
        for r in rows:
            cursor.execute(
                "SELECT id FROM jobs WHERE group_id = ? ORDER BY created_at ASC;",
                (r[0],),
            )
            job_ids = tuple(make_job_id(jr[0]) for jr in cursor.fetchall())
            result.append(self._row_to_group(r, job_ids))
        return result

    def delete(self, group_id: JobGroupId) -> bool:
        """Delete a JobGroup record."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM job_groups WHERE id = ?;", (str(group_id),))
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_group(self, row: tuple, job_ids: tuple[JobId, ...] = ()) -> JobGroup:
        (
            gid,
            name,
            kind_str,
            tot_jobs,
            comp_jobs,
            fail_jobs,
            tot_len,
            comp_len,
            meta_json,
        ) = row

        return JobGroup(
            id=make_job_group_id(gid),
            name=name,
            kind=JobGroupKind(kind_str),
            job_ids=job_ids,
            total_jobs=tot_jobs,
            completed_jobs=comp_jobs,
            failed_jobs=fail_jobs,
            total_length=ByteSize(tot_len) if tot_len is not None else None,
            completed_length=ByteSize(comp_len or 0),
            metadata=json.loads(meta_json or "{}"),
        )
