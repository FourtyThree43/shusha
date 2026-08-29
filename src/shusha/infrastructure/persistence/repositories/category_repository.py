"""
SQLite-backed Category repository for Shusha 2.
"""

import json
import sqlite3

from shusha.domain.category import Category, CategoryRule
from shusha.domain.identifiers import CategoryId
from shusha.infrastructure.persistence.database import DatabaseManager


class CategoryRepository:
    """Repository handling persistence for Category entities."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def _row_to_category(self, row: sqlite3.Row) -> Category:
        exts = json.loads(row["extensions_json"])
        hosts = json.loads(row["host_patterns_json"])
        rule = CategoryRule(extensions=exts, host_patterns=hosts)
        return Category(
            id=CategoryId(row["id"]),
            name=row["name"],
            download_dir=row["download_dir"],
            rule=rule,
            icon_name=row["icon_name"],
        )

    def save(self, category: Category) -> None:
        """Persist or update a Category."""
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO categories (id, name, download_dir, extensions_json, host_patterns_json, icon_name)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    download_dir = excluded.download_dir,
                    extensions_json = excluded.extensions_json,
                    host_patterns_json = excluded.host_patterns_json,
                    icon_name = excluded.icon_name;
                """,
                (
                    str(category.id),
                    category.name,
                    category.download_dir,
                    json.dumps(category.rule.extensions),
                    json.dumps(category.rule.host_patterns),
                    category.icon_name,
                ),
            )

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Fetch category by ID."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM categories WHERE id = ?;", (str(category_id),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_category(row)

    def list_all(self) -> list[Category]:
        """List all configured categories."""
        with self.db_manager.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [self._row_to_category(row) for row in rows]

    def delete(self, category_id: CategoryId) -> bool:
        """Delete category record."""
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?;", (str(category_id),))
            return cursor.rowcount > 0
