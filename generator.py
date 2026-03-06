import random
from typing import List, Tuple

import content_seed as cs
from content_seed import GREET, WISDOM, ANIMAL, STORIES, RARE


def _pick(pool: List[str], recent: set, tries: int = 10) -> str:
    for _ in range(tries):
        item = random.choice(pool)
        if item not in recent:
            return item
    return random.choice(pool)


def _fmt(text: str) -> str:
    return text.strip()


def _animal_vars() -> dict:
    return {
        "dog": random.choice(cs.META["animals"]["dogs"]),
        "cat": random.choice(cs.META["animals"]["cats"]),
    }


def build_message(
    slot: str,
    tasks_lines: List[str],
    quiet: bool,
    recent: set,
) -> Tuple[str, List[str]]:
    greet = _pick(GREET[slot], recent)
    parts = [greet]
    if tasks_lines:
        parts.append("\n".join(tasks_lines))
    if not quiet:
        parts.append(_pick(WISDOM, recent))
        if random.random() < 0.5:
            parts.append(_pick(ANIMAL, recent))
        if random.random() < 0.3:
            parts.append(_pick(STORIES, recent))
        if random.random() < 0.1:
            parts.append(_pick(RARE, recent))
    return "\n\n".join(parts), []
