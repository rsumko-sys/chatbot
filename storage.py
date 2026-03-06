import sqlite3
from datetime import datetime, date
from typing import Optional

SLOTS = ("morning", "day", "evening")


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    message_hash TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sent_messages_slot_date
                ON sent_messages (slot, sent_at)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    completed_date TEXT NOT NULL
                )
            """)
            conn.commit()

    def record_sent(self, slot: str, message_hash: Optional[str] = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sent_messages (slot, sent_at, message_hash) VALUES (?, ?, ?)",
                (slot, _utc_now_iso(), message_hash),
            )
            conn.commit()

    def was_sent_today(self, slot: str) -> bool:
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM sent_messages WHERE slot = ? AND sent_at LIKE ? LIMIT 1",
                (slot, f"{today}%"),
            ).fetchone()
        return row is not None

    def record_completion(self, slot: str) -> None:
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO task_completions (slot, completed_at, completed_date) VALUES (?, ?, ?)",
                (slot, _utc_now_iso(), today),
            )
            conn.commit()
