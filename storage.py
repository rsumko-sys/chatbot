import sqlite3
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict

SLOTS = ("morning", "day", "evening")

def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

class Storage:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._con = sqlite3.connect(db_path, check_same_thread=False)
        self._migrate()

    def _migrate(self) -> None:
        c = self._con
        c.execute("""
            CREATE TABLE IF NOT EXISTS custom_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot TEXT NOT NULL,
                text TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot TEXT NOT NULL,
                task TEXT NOT NULL,
                done_date TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS recent_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        c.commit()

    def get_custom_tasks(self, slot: str) -> List[str]:
        cur = self._con.execute(
            "SELECT text FROM custom_tasks WHERE slot=? ORDER BY id", (slot,)
        )
        return [row[0] for row in cur.fetchall()]

    def add_task(self, slot: str, text: str) -> None:
        self._con.execute(
            "INSERT INTO custom_tasks (slot, text) VALUES (?, ?)", (slot, text)
        )
        self._con.commit()

    def delete_task(self, slot: str, index: int) -> bool:
        rows = self._con.execute(
            "SELECT id FROM custom_tasks WHERE slot=? ORDER BY id", (slot,)
        ).fetchall()
        if index < 0 or index >= len(rows):
            return False
        self._con.execute("DELETE FROM custom_tasks WHERE id=?", (rows[index][0],))
        self._con.commit()
        return True

    def mark_done(self, slot: str, task: str, dt: date) -> None:
        date_str = dt.isoformat()
        exists = self._con.execute(
            "SELECT 1 FROM completions WHERE slot=? AND task=? AND done_date=?",
            (slot, task, date_str),
        ).fetchone()
        if not exists:
            self._con.execute(
                "INSERT INTO completions (slot, task, done_date) VALUES (?, ?, ?)",
                (slot, task, date_str),
            )
            self._con.commit()

    def is_done(self, slot: str, task: str, dt: date) -> bool:
        row = self._con.execute(
            "SELECT 1 FROM completions WHERE slot=? AND task=? AND done_date=?",
            (slot, task, dt.isoformat()),
        ).fetchone()
        return row is not None

    def get_stats(self, days: int = 7) -> Dict[str, int]:
        cur = self._con.execute(
            """
            SELECT done_date, COUNT(*) as cnt
            FROM completions
            WHERE done_date >= date('now', ?)
            GROUP BY done_date
            ORDER BY done_date DESC
            """,
            (f"-{days} days",),
        )
        return {row[0]: row[1] for row in cur.fetchall()}

    def get_quiet(self) -> bool:
        row = self._con.execute(
            "SELECT value FROM settings WHERE key='quiet'"
        ).fetchone()
        return row is not None and row[0] == "1"

    def set_quiet(self, val: bool) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('quiet', ?)",
            ("1" if val else "0",),
        )
        self._con.commit()

    def get_recent_content(self, n: int = 10) -> set:
        rows = self._con.execute(
            "SELECT content FROM recent_content ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return {row[0] for row in rows}

    def add_recent_content(self, content: str) -> None:
        self._con.execute(
            "INSERT INTO recent_content (content, created_at) VALUES (?, ?)",
            (content, _utc_now_iso()),
        )
        self._con.execute(
            "DELETE FROM recent_content WHERE id NOT IN "
            "(SELECT id FROM recent_content ORDER BY id DESC LIMIT 50)"
        )
        self._con.commit()

