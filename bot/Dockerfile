FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
COPY bot/requirements.txt bot/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r bot/requirements.txt

COPY backend/app backend/app
COPY bot bot

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "bot.main"]
