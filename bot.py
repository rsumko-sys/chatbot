import asyncio
import logging
import sys
from datetime import datetime, timedelta, date
from functools import partial
from typing import Optional
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

# Initialized in main() after config validation
bot: Optional[Bot] = None
dp = Dispatcher()
scheduler = make_scheduler(CFG.tz_name)


def _done_kb(slot: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Виконано",
        callback_data=f"done:{slot}:{date.today().isoformat()}",
    )
    return builder.as_markup()


async def send_slot(slot: str) -> None:
    assert bot is not None
    if db.is_sent(slot):
        return
    recent = db.get_recent_phrases()
    tasks_lines = TASKS.get(slot, [])
    msg, used = build_message(slot, tasks_lines, quiet=False, recent=recent)

    weather_info = get_weather(api_key=CFG.weather_api_key)
    full_msg = f"{msg}\n\n🌤 {weather_info}"

    await bot.send_message(
        chat_id=CFG.target_chat_id,
        text=full_msg,
        reply_markup=_done_kb(slot),
    )
    db.mark_sent(slot)
    for phrase in used:
        db.add_recent_phrase(phrase)

    chase_at = datetime.now(tz=TZ) + timedelta(minutes=CFG.critical_chase_minutes)
    schedule_once(scheduler, chase_at, f"{slot}_chase", partial(chase_slot, slot))


async def chase_slot(slot: str) -> None:
    assert bot is not None
    if db.is_done(slot):
        return
    critical = [t for t in TASKS.get(slot, []) if any(kw in t for kw in CRITICAL_KEYWORDS)]
    if not critical:
        return
    lines = "\n".join(f"⚠️ {t}" for t in critical)
    await bot.send_message(
        chat_id=CFG.target_chat_id,
        text=f"🔔 Нагадування — не забудьте:\n{lines}",
        reply_markup=_done_kb(slot),
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("done:"))
async def on_done(callback: types.CallbackQuery) -> None:
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Невірний формат даних.")
        return
    _, slot, day_str = parts
    if slot not in SLOTS:
        await callback.answer("Невідомий слот.")
        return
    try:
        day = date.fromisoformat(day_str)
    except ValueError:
        await callback.answer("Невірна дата.")
        return
    db.mark_done(slot, day)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Відмічено!")


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Привіт! Я бот Верховини 🏔\n"
        "Надсилаю нагадування тричі на день.\n\n"
        "Команди:\n"
        "/snooze — відкласти нагадування\n"
        "/status — поточний статус за сьогодні"
    )


@dp.message(Command("snooze"))
async def cmd_snooze(message: types.Message) -> None:
    now = datetime.now(tz=TZ)
    hour = now.hour
    if 5 <= hour < 12:
        slot = "morning"
    elif 12 <= hour < 18:
        slot = "day"
    else:
        slot = "evening"
    snooze_at = now + timedelta(minutes=CFG.snooze_minutes_default)
    schedule_once(scheduler, snooze_at, f"{slot}_snooze", partial(send_slot_forced, slot))
    await message.answer(f"🔕 Відкладено на {CFG.snooze_minutes_default} хв.")


async def send_slot_forced(slot: str) -> None:
    assert bot is not None
    recent = db.get_recent_phrases()
    tasks_lines = TASKS.get(slot, [])
    msg, used = build_message(slot, tasks_lines, quiet=True, recent=recent)
    weather_info = get_weather(api_key=CFG.weather_api_key)
    full_msg = f"{msg}\n\n🌤 {weather_info}"
    await bot.send_message(
        chat_id=CFG.target_chat_id,
        text=full_msg,
        reply_markup=_done_kb(slot),
    )
    db.mark_sent(slot)
    for phrase in used:
        db.add_recent_phrase(phrase)


@dp.message(Command("status"))
async def cmd_status(message: types.Message) -> None:
    today = date.today()
    lines = []
    for slot in SLOTS:
        sent = "✅" if db.is_sent(slot, today) else "—"
        done = "✅" if db.is_done(slot, today) else "—"
        lines.append(f"{slot}: надіслано {sent}  виконано {done}")
    await message.answer("\n".join(lines))


async def main():
    global bot

    missing = [name for name, val in [
        ("TELEGRAM_BOT_TOKEN", CFG.bot_token),
        ("TARGET_CHAT_ID", CFG.target_chat_id),
    ] if not val]
    if missing:
        logging.error(
            "Required environment variable(s) not set: %s. "
            "Copy .env.example to .env and fill in your credentials.",
            ", ".join(missing),
        )
        sys.exit(1)

    bot = Bot(token=CFG.bot_token)

    schedule_daily(scheduler, CFG.tz_name, "morning", CFG.morning_at, partial(send_slot, "morning"))
    schedule_daily(scheduler, CFG.tz_name, "day",     CFG.day_at,     partial(send_slot, "day"))
    schedule_daily(scheduler, CFG.tz_name, "evening", CFG.evening_at, partial(send_slot, "evening"))
    scheduler.start()
    logging.info("Бот стартує...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
