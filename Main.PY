"""
main.py — Bot entry point.

Responsibilities:
- Initialize DB
- Build the Application with JobQueue
- Register all handlers
- Re-inject pending alarms from DB into JobQueue (resilience)
- Start polling
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
)

from config import settings
from database import get_all_pending_alarms, init_db
from handlers.admin import register_admin_handlers
from handlers.alarm import _fire_alarm, register_alarm_handlers
from handlers.common import register_common_handlers
from i18n import t

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
# Quiet noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ── Subscribe button (placeholder) ────────────────────────────────────────────

async def subscribe_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Placeholder — replace with payment gateway logic."""
    query = update.callback_query
    await query.answer("💳 Payment system coming soon!", show_alert=True)  # type: ignore[union-attr]


# ── Pending alarm re-injection ─────────────────────────────────────────────────

async def reinject_pending_alarms(application: Application) -> None:  # type: ignore[type-arg]
    """
    Called on startup.
    Queries all future-dated active alarms and re-schedules them in JobQueue.
    This ensures reminders survive bot restarts.
    """
    pending = await get_all_pending_alarms()
    now = datetime.now(tz=timezone.utc)
    reinjected = 0

    for alarm in pending:
        trigger = alarm.trigger_time
        if trigger.tzinfo is None:
            trigger = trigger.replace(tzinfo=timezone.utc)

        if trigger <= now:
            # Alarm misfired during downtime — fire immediately with a 2-second delay
            delay = 2.0
        else:
            delay = (trigger - now).total_seconds()

        application.job_queue.run_once(  # type: ignore[union-attr]
            _fire_alarm,
            when=delay,
            data={
                "alarm_id": alarm.id,
                "user_id": alarm.user_id,
                "message": alarm.message_text,
            },
            name=f"alarm_{alarm.id}",
            chat_id=alarm.user_id,
        )
        reinjected += 1

    logger.info("Re-injected %d pending alarms into JobQueue.", reinjected)


# ── Post-init hook ─────────────────────────────────────────────────────────────

async def post_init(application: Application) -> None:  # type: ignore[type-arg]
    """Runs after the Application is initialized but before polling starts."""
    await init_db()
    await reinject_pending_alarms(application)

    # Set bot commands menu
    await application.bot.set_my_commands([
        BotCommand("start", "Start / Main menu"),
        BotCommand("admin", "Admin panel (admin only)"),
    ])
    logger.info("Bot initialized. Token: ...%s", settings.BOT_TOKEN[-6:])


# ── Error handler ──────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while processing update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            lang = "en"
            if update.effective_user:
                from utils.helpers import resolve_lang
                lang = await resolve_lang(update.effective_user.id)
            await update.effective_message.reply_text(
                t(lang, "error.generic"), parse_mode="HTML"
            )
        except Exception:
            pass  # Don't recurse


# ── Application factory ────────────────────────────────────────────────────────

def build_application() -> Application:  # type: ignore[type-arg]
    builder = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .post_init(post_init)
        .concurrent_updates(True)
    )

    app = builder.build()

    # ── Register handlers (order matters: ConversationHandlers first) ──────────
    register_common_handlers(app)
    register_alarm_handlers(app)
    register_admin_handlers(app)

    # Generic callbacks
    app.add_handler(
        CallbackQueryHandler(subscribe_callback, pattern=r"^menu:subscribe$")
    )

    # Global error handler
    app.add_error_handler(error_handler)

    return app


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Starting Telegram Reminder Bot…")
    application = build_application()
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
