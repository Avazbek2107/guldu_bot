# Technician Support Bot

Guliston davlat universiteti uchun texnik yordam tizimi: Telegram bot + Web admin panel.
To'liq talablar uchun [`tz.pdf`](tz.pdf) ga qarang.

## Bosqich 1 — Loyiha skeleti + DB modellar

Hozircha loyihada backend skeleti va PostgreSQL uchun SQLAlchemy modellari mavjud
(fakultet, foydalanuvchi/texnik xodim, bildirishnoma, ilova, qayta yo'naltirish, baholash, audit log).
Telegram bot va React admin panel keyingi bosqichlarda qo'shiladi.

## Ishga tushirish (Docker)

```bash
cp .env.example .env
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose up backend
```

`GET http://localhost:8000/health` — backend va DB ulanishini tekshiradi.

## Lokal ishlab chiqish (Docker'siz)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp ../.env.example ../.env    # DATABASE_URL ni lokal Postgres'ga moslang
alembic upgrade head
uvicorn app.main:app --reload
```

## Loyiha tuzilishi

```
backend/
  app/
    core/       # config, database
    models/     # SQLAlchemy modellari
  migrations/   # Alembic migratsiyalari
storage/        # yuklangan rasm/video fayllari (lokal disk)
```
