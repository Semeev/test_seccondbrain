"""SQLite storage for finance records."""

import sqlite3
from datetime import datetime, date
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
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    raw_text TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    def add_expense(
        self,
        user_id: int,
        amount: float,
        category: str,
        description: str,
        raw_text: str,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO expenses
                   (user_id, amount, category, description, raw_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, amount, category, description, raw_text,
                 datetime.now().isoformat()),
            )
            return cursor.lastrowid

    def get_weekly(self, user_id: int) -> list[dict[str, Any]]:
        from datetime import timedelta
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM expenses
                   WHERE user_id = ? AND created_at >= ?
                   ORDER BY created_at DESC""",
                (user_id, week_ago),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_monthly(self, user_id: int) -> list[dict[str, Any]]:
        month_start = date.today().replace(day=1).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM expenses
                   WHERE user_id = ? AND created_at >= ?
                   ORDER BY created_at DESC""",
                (user_id, month_start),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_today(self, user_id: int) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM expenses
                   WHERE user_id = ? AND created_at >= ?
                   ORDER BY created_at DESC""",
                (user_id, today),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_total_by_category(self, records: list[dict]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for r in records:
            cat = r["category"]
            totals[cat] = totals.get(cat, 0) + r["amount"]
        return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))
