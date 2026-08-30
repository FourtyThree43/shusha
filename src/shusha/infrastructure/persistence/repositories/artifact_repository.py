"""SQLite implementation of ArtifactRepository (E04-I02)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from shusha.domain.artifact import Artifact, ArtifactKind, ArtifactStatus
from shusha.domain.identifiers import ArtifactId, JobId, make_artifact_id, make_job_id
from shusha.domain.values import ByteSize, Checksum
from shusha.infrastructure.persistence.contracts import ArtifactRepository


class SqliteArtifactRepository(ArtifactRepository):
    """Stores and queries execution output artifacts in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, artifact: Artifact) -> None:
        """Upsert an Artifact entity."""
        cursor = self.conn.cursor()
        size_val = artifact.size.bytes if artifact.size else None
        checksum_val = (
            f"{artifact.checksum.algorithm}:{artifact.checksum.digest}"
            if artifact.checksum
            else None
        )

        cursor.execute(
            """
            INSERT INTO artifacts (
                id, job_id, kind, name, path, size, checksum, status, mime_type, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                job_id = excluded.job_id,
                kind = excluded.kind,
                name = excluded.name,
                path = excluded.path,
                size = excluded.size,
                checksum = excluded.checksum,
                status = excluded.status,
                mime_type = excluded.mime_type,
                metadata_json = excluded.metadata_json;
            """,
            (
                str(artifact.id),
                str(artifact.job_id),
                artifact.kind.value,
                artifact.name,
                str(artifact.path),
                size_val,
                checksum_val,
                artifact.status.value,
                artifact.mime_type,
                json.dumps(artifact.metadata),
            ),
        )
        self.conn.commit()

    def get(self, artifact_id: ArtifactId) -> Artifact | None:
        """Fetch an artifact by its ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, job_id, kind, name, path, size, checksum, status, mime_type, metadata_json
            FROM artifacts WHERE id = ?;
            """,
            (str(artifact_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_artifact(row)

    def list_for_job(self, job_id: JobId) -> list[Artifact]:
        """List all artifacts associated with a given Job."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, job_id, kind, name, path, size, checksum, status, mime_type, metadata_json
            FROM artifacts WHERE job_id = ?
            ORDER BY created_at ASC;
            """,
            (str(job_id),),
        )
        return [self._row_to_artifact(r) for r in cursor.fetchall()]

    def delete(self, artifact_id: ArtifactId) -> bool:
        """Delete an artifact record."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM artifacts WHERE id = ?;", (str(artifact_id),))
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_artifact(self, row: tuple) -> Artifact:
        (
            aid,
            jid,
            kind_str,
            name,
            path_str,
            size_val,
            chk_val,
            status_str,
            mime,
            meta_json,
        ) = row

        checksum_obj: Checksum | None = None
        if chk_val and ":" in chk_val:
            algo, digest = chk_val.split(":", 1)
            checksum_obj = Checksum(algorithm=algo, digest=digest)

        return Artifact(
            id=make_artifact_id(aid),
            job_id=make_job_id(jid),
            kind=ArtifactKind(kind_str),
            name=name,
            path=Path(path_str),
            size=ByteSize(size_val) if size_val is not None else None,
            checksum=checksum_obj,
            status=ArtifactStatus(status_str),
            mime_type=mime,
            metadata=json.loads(meta_json or "{}"),
        )
