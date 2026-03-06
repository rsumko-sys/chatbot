import random
from typing import List, Tuple

from content_seed import GREET, WATER, MEDS, WISDOM, ANIMAL, STORIES, RARE


def _pick(pool: List[str], recent: set, tries: int = 10) -> str:
    for _ in range(tries):
        item = random.choice(pool)
        if item not in recent:
            return item
    return random.choice(pool)


def _fmt(text: str) -> str:
    return text.strip()


def build_message(slot: str, tasks_lines: List[str], quiet: bool, recent: set) -> Tuple[str, List[str]]:
    parts = [random.choice(GREET[slot])]
    new_recent: List[str] = []

    if tasks_lines:
        has_water = any("вод" in t for t in tasks_lines)
        has_meds = any("ліки" in t for t in tasks_lines)
        task_block = "\n".join(f"• {t}" for t in tasks_lines)
        parts.append(task_block)
        if has_water:
            parts.append(_fmt(random.choice(WATER)))
        if has_meds:
            parts.append(_fmt(random.choice(MEDS)))

    if not quiet:
        if random.random() < 0.5:
            item = _pick(WISDOM, recent)
            parts.append(_fmt(item))
            new_recent.append(item)
        if random.random() < 0.3:
            item = _pick(ANIMAL, recent)
            parts.append(_fmt(item))
            new_recent.append(item)
        if random.random() < 0.2:
            item = _pick(STORIES, recent)
            parts.append(_fmt(item))
            new_recent.append(item)
        if random.random() < 0.1:
            item = _pick(RARE, recent)
            parts.append(_fmt(item))
            new_recent.append(item)

    msg = "\n\n".join(parts)
    return msg, new_recent
