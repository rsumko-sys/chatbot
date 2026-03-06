import sqlite3
from datetime import datetime
from typing import List, Dict

SLOTS = ("morning", "day", "evening")


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot TEXT NOT NULL,
                    task TEXT NOT NULL,
                    action TEXT NOT NULL,
                    ts TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_tasks (
                    slot TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    PRIMARY KEY (slot, idx)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

    def log_action(self, slot: str, task: str, action: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO log (slot, task, action, ts) VALUES (?, ?, ?, ?)",
                (slot, task, action, _utc_now_iso()),
            )
            conn.commit()

    def get_stats(self, days: int = 7) -> Dict[str, Dict[str, int]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT slot, action, COUNT(*) FROM log "
                "WHERE ts >= datetime('now', ?) "
                "GROUP BY slot, action",
                (f"-{days} days",),
            ).fetchall()
        stats: Dict[str, Dict[str, int]] = {}
        for slot, action, count in rows:
            stats.setdefault(slot, {})[action] = count
        return stats

    def get_custom_tasks(self, slot: str) -> List[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT text FROM custom_tasks WHERE slot = ? ORDER BY idx",
                (slot,),
            ).fetchall()
        return [r[0] for r in rows]

    def add_custom_task(self, slot: str, text: str) -> None:
        with self._conn() as conn:
            max_idx = conn.execute(
                "SELECT COALESCE(MAX(idx), -1) FROM custom_tasks WHERE slot = ?",
                (slot,),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO custom_tasks (slot, idx, text) VALUES (?, ?, ?)",
                (slot, max_idx + 1, text),
            )
            conn.commit()

    def del_custom_task(self, slot: str, idx: int) -> bool:
        with self._conn() as conn:
            rows_affected = conn.execute(
                "DELETE FROM custom_tasks WHERE slot = ? AND idx = ?",
                (slot, idx),
            ).rowcount
            conn.commit()
        return rows_affected > 0

    def set_quiet(self, quiet: bool) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('quiet', ?)",
                ("1" if quiet else "0",),
            )
            conn.commit()

    def is_quiet(self) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'quiet'"
            ).fetchone()
        return row is not None and row[0] == "1"

    def get_recent(self, key: str) -> set:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT task FROM log WHERE slot = ? "
                "AND ts >= datetime('now', '-48 hours')",
                (key,),
            ).fetchall()
        return {r[0] for r in rows}
