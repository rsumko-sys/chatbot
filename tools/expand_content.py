import random
from content_seed import META

DOGS = META["animals"]["dogs"]
CATS = META["animals"]["cats"]

OPENERS = ["У горах день починається тихо.", "Добрий день починається з води і тиші."]
NUGGETS = ["Каміння пам’ятає все.", "Гуцул не спішить — він просто знає куди йде."]
ANIMALS = ["Белла сьогодні перевірила територію.", "Фріда дивиться на павлінів з підозрою."]
STORY_TEMPLATES = ["[персонаж] одного разу вирішив що [абсурдна ідея], але [інший персонаж] мав іншу думку."]

def gen_wisdom(n=1000):
    wisdoms = []
    for _ in range(n):
        wisdoms.append(random.choice(OPENERS) + " " + random.choice(NUGGETS))
    return wisdoms

def gen_stories(n=300):
    stories = []
    for _ in range(n):
        stories.append(random.choice(STORY_TEMPLATES))
    return stories

if __name__ == "__main__":
    wisdoms = gen_wisdom()
    stories = gen_stories()
    print("STORIES_SAMPLE:", stories[:5])
