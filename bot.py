import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import load_config
from content_seed import CRITICAL_KEYWORDS, META, TASKS
from generator import build_message
from scheduler import make_scheduler, schedule_daily, schedule_once
from storage import SLOTS, Storage
from weather import get_weather

logging.basicConfig(level=logging.INFO)

CFG = load_config()
TZ = ZoneInfo(CFG.tz_name)

db = Storage(CFG.db_path)


async def send_slot_message(bot: Bot, slot: str) -> None:
    tasks_lines = TASKS.get(slot, [])
    quiet = False
    recent: set = set()
    msg, _ = build_message(slot, tasks_lines, quiet, recent)
    weather_info = get_weather()
    full_msg = f"{msg}\n\n{weather_info}"

    critical = [t for t in tasks_lines if any(k in t for k in CRITICAL_KEYWORDS)]
    animals = META["animals"]
    logging.info("Sending %s message. Critical tasks: %s. Animals: %s", slot, critical, animals)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Виконано", callback_data=f"done:{slot}")
    builder.button(text="⏰ Нагадати пізніше", callback_data=f"snooze:{slot}")

    await bot.send_message(
        chat_id=CFG.target_chat_id,
        text=full_msg,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML,
    )
    db.record_sent(slot)


async def main() -> None:
    bot = Bot(token=CFG.bot_token)
    dp = Dispatcher()
    scheduler = make_scheduler(CFG.tz_name)

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        await message.answer("Бот активний! Нагадування будуть приходити за розкладом.")

    @dp.message(Command("status"))
    async def cmd_status(message: types.Message) -> None:
        now = datetime.now(TZ)
        await message.answer(
            f"Статус: активний\nЧас: {now.strftime('%H:%M %d.%m.%Y')}\n"
            f"Часовий пояс: {CFG.tz_name}"
        )

    @dp.callback_query(lambda c: c.data and c.data.startswith("done:"))
    async def handle_done(callback: types.CallbackQuery) -> None:
        slot = callback.data.split(":")[1]
        db.record_completion(slot)
        await callback.answer(f"✅ Задачі за {slot} відмічено виконаними!")
        await callback.message.edit_reply_markup(reply_markup=None)

    @dp.callback_query(lambda c: c.data and c.data.startswith("snooze:"))
    async def handle_snooze(callback: types.CallbackQuery) -> None:
        slot = callback.data.split(":")[1]
        snooze_minutes = CFG.snooze_minutes_default
        run_at = datetime.now(TZ) + timedelta(minutes=snooze_minutes)
        job_id = f"snooze_{slot}_{int(run_at.timestamp())}"
        schedule_once(scheduler, run_at, job_id, partial(send_slot_message, bot, slot))
        await callback.answer(f"⏰ Нагадую через {snooze_minutes} хвилин.")
        await callback.message.edit_reply_markup(reply_markup=None)

    slot_times = [(SLOTS[0], CFG.morning_at), (SLOTS[1], CFG.day_at), (SLOTS[2], CFG.evening_at)]
    for slot, at_time in slot_times:
        schedule_daily(scheduler, CFG.tz_name, slot, at_time, partial(send_slot_message, bot, slot))

    scheduler.start()
    logging.info("Бот стартує...")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
