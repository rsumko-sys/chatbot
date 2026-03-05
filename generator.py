import random
from datetime import datetime
from typing import List, Dict, Tuple

from content_seed import META, GREET, WATER, MEDS, WISDOM, ANIMAL, STORIES, RARE

def _pick(pool: List[str], recent: set, tries: int = 10) -> str:
    for _ in range(tries):
        choice = random.choice(pool)
        if choice not in recent:
            return choice
    return random.choice(pool)

def _fmt(text: str) -> str:
    return text.strip()

def _animal_vars() -> Dict[str, str]:
    return {"dog": random.choice(META["animals"]["dogs"]), "cat": random.choice(META["animals"]["cats"])}

def build_message(slot: str, tasks_lines: List[str], quiet: bool, recent: set) -> Tuple[str, List[str]]:
    used: List[str] = []
    parts: List[str] = []

    greet = _pick(GREET.get(slot, GREET["morning"]), recent)
    parts.append(_fmt(greet))
    used.append(greet)

    if tasks_lines:
        parts.append("\n".join(f"• {t}" for t in tasks_lines))

    if not quiet:
        wisdom = _pick(WISDOM, recent)
        parts.append(_fmt(wisdom))
        used.append(wisdom)

        r = random.random()
        if r < 0.4:
            story = _pick(STORIES, recent)
            parts.append(_fmt(story))
            used.append(story)
        elif r < 0.6:
            rare = _pick(RARE, recent)
            parts.append(_fmt(rare))
            used.append(rare)

    msg = "\n\n".join(parts)
    return msg, used
