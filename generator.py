import random
from datetime import datetime
from typing import List, Dict, Tuple

from content_seed import META, GREET, WATER, MEDS, WISDOM, ANIMAL, STORIES, RARE

def _pick(pool: List[str], recent: set, tries: int = 10) -> str:
    # ...existing code...
    return random.choice(pool)

def _fmt(text: str) -> str:
    return text.strip()

def _animal_vars() -> Dict[str, str]:
    return {"dog": random.choice(META["animals"]["dogs"]), "cat": random.choice(META["animals"]["cats"])}

def build_message(slot: str, tasks_lines: List[str], quiet: bool, recent: set) -> Tuple[str, List[str]]:
    # ...existing code...
    msg = random.choice(GREET[slot]) + "\n" + "\n".join(tasks_lines)
    return msg, []
