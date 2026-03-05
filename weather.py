import os
import requests


def get_weather(city: str = "Verkhovyna", api_key: str = None) -> str:
    if api_key is None:
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "[Погода: API ключ не налаштовано]"
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric&lang=ua"
    )
    try:
        resp = requests.get(url)
        data = resp.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"Сьогодні у Верховині {temp}°C, {desc}."
    except Exception:
        return "[Погода: помилка отримання даних]"
