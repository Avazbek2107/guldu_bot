FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
COPY bot/requirements.txt bot/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r bot/requirements.txt

COPY backend/app backend/app
COPY bot bot

CMD ["python", "-m", "bot.main"]
