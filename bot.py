import asyncio
import logging
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import load_config
from storage import Storage, SLOTS
from content_seed import TASKS, CRITICAL_KEYWORDS, META
from generator import build_message
from scheduler import make_scheduler, schedule_daily, schedule_once
from weather import get_weather

logging.basicConfig(level=logging.INFO)

CFG = load_config()
TZ = ZoneInfo(CFG.tz_name)

db = Storage(CFG.db_path)

# ...existing code...

async def main():
    # ...existing code...
    # Приклад використання погодного API
    print(get_weather(api_key=CFG.openweather_api_key))
    pass

if __name__ == "__main__":
    asyncio.run(main())
print("Бот стартує...")
