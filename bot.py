import asyncio
import logging
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F, types
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
bot = Bot(token=CFG.bot_token)
dp = Dispatcher()

_scheduler = None


def _today() -> date:
    return datetime.now(TZ).date()


def _get_tasks(slot: str) -> list[str]:
    custom = db.get_custom_tasks(slot)
    return custom if custom else list(TASKS[slot])


def _make_task_keyboard(slot: str, tasks: list[str]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, task in enumerate(tasks):
        status = "✅" if db.is_done(slot, task, _today()) else "☐"
        builder.button(text=f"{status} {task}", callback_data=f"done|{slot}|{i}")
    builder.button(text="⏰ Нагадай", callback_data=f"snooze|{slot}")
    builder.adjust(1)
    return builder.as_markup()


async def _send_slot(slot: str, chat_id: str | None = None) -> None:
    cid = chat_id or CFG.target_chat_id
    tasks = _get_tasks(slot)
    recent = db.get_recent_content()
    quiet = db.get_quiet()
    task_lines = [f"☐ {t}" for t in tasks]

    msg, used = build_message(slot, task_lines, quiet, recent)

    weather_text = get_weather()
    if weather_text and not weather_text.startswith("["):
        msg = msg + "\n\n" + weather_text

    for content in used:
        db.add_recent_content(content)

    kb = _make_task_keyboard(slot, tasks)
    await bot.send_message(cid, msg, reply_markup=kb, parse_mode=ParseMode.HTML)

    if _scheduler is not None:
        run_at = datetime.now(TZ) + timedelta(minutes=CFG.critical_chase_minutes)
        for i, task in enumerate(tasks):
            if any(kw in task for kw in CRITICAL_KEYWORDS):
                job_id = f"chase|{slot}|{i}|{_today().isoformat()}"

                async def _chase_job(s: str = slot, t: str = task, c: str = cid) -> None:
                    await _chase_critical(s, t, c)

                schedule_once(_scheduler, run_at, job_id, _chase_job)


async def _chase_critical(slot: str, task: str, chat_id: str) -> None:
    if db.is_done(slot, task, _today()):
        return
    tasks = _get_tasks(slot)
    try:
        idx = tasks.index(task)
    except ValueError:
        idx = 0
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Зроблено", callback_data=f"done|{slot}|{idx}")
    await bot.send_message(
        chat_id,
        f"⚠️ Критична задача не виконана: <b>{task}</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML,
    )


# ── Commands ────────────────────────────────────────────────────────────────

@dp.message(Command("ping"))
async def cmd_ping(message: types.Message) -> None:
    await message.answer("🤖 живий")


@dp.message(Command("morning"))
async def cmd_morning(message: types.Message) -> None:
    await _send_slot("morning", str(message.chat.id))


@dp.message(Command("day"))
async def cmd_day(message: types.Message) -> None:
    await _send_slot("day", str(message.chat.id))


@dp.message(Command("evening"))
async def cmd_evening(message: types.Message) -> None:
    await _send_slot("evening", str(message.chat.id))


@dp.message(Command("quiet"))
async def cmd_quiet(message: types.Message) -> None:
    db.set_quiet(True)
    await message.answer("🔇 Тихий режим увімкнено.")


@dp.message(Command("normal"))
async def cmd_normal(message: types.Message) -> None:
    db.set_quiet(False)
    await message.answer("🔔 Звичайний режим увімкнено.")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message) -> None:
    stats = db.get_stats(7)
    if not stats:
        await message.answer("Статистика порожня.")
        return
    lines = ["📊 Статистика за 7 днів:"]
    for day, cnt in sorted(stats.items(), reverse=True):
        lines.append(f"  {day}: {cnt} виконано")
    await message.answer("\n".join(lines))


@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message) -> None:
    lines = ["📋 Поточні таски:\n"]
    for slot in SLOTS:
        tasks = _get_tasks(slot)
        lines.append(f"<b>{slot}:</b>")
        for i, t in enumerate(tasks):
            lines.append(f"  {i}. {t}")
        lines.append("")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@dp.message(Command("addtask"))
async def cmd_addtask(message: types.Message) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or parts[1] not in SLOTS:
        await message.answer(
            f"Використання: /addtask <slot> <текст>\nSlots: {', '.join(SLOTS)}"
        )
        return
    slot, text = parts[1], parts[2]
    db.add_task(slot, text)
    await message.answer(f"✅ Таск додано до {slot}: {text}")


@dp.message(Command("deltask"))
async def cmd_deltask(message: types.Message) -> None:
    parts = (message.text or "").split()
    if len(parts) < 3 or parts[1] not in SLOTS:
        await message.answer(
            f"Використання: /deltask <slot> <index>\nSlots: {', '.join(SLOTS)}"
        )
        return
    slot = parts[1]
    try:
        index = int(parts[2])
    except ValueError:
        await message.answer("Індекс повинен бути числом.")
        return
    if db.delete_task(slot, index):
        await message.answer(f"🗑️ Таск {index} видалено з {slot}.")
    else:
        await message.answer(f"Таск {index} не знайдено в {slot}.")


# ── Callbacks ────────────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("done|"))
async def cb_done(callback: types.CallbackQuery) -> None:
    parts = callback.data.split("|")
    if len(parts) < 3:
        await callback.answer("Помилка.")
        return
    slot, idx_str = parts[1], parts[2]
    tasks = _get_tasks(slot)
    try:
        idx = int(idx_str)
        task = tasks[idx]
    except (ValueError, IndexError):
        await callback.answer("Помилка.")
        return
    db.mark_done(slot, task, _today())
    await callback.answer(f"✅ {task}")
    kb = _make_task_keyboard(slot, tasks)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        logging.warning("Could not update reply markup", exc_info=True)


@dp.callback_query(F.data.startswith("snooze|"))
async def cb_snooze(callback: types.CallbackQuery) -> None:
    parts = callback.data.split("|")
    if len(parts) < 2:
        await callback.answer("Помилка.")
        return
    slot = parts[1]
    if _scheduler is not None:
        run_at = datetime.now(TZ) + timedelta(minutes=CFG.snooze_minutes_default)
        cid = str(callback.message.chat.id)

        async def _snooze_job(s: str = slot, c: str = cid) -> None:
            await _send_slot(s, c)

        schedule_once(
            _scheduler,
            run_at,
            f"snooze|{slot}|{run_at.isoformat()}",
            _snooze_job,
        )
    await callback.answer(f"⏰ Нагадаю через {CFG.snooze_minutes_default} хв.")


# ── Entry point ──────────────────────────────────────────────────────────────

async def main() -> None:
    global _scheduler
    s = make_scheduler(CFG.tz_name)
    _scheduler = s

    async def _job_morning() -> None:
        await _send_slot("morning")

    async def _job_day() -> None:
        await _send_slot("day")

    async def _job_evening() -> None:
        await _send_slot("evening")

    schedule_daily(s, CFG.tz_name, "morning", CFG.morning_at, _job_morning)
    schedule_daily(s, CFG.tz_name, "day", CFG.day_at, _job_day)
    schedule_daily(s, CFG.tz_name, "evening", CFG.evening_at, _job_evening)
    s.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
