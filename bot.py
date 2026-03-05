import asyncio
import logging
from zoneinfo import ZoneInfo

from config import load_config
from storage import Storage
from weather import get_weather

logging.basicConfig(level=logging.INFO)

CFG = load_config()
TZ = ZoneInfo(CFG.tz_name)

db = Storage(CFG.db_path)

# ...existing code...

async def main():
    # ...existing code...
    # Приклад використання погодного API
    print(get_weather())
    pass

if __name__ == "__main__":
    asyncio.run(main())
print("Бот стартує...")
