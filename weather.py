import os

import requests


def get_weather(city: str = "Verkhovyna", api_key: str = None) -> str:
    if api_key is None:
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "[Погода: API ключ не налаштовано]"
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric&lang=ua"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"Сьогодні у {city} {temp}°C, {desc}."
    except requests.exceptions.RequestException as exc:
        return f"[Погода: помилка мережі: {exc}]"
    except (KeyError, ValueError):
        return "[Погода: неочікуваний формат відповіді]"
