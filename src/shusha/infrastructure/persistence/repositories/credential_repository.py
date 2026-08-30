"""SQLite implementation of CredentialRepositoryProtocol (E04-I02)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from shusha.domain.credentials import (
    CredentialKind,
    CredentialReference,
    CredentialScope,
)
from shusha.domain.identifiers import CredentialId, make_credential_id
from shusha.infrastructure.persistence.contracts import CredentialRepositoryProtocol


class SqliteCredentialRepository(CredentialRepositoryProtocol):
    """Stores credential references (not plaintext secrets) in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, credential: CredentialReference) -> None:
        """Upsert a CredentialReference."""
        cursor = self.conn.cursor()
        created_str = credential.created_at.isoformat()

        cursor.execute(
            """
            INSERT INTO credential_references (
                id, kind, store_key, scope, label, domain_pattern, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                kind = excluded.kind,
                store_key = excluded.store_key,
                scope = excluded.scope,
                label = excluded.label,
                domain_pattern = excluded.domain_pattern,
                description = excluded.description;
            """,
            (
                str(credential.id),
                credential.kind.value,
                credential.store_key,
                credential.scope.value,
                credential.label,
                credential.domain_pattern,
                credential.description,
                created_str,
            ),
        )
        self.conn.commit()

    def get(self, credential_id: CredentialId) -> CredentialReference | None:
        """Fetch a CredentialReference by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, kind, store_key, scope, label, domain_pattern, description, created_at
            FROM credential_references WHERE id = ?;
            """,
            (str(credential_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_cred(row)

    def list_all(self) -> list[CredentialReference]:
        """List all CredentialReferences."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, kind, store_key, scope, label, domain_pattern, description, created_at
            FROM credential_references ORDER BY created_at DESC;
            """
        )
        return [self._row_to_cred(r) for r in cursor.fetchall()]

    def delete(self, credential_id: CredentialId) -> bool:
        """Delete a CredentialReference."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM credential_references WHERE id = ?;", (str(credential_id),)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_cred(self, row: tuple) -> CredentialReference:
        (
            cid,
            kind_str,
            key,
            scope_str,
            label,
            dom_pattern,
            desc,
            created_str,
        ) = row

        created_dt = (
            datetime.fromisoformat(created_str) if created_str else datetime.now(UTC)
        )

        return CredentialReference(
            id=make_credential_id(cid),
            kind=CredentialKind(kind_str),
            store_key=key,
            scope=CredentialScope(scope_str),
            label=label,
            domain_pattern=dom_pattern,
            description=desc,
            created_at=created_dt,
        )
