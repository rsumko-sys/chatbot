# Verkhovyna Helper Bot

Триразові нагадування + кнопки "зроблено/нагадай/не встигла" + критичні задачі (павліни/двері/вода/ліки) з повтором.

## Запуск
1) python -m venv .venv && source .venv/bin/activate
2) pip install -r requirements.txt
3) cp .env.example .env і заповни TOKEN та CHAT_ID
4) python bot.py

## Команди
/ping — живий
/morning /day /evening — ручний виклик повідомлення
/quiet — тихий режим (коротко, без історій)
/normal — звичайний режим
/stats — статистика за 7 днів
/tasks — показати таски
/addtask <slot> <text> — додати таск
/deltask <slot> <index> — видалити таск

