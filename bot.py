import asyncio
import logging
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import load_config
from content_seed import TASKS
from generator import build_message
from scheduler import make_scheduler, schedule_daily
from storage import Storage, SLOTS
from weather import get_weather

logging.basicConfig(level=logging.INFO)

CFG = load_config()
TZ = ZoneInfo(CFG.tz_name)

db = Storage(CFG.db_path)


async def send_slot(slot: str, bot: Bot):
    quiet = db.is_quiet()
    custom = db.get_custom_tasks(slot)
    all_tasks = TASKS[slot] + custom
    recent = db.get_recent(slot)
    task_lines = [f"\u2022 {t}" for t in all_tasks]
    msg, _ = build_message(slot, task_lines, quiet, recent)

    weather = get_weather()
    if weather and not weather.startswith("["):
        msg += f"\n\n\U0001f324 {weather}"

    builder = InlineKeyboardBuilder()
    for task in all_tasks:
        builder.button(
            text="\u2705",
            callback_data=f"done:{slot}:{task}",
        )
        builder.button(
            text="\u23ed",
            callback_data=f"skip:{slot}:{task}",
        )
    builder.adjust(2)
    await bot.send_message(
        CFG.target_chat_id,
        msg,
        reply_markup=builder.as_markup(),
    )


async def main():
    bot = Bot(
        token=CFG.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    @dp.message(Command("ping"))
    async def cmd_ping(message: types.Message):
        await message.answer("\U0001f7e2 Живий!")

    @dp.message(Command("morning"))
    async def cmd_morning(message: types.Message):
        await send_slot("morning", bot)

    @dp.message(Command("day"))
    async def cmd_day(message: types.Message):
        await send_slot("day", bot)

    @dp.message(Command("evening"))
    async def cmd_evening(message: types.Message):
        await send_slot("evening", bot)

    @dp.message(Command("quiet"))
    async def cmd_quiet(message: types.Message):
        db.set_quiet(True)
        await message.answer("\U0001f515 Тихий режим увімкнено.")

    @dp.message(Command("normal"))
    async def cmd_normal(message: types.Message):
        db.set_quiet(False)
        await message.answer("\U0001f514 Звичайний режим увімкнено.")

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        stats = db.get_stats(7)
        lines = ["\U0001f4ca Статистика за 7 днів:"]
        for slot in SLOTS:
            s = stats.get(slot, {})
            done = s.get("done", 0)
            skip = s.get("skip", 0)
            lines.append(f"  {slot}: \u2705{done} / \u23ed{skip}")
        await message.answer("\n".join(lines))

    @dp.message(Command("tasks"))
    async def cmd_tasks(message: types.Message):
        lines = []
        for slot in SLOTS:
            custom = db.get_custom_tasks(slot)
            all_t = ", ".join(TASKS[slot] + custom)
            lines.append(f"<b>{slot}</b>: {all_t}")
        await message.answer("\n".join(lines))

    @dp.message(Command("addtask"))
    async def cmd_addtask(message: types.Message):
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3 or parts[1] not in SLOTS:
            await message.answer("Використання: /addtask <slot> <text>")
            return
        db.add_custom_task(parts[1], parts[2])
        await message.answer(f"\u2705 Додано таск у {parts[1]}.")

    @dp.message(Command("deltask"))
    async def cmd_deltask(message: types.Message):
        parts = (message.text or "").split()
        if len(parts) < 3 or parts[1] not in SLOTS:
            await message.answer("Використання: /deltask <slot> <index>")
            return
        try:
            idx = int(parts[2])
        except ValueError:
            await message.answer("Індекс має бути числом.")
            return
        if db.del_custom_task(parts[1], idx):
            await message.answer("\u2705 Таск видалено.")
        else:
            await message.answer("\u274c Таск не знайдено.")

    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery):
        data = callback.data or ""
        parts = data.split(":")
        if len(parts) == 3:
            action, slot, task = parts
            db.log_action(slot, task, action)
            labels = {
                "done": "\u2705 Зроблено",
                "skip": "\u23ed Пропущено",
            }
            label = labels.get(action, action)
            await callback.answer(label)
            if callback.message:
                await callback.message.edit_reply_markup(reply_markup=None)

    async def morning_job():
        await send_slot("morning", bot)

    async def day_job():
        await send_slot("day", bot)

    async def evening_job():
        await send_slot("evening", bot)

    scheduler = make_scheduler(CFG.tz_name)
    schedule_daily(scheduler, CFG.tz_name, "morning", CFG.morning_at, morning_job)
    schedule_daily(scheduler, CFG.tz_name, "day", CFG.day_at, day_job)
    schedule_daily(scheduler, CFG.tz_name, "evening", CFG.evening_at, evening_job)
    scheduler.start()
    logging.info("Бот стартує...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
