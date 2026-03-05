import sqlite3
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict

SLOTS = ("morning", "day", "evening")

def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_tables()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_log (
                    date TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    sent INTEGER NOT NULL DEFAULT 0,
                    done INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (date, slot)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recent_phrases (
                    phrase TEXT PRIMARY KEY,
                    used_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def mark_sent(self, slot: str, day: Optional[date] = None) -> None:
        d = (day or date.today()).isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO daily_log (date, slot, sent, done) VALUES (?, ?, 1, 0)
                   ON CONFLICT(date, slot) DO UPDATE SET sent=1""",
                (d, slot),
            )
            conn.commit()

    def is_sent(self, slot: str, day: Optional[date] = None) -> bool:
        d = (day or date.today()).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT sent FROM daily_log WHERE date=? AND slot=?", (d, slot)
            ).fetchone()
        return bool(row and row[0])

    def mark_done(self, slot: str, day: Optional[date] = None) -> None:
        d = (day or date.today()).isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO daily_log (date, slot, sent, done) VALUES (?, ?, 0, 1)
                   ON CONFLICT(date, slot) DO UPDATE SET done=1""",
                (d, slot),
            )
            conn.commit()

    def is_done(self, slot: str, day: Optional[date] = None) -> bool:
        d = (day or date.today()).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT done FROM daily_log WHERE date=? AND slot=?", (d, slot)
            ).fetchone()
        return bool(row and row[0])

    def get_recent_phrases(self, n: int = 20) -> set:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT phrase FROM recent_phrases ORDER BY used_at DESC LIMIT ?", (n,)
            ).fetchall()
        return {r[0] for r in rows}

    def add_recent_phrase(self, phrase: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO recent_phrases (phrase, used_at) VALUES (?, ?)
                   ON CONFLICT(phrase) DO UPDATE SET used_at=excluded.used_at""",
                (phrase, _utc_now_iso()),
            )
            conn.commit()
