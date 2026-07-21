# Technician Support Bot

Guliston davlat universiteti uchun texnik yordam tizimi: Telegram bot + Web admin panel.
To'liq talablar uchun [`tz.pdf`](tz.pdf) ga qarang.

## Holat

- **Bosqich 1** — Backend skeleti + PostgreSQL uchun SQLAlchemy modellari (fakultet, foydalanuvchi/texnik
  xodim, bildirishnoma, ilova, qayta yo'naltirish, baholash, audit log)
- **Bosqich 2** — Auth/RBAC API: JWT login, rolga asoslangan kirish nazorati, Super Admin uchun
  fakultet va foydalanuvchi/texnik xodim boshqaruvi
- **Bosqich 3** — Telegram bot (Aiogram 3.x): ro'yxatdan o'tish, ariza yaratish, texnik xodimga
  yo'naltirish, qabul qilish/yopish/qayta yo'naltirish, baholash, shubhali chaqiruv belgilash, eskalatsiya

React admin panel keyingi bosqichda qo'shiladi.

## Ishga tushirish (Docker)

```bash
cp .env.example .env
# .env faylida BOT_TOKEN ni @BotFather'dan olingan token bilan to'ldiring
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.scripts.seed_faculties
docker compose run --rm backend python -m app.scripts.create_superadmin --username admin --password '<parol>' --full-name "F I Sh" --phone "+998901234567"
docker compose up backend bot
```

`GET http://localhost:8000/health` — backend va DB ulanishini tekshiradi.

## Lokal ishlab chiqish (Docker'siz)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt -r ../bot/requirements.txt
cp ../.env.example ../.env    # DATABASE_URL va BOT_TOKEN'ni to'ldiring
alembic upgrade head
python -m app.scripts.seed_faculties
python -m app.scripts.create_superadmin --username admin --password ... --full-name "..." --phone "+998..."
uvicorn app.main:app --reload
```

Botni alohida terminalda ishga tushirish (repo ildizidan):

```bash
python -m bot.main
```

## Bot: texnik xodim akkountini bog'lash

Texnik xodim/Super Admin hisoblari Web panel (`POST /users`) orqali `username`+`parol`+`telefon` bilan
yaratiladi. Ular botdan foydalanish uchun `/start` bosib, telefon raqamini yuborishlari kifoya — bot shu
raqam bo'yicha mavjud hisobni topib, Telegram akkountini avtomatik bog'laydi.

## Loyiha tuzilishi

```
backend/
  app/
    core/       # config, database, security (JWT/parol)
    models/     # SQLAlchemy modellari
    schemas/    # Pydantic sxemalar
    api/        # FastAPI routerlar (auth, users, faculties)
    scripts/    # create_superadmin, seed_faculties
  migrations/   # Alembic migratsiyalari
bot/
  handlers/     # registration, tickets, technician
  services/     # tickets, escalation, users (biznes-logika)
  main.py       # Bot/Dispatcher + eskalatsiya background task
storage/        # yuklangan rasm/video fayllari (lokal disk)
```
