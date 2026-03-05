import random
from typing import List, Dict, Tuple

from content_seed import META, GREET, WATER, MEDS, WISDOM, ANIMAL, STORIES, RARE

_RARE_CONTENT_PROBABILITY = 0.15
_REMINDER_PROBABILITY = 0.5


def _pick(pool: List[str], recent: set, tries: int = 10) -> str:
    for _ in range(tries):
        item = random.choice(pool)
        if item not in recent:
            return item
    return random.choice(pool)


def _fmt(text: str) -> str:
    return text.strip()


def _animal_vars() -> Dict[str, str]:
    return {
        "dog": random.choice(META["animals"]["dogs"]),
        "cat": random.choice(META["animals"]["cats"]),
    }


def build_message(
    slot: str,
    tasks_lines: List[str],
    quiet: bool,
    recent: set,
) -> Tuple[str, List[str]]:
    used: List[str] = []

    greeting = _pick(GREET[slot], recent)
    used.append(greeting)
    parts = [_fmt(greeting)]

    if not quiet:
        # Occasionally use rare content; otherwise pick from stories/animals/wisdom
        if random.random() < _RARE_CONTENT_PROBABILITY:
            content_pool = RARE
        else:
            content_pool = random.choice([STORIES, ANIMAL, WISDOM])
        content = _pick(content_pool, recent)
        used.append(content)
        parts.append(_fmt(content))

        # Add water or meds reminder with some probability
        if random.random() < _REMINDER_PROBABILITY:
            reminder = _pick(WATER + MEDS, recent)
            used.append(reminder)
            parts.append(_fmt(reminder))

    if tasks_lines:
        parts.append("")
        parts.extend(tasks_lines)

    return "\n".join(parts), used
