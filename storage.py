from datetime import datetime

SLOTS = ("morning", "day", "evening")

def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Тут можна додати ініціалізацію бази, якщо потрібно
