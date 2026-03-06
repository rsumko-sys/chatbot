from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Callable

def parse_hhmm(hhmm: str) -> tuple[int, int]:
    h, m = map(int, hhmm.split(":"))
    return h, m

def make_scheduler(tz_name: str) -> AsyncIOScheduler:
    return AsyncIOScheduler(timezone=ZoneInfo(tz_name))

def schedule_daily(s: AsyncIOScheduler, tz_name: str, slot: str, at_hhmm: str, fn: Callable):
    h, m = parse_hhmm(at_hhmm)
    trigger = CronTrigger(hour=h, minute=m, timezone=ZoneInfo(tz_name))
    s.add_job(fn, trigger=trigger, id=f"{slot}_daily", replace_existing=True)

def schedule_once(s: AsyncIOScheduler, run_at: datetime, job_id: str, fn: Callable):
    trigger = DateTrigger(run_date=run_at)
    s.add_job(fn, trigger=trigger, id=job_id, replace_existing=True)
