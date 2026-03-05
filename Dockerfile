FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source files
COPY bot.py config.py content_seed.py generator.py scheduler.py storage.py weather.py ./

# Persistent storage volume for SQLite database
RUN mkdir /data
ENV DB_PATH=/data/bot.db
VOLUME ["/data"]

# Stream logs immediately
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
