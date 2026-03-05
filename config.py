import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    bot_token: str
    target_chat_id: str
    tz_name: str
    morning_at: str
    day_at: str
    evening_at: str
    snooze_minutes_default: int
    critical_chase_minutes: int
    db_path: str
    weather_api_key: str

def load_config() -> Config:
    return Config(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        target_chat_id=os.getenv("TARGET_CHAT_ID", "").strip(),
        tz_name=os.getenv("TZ_NAME", "Europe/Kyiv"),
        morning_at=os.getenv("MORNING_AT", "07:30"),
        day_at=os.getenv("DAY_AT", "13:00"),
        evening_at=os.getenv("EVENING_AT", "21:00"),
        snooze_minutes_default=int(os.getenv("SNOOZE_MINUTES_DEFAULT", "30")),
        critical_chase_minutes=int(os.getenv("CRITICAL_CHASE_MINUTES", "60")),
        db_path=os.getenv("DB_PATH", "bot.db"),
        weather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
    )
