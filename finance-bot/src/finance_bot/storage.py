"""SQLite storage for finance records."""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any


class FinanceStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT NOT NULL DEFAULT 'expense',
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    raw_text TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            # Migration: add type column if missing
            try:
                conn.execute("ALTER TABLE expenses ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'")
            except Exception:
                pass
            # Migration: add currency column if missing
            try:
                conn.execute("ALTER TABLE expenses ADD COLUMN currency TEXT NOT NULL DEFAULT 'KZT'")
            except Exception:
                pass

    def add_record(
        self,
        user_id: int,
        record_type: str,  # 'expense' or 'income'
        amount: float,
        category: str,
        description: str,
        raw_text: str,
        currency: str = "KZT",
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO expenses
                   (user_id, type, amount, currency, category, description, raw_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, record_type, amount, currency.upper(), category, description, raw_text,
                 datetime.now().isoformat()),
            )
            return cursor.lastrowid

    def add_expense(self, user_id, amount, category, description, raw_text) -> int:
        return self.add_record(user_id, "expense", amount, category, description, raw_text)

    def _get_records(self, user_id: int, since: str, record_type: str | None = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if record_type:
                rows = conn.execute(
                    """SELECT * FROM expenses
                       WHERE user_id = ? AND created_at >= ? AND type = ?
                       ORDER BY created_at DESC""",
                    (user_id, since, record_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM expenses
                       WHERE user_id = ? AND created_at >= ?
                       ORDER BY created_at DESC""",
                    (user_id, since),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_today(self, user_id: int) -> list[dict[str, Any]]:
        return self._get_records(user_id, date.today().isoformat())

    def get_weekly(self, user_id: int) -> list[dict[str, Any]]:
        since = (date.today() - timedelta(days=7)).isoformat()
        return self._get_records(user_id, since)

    def get_monthly(self, user_id: int) -> list[dict[str, Any]]:
        since = date.today().replace(day=1).isoformat()
        return self._get_records(user_id, since)

    def delete_last(self, user_id: int) -> dict | None:
        """Delete last record, return it or None."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if row:
                conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
                return dict(row)
        return None

    def get_total_by_category(self, records: list[dict]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for r in records:
            cat = r["category"]
            totals[cat] = totals.get(cat, 0) + r["amount"]
        return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))
