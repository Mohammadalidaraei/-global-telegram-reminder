# ⏰ Telegram Reminder Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v21-green?style=for-the-badge&logo=telegram)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-6-purple?style=for-the-badge)

**A production-ready, fully monetized Telegram Reminder Bot with multi-language support, subscription enforcement, and a secure admin panel.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [Configuration](#-configuration) • [Running](#-running) • [Architecture](#-architecture)

---

</div>

---

## 🌐 Language / زبان

- [🇬🇧 English Documentation](#english-documentation)
- [🇮🇷 مستندات فارسی](#مستندات-فارسی)

---

<a name="english-documentation"></a>
# 🇬🇧 English Documentation

## ✨ Features

| Feature | Description |
|---|---|
| **🔒 Subscription Gate** | All core features require an active subscription; blocked users see a CTA keyboard |
| **🔐 Admin Panel** | Restricted to a hardcoded `ADMIN_CHAT_ID`; add/remove subscriptions, view stats |
| **⏰ Smart Alarm Engine** | Step-by-step Inline Keyboard wizard (Month → Day → Hour → Minute → Message) |
| **♻️ Resilient Job Queue** | On startup, all pending alarms are re-injected from the DB — no reminders lost |
| **🌍 6 Languages** | English, Persian (Farsi), Spanish, Arabic, Russian, Chinese — per-user preference stored in DB |
| **📋 Alarm Management** | List active alarms, delete by ID, automatic deactivation after firing |
| **🧱 Modular Architecture** | Clean separation of concerns across `models`, `database`, `handlers`, `locales` |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Bot Framework | `python-telegram-bot` v21 (async/await, JobQueue) |
| ORM | SQLAlchemy 2.0 (async) |
| DB Drivers | `aiosqlite` (SQLite) / `asyncpg` (PostgreSQL) |
| Scheduler | APScheduler via PTB's built-in `JobQueue` |
| i18n | Custom JSON-based localization engine |
| Config | `python-dotenv` |

---

## 📁 Project Structure

```
telegram-reminder-bot/
├── main.py                  # Entry point: app factory, startup hooks, error handler
├── config.py                # Centralized settings via dataclass + .env
├── models.py                # SQLAlchemy ORM models (User, Alarm)
├── database.py              # Async DB engine, session factory, all CRUD helpers
├── i18n.py                  # Localization engine (JSON-backed, dot-notation keys)
├── keyboards.py             # All InlineKeyboardMarkup factory functions
├── handlers/
│   ├── __init__.py
│   ├── common.py            # /start, language selection, main menu
│   ├── alarm.py             # Alarm ConversationHandler + list/delete
│   └── admin.py             # Admin ConversationHandler (add/remove sub, stats)
├── utils/
│   ├── __init__.py
│   └── helpers.py           # Shared: lang resolution, subscription guard, admin guard
├── locales/
│   ├── en.json              # English strings
│   ├── fa.json              # Persian strings
│   ├── es.json              # Spanish strings
│   ├── ar.json              # Arabic strings
│   ├── ru.json              # Russian strings
│   └── zh.json              # Chinese strings
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

All configuration is managed through environment variables. Copy the template:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_CHAT_ID=123456789          # Your Telegram numeric user ID

# Database (SQLite default, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./reminder_bot.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/reminderbot

# Optional Redis
# REDIS_URL=redis://localhost:6379/0

# Timezone
TZ=UTC
```

### How to get your `ADMIN_CHAT_ID`
Send any message to [@userinfobot](https://t.me/userinfobot) on Telegram — it will reply with your numeric user ID.

---

## 🚀 Installation

### Prerequisites

- Python **3.10** or higher
- pip / virtualenv
- (Optional) PostgreSQL for production
- (Optional) Redis

### Step-by-step

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-reminder-bot.git
cd telegram-reminder-bot
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment**
```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_CHAT_ID
```

**5. (PostgreSQL only) Create the database**
```bash
createdb reminderbot
# Update DATABASE_URL in .env accordingly
```

---

## ▶️ Running the Bot

```bash
python main.py
```

The bot will:
1. Connect to Telegram
2. Initialize (or migrate) the database schema automatically
3. Re-inject all pending future alarms from the DB into the scheduler
4. Begin polling for updates

You should see output like:
```
2025-01-01 12:00:00 | INFO     | __main__ — Starting Telegram Reminder Bot…
2025-01-01 12:00:01 | INFO     | database — Database tables created / verified.
2025-01-01 12:00:01 | INFO     | __main__ — Re-injected 3 pending alarms into JobQueue.
2025-01-01 12:00:01 | INFO     | __main__ — Bot initialized. Token: ...abc123
```

### Running with systemd (Production)

Create `/etc/systemd/system/reminderbot.service`:

```ini
[Unit]
Description=Telegram Reminder Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telegram-reminder-bot
EnvironmentFile=/opt/telegram-reminder-bot/.env
ExecStart=/opt/telegram-reminder-bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable reminderbot
sudo systemctl start reminderbot
sudo systemctl status reminderbot
```

### Running with Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t reminder-bot .
docker run -d --env-file .env --name reminder-bot reminder-bot
```

---

## 🗄️ Database

### Models

**`users` table**

| Column | Type | Description |
|---|---|---|
| `id` | BIGINT PK | Telegram user_id |
| `username` | VARCHAR(64) | Telegram @username |
| `first_name` | VARCHAR(128) | User's first name |
| `language_code` | VARCHAR(8) | Stored language preference |
| `subscription_expiry` | DATETIME | NULL = no subscription |
| `created_at` | DATETIME | Registration timestamp |

**`alarms` table**

| Column | Type | Description |
|---|---|---|
| `id` | INT PK | Auto-increment alarm ID |
| `user_id` | BIGINT FK | References `users.id` |
| `trigger_time` | DATETIME | UTC time to fire the alarm |
| `message_text` | TEXT | The reminder message |
| `is_active` | BOOLEAN | False = fired or deleted |
| `created_at` | DATETIME | Creation timestamp |

Tables are created automatically on first run via SQLAlchemy's `create_all`.

---

## 🌍 Adding a New Language

1. Create `locales/XX.json` (where `XX` is the ISO 639-1 code)
2. Copy `locales/en.json` as a template and translate all values
3. Add the code to `SUPPORTED_LANGUAGES` in `config.py`
4. Add the display name to `language_name()` in `i18n.py`
5. Add the flag button to `language_keyboard()` in `keyboards.py`

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss major changes.

---

## 📄 License

[MIT](LICENSE)

---
---

<a name="مستندات-فارسی"></a>
# 🇮🇷 مستندات فارسی

<div dir="rtl">

## ✨ ویژگی‌ها

| ویژگی | توضیحات |
|---|---|
| **🔒 دروازه اشتراک** | تمام ویژگی‌های اصلی نیاز به اشتراک فعال دارند؛ کاربران مسدود یک صفحه کلید دکمه‌ای می‌بینند |
| **🔐 پنل مدیریت** | فقط برای `ADMIN_CHAT_ID` مشخص شده؛ افزودن/حذف اشتراک، مشاهده آمار |
| **⏰ موتور یادآور هوشمند** | ویزارد گام‌به‌گام با صفحه کلید درون‌خطی (ماه ← روز ← ساعت ← دقیقه ← پیام) |
| **♻️ صف کار مقاوم** | هنگام راه‌اندازی، تمام یادآورهای معلق از پایگاه داده دوباره زمان‌بندی می‌شوند |
| **🌍 ۶ زبان** | انگلیسی، فارسی، اسپانیایی، عربی، روسی، چینی — ترجیح هر کاربر در پایگاه داده ذخیره می‌شود |
| **📋 مدیریت یادآور** | فهرست یادآورهای فعال، حذف با شناسه، غیرفعال‌سازی خودکار پس از اجرا |
| **🧱 معماری ماژولار** | جداسازی واضح مسئولیت‌ها در `models`، `database`، `handlers`، `locales` |

---

## 🛠 پشته فناوری

| لایه | فناوری |
|---|---|
| زبان | Python 3.10+ |
| فریمورک ربات | `python-telegram-bot` نسخه ۲۱ (async/await، JobQueue) |
| ORM | SQLAlchemy 2.0 (غیرهمزمان) |
| درایورهای پایگاه داده | `aiosqlite` (SQLite) / `asyncpg` (PostgreSQL) |
| زمان‌بند | APScheduler از طریق `JobQueue` داخلی PTB |
| i18n | موتور بومی‌سازی سفارشی مبتنی بر JSON |
| پیکربندی | `python-dotenv` |

---

## 📁 ساختار پروژه

```
telegram-reminder-bot/
├── main.py                  # نقطه ورود: کارخانه برنامه، هوک‌های راه‌اندازی، مدیریت خطا
├── config.py                # تنظیمات متمرکز از طریق dataclass + .env
├── models.py                # مدل‌های SQLAlchemy ORM (User، Alarm)
├── database.py              # موتور DB غیرهمزمان، کارخانه session، تمام توابع CRUD
├── i18n.py                  # موتور بومی‌سازی (پشتیبانی JSON، کلیدهای dot-notation)
├── keyboards.py             # تمام توابع سازنده InlineKeyboardMarkup
├── handlers/
│   ├── __init__.py
│   ├── common.py            # /start، انتخاب زبان، منوی اصلی
│   ├── alarm.py             # ConversationHandler یادآور + فهرست/حذف
│   └── admin.py             # ConversationHandler مدیریت (افزودن/حذف اشتراک، آمار)
├── utils/
│   ├── __init__.py
│   └── helpers.py           # اشتراکی: تشخیص زبان، محافظ اشتراک، محافظ مدیر
├── locales/
│   ├── en.json              # رشته‌های انگلیسی
│   ├── fa.json              # رشته‌های فارسی
│   ├── es.json              # رشته‌های اسپانیایی
│   ├── ar.json              # رشته‌های عربی
│   ├── ru.json              # رشته‌های روسی
│   └── zh.json              # رشته‌های چینی
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ پیکربندی

تمام پیکربندی از طریق متغیرهای محیطی مدیریت می‌شود. قالب را کپی کنید:

```bash
cp .env.example .env
```

فایل `.env` را ویرایش کنید:

```env
# الزامی
BOT_TOKEN=توکن_ربات_از_بات‌فادر
ADMIN_CHAT_ID=123456789          # شناسه عددی تلگرام شما

# پایگاه داده
DATABASE_URL=sqlite+aiosqlite:///./reminder_bot.db
# برای محیط تولید:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/reminderbot

# ریدیس (اختیاری)
# REDIS_URL=redis://localhost:6379/0

# منطقه زمانی
TZ=Asia/Tehran
```

### نحوه دریافت `ADMIN_CHAT_ID`
هر پیامی به [@userinfobot](https://t.me/userinfobot) در تلگرام ارسال کنید — شناسه عددی شما را در پاسخ می‌فرستد.

---

## 🚀 نصب

### پیش‌نیازها

- Python نسخه **۳.۱۰** یا بالاتر
- pip / virtualenv
- (اختیاری) PostgreSQL برای محیط تولید
- (اختیاری) Redis

### گام‌به‌گام

**۱. کلون کردن مخزن**
```bash
git clone https://github.com/yourusername/telegram-reminder-bot.git
cd telegram-reminder-bot
```

**۲. ساختن و فعال کردن محیط مجازی**
```bash
python -m venv venv
source venv/bin/activate        # لینوکس / macOS
# venv\Scripts\activate         # ویندوز
```

**۳. نصب وابستگی‌ها**
```bash
pip install -r requirements.txt
```

**۴. پیکربندی محیط**
```bash
cp .env.example .env
# فایل .env را با BOT_TOKEN و ADMIN_CHAT_ID خود ویرایش کنید
```

**۵. (فقط PostgreSQL) ساختن پایگاه داده**
```bash
createdb reminderbot
# DATABASE_URL را در فایل .env به‌روز کنید
```

---

## ▶️ اجرای ربات

```bash
python main.py
```

ربات:
۱. به تلگرام متصل می‌شود
۲. شمای پایگاه داده را به‌طور خودکار ایجاد یا بروزرسانی می‌کند
۳. تمام یادآورهای آینده معلق را از پایگاه داده در زمان‌بند دوباره تزریق می‌کند
۴. شروع به دریافت به‌روزرسانی‌ها می‌کند

---

## 🌍 افزودن زبان جدید

۱. فایل `locales/XX.json` را ایجاد کنید (جایی که `XX` کد ISO 639-1 است)
۲. `locales/en.json` را به عنوان قالب کپی کرده و تمام مقادیر را ترجمه کنید
۳. کد را به `SUPPORTED_LANGUAGES` در `config.py` اضافه کنید
۴. نام نمایشی را به `language_name()` در `i18n.py` اضافه کنید
۵. دکمه پرچم را به `language_keyboard()` در `keyboards.py` اضافه کنید

---

## 📄 مجوز

[MIT](LICENSE)

</div>
