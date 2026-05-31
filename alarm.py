"""
handlers/alarm.py — Alarm creation ConversationHandler + alarm list/delete.

Conversation flow:
    MONTH → DAY → HOUR → MINUTE → MESSAGE
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database import (
    create_alarm,
    delete_alarm,
    get_active_alarms_for_user,
)
from i18n import t
from keyboards import (
    day_keyboard,
    hour_keyboard,
    main_menu_keyboard,
    minute_keyboard,
    month_keyboard,
    my_alarms_keyboard,
)
from utils.helpers import fmt_dt, get_lang, require_subscription

logger = logging.getLogger(__name__)

# ── Conversation states ────────────────────────────────────────────────────────
MONTH, DAY, HOUR, MINUTE, MESSAGE = range(5)

# Context keys for storing partial alarm data
_KEY_YEAR = "alarm_year"
_KEY_MONTH = "alarm_month"
_KEY_DAY = "alarm_day"
_KEY_HOUR = "alarm_hour"
_KEY_MINUTE = "alarm_minute"


# ── Entry point — triggered by "Set Alarm" button ─────────────────────────────

async def set_alarm_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)

    if not await require_subscription(update, context, lang):
        return ConversationHandler.END

    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.select_month"),
        parse_mode="HTML",
        reply_markup=month_keyboard(lang),
    )
    # Store current year in context
    context.user_data[_KEY_YEAR] = datetime.now(tz=timezone.utc).year  # type: ignore[index]
    return MONTH


# ── Step 1: Month selected ────────────────────────────────────────────────────

async def month_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data: str = query.data  # type: ignore[union-attr]
    lang = await get_lang(update)

    if data == "alarm:cancel":
        return await _cancel(update, context)

    _, _, month_str = data.split(":")
    month = int(month_str)
    context.user_data[_KEY_MONTH] = month  # type: ignore[index]
    year: int = context.user_data[_KEY_YEAR]  # type: ignore[index]

    month_name = t(lang, f"months.{month}")
    await query.answer()  # type: ignore[union-attr]
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.select_day", month=month_name),
        parse_mode="HTML",
        reply_markup=day_keyboard(lang, year, month),
    )
    return DAY


# ── Step 2: Day selected ──────────────────────────────────────────────────────

async def day_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data: str = query.data  # type: ignore[union-attr]
    lang = await get_lang(update)

    if data == "alarm:cancel":
        return await _cancel(update, context)
    if data == "alarm:back:month":
        await query.answer()  # type: ignore[union-attr]
        await query.message.reply_text(  # type: ignore[union-attr]
            t(lang, "alarm.select_month"),
            parse_mode="HTML",
            reply_markup=month_keyboard(lang),
        )
        return MONTH

    _, _, day_str = data.split(":")
    day = int(day_str)
    context.user_data[_KEY_DAY] = day  # type: ignore[index]

    year: int = context.user_data[_KEY_YEAR]  # type: ignore[index]
    month: int = context.user_data[_KEY_MONTH]  # type: ignore[index]
    date_str = f"{year}-{month:02d}-{day:02d}"

    await query.answer()  # type: ignore[union-attr]
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.select_hour", date=date_str),
        parse_mode="HTML",
        reply_markup=hour_keyboard(lang),
    )
    return HOUR


# ── Step 3: Hour selected ─────────────────────────────────────────────────────

async def hour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data: str = query.data  # type: ignore[union-attr]
    lang = await get_lang(update)

    if data == "alarm:cancel":
        return await _cancel(update, context)
    if data == "alarm:back:day":
        year: int = context.user_data[_KEY_YEAR]  # type: ignore[index]
        month: int = context.user_data[_KEY_MONTH]  # type: ignore[index]
        month_name = t(lang, f"months.{month}")
        await query.answer()  # type: ignore[union-attr]
        await query.message.reply_text(  # type: ignore[union-attr]
            t(lang, "alarm.select_day", month=month_name),
            parse_mode="HTML",
            reply_markup=day_keyboard(lang, year, month),
        )
        return DAY

    _, _, hour_str = data.split(":")
    hour = int(hour_str)
    context.user_data[_KEY_HOUR] = hour  # type: ignore[index]

    year = context.user_data[_KEY_YEAR]  # type: ignore[index]
    month = context.user_data[_KEY_MONTH]  # type: ignore[index]
    day: int = context.user_data[_KEY_DAY]  # type: ignore[index]
    partial_dt = f"{year}-{month:02d}-{day:02d} {hour:02d}:??"

    await query.answer()  # type: ignore[union-attr]
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.select_minute", datetime=partial_dt),
        parse_mode="HTML",
        reply_markup=minute_keyboard(lang),
    )
    return MINUTE


# ── Step 4: Minute selected ───────────────────────────────────────────────────

async def minute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data: str = query.data  # type: ignore[union-attr]
    lang = await get_lang(update)

    if data == "alarm:cancel":
        return await _cancel(update, context)
    if data == "alarm:back:hour":
        year: int = context.user_data[_KEY_YEAR]  # type: ignore[index]
        month: int = context.user_data[_KEY_MONTH]  # type: ignore[index]
        day: int = context.user_data[_KEY_DAY]  # type: ignore[index]
        date_str = f"{year}-{month:02d}-{day:02d}"
        await query.answer()  # type: ignore[union-attr]
        await query.message.reply_text(  # type: ignore[union-attr]
            t(lang, "alarm.select_hour", date=date_str),
            parse_mode="HTML",
            reply_markup=hour_keyboard(lang),
        )
        return HOUR

    _, _, minute_str = data.split(":")
    minute = int(minute_str)
    context.user_data[_KEY_MINUTE] = minute  # type: ignore[index]

    year = context.user_data[_KEY_YEAR]  # type: ignore[index]
    month = context.user_data[_KEY_MONTH]  # type: ignore[index]
    day = context.user_data[_KEY_DAY]  # type: ignore[index]
    hour: int = context.user_data[_KEY_HOUR]  # type: ignore[index]
    dt_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC"

    await query.answer()  # type: ignore[union-attr]
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.enter_message", datetime=dt_str),
        parse_mode="HTML",
    )
    return MESSAGE


# ── Step 5: Message text received ────────────────────────────────────────────

async def message_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update)
    msg_text = (update.message.text or "").strip()  # type: ignore[union-attr]

    if not msg_text:
        await update.message.reply_text(t(lang, "error.invalid_input"))  # type: ignore
        return MESSAGE

    year: int = context.user_data[_KEY_YEAR]  # type: ignore[index]
    month: int = context.user_data[_KEY_MONTH]  # type: ignore[index]
    day: int = context.user_data[_KEY_DAY]  # type: ignore[index]
    hour: int = context.user_data[_KEY_HOUR]  # type: ignore[index]
    minute: int = context.user_data[_KEY_MINUTE]  # type: ignore[index]

    trigger_dt = datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

    if trigger_dt <= datetime.now(tz=timezone.utc):
        await update.message.reply_text(  # type: ignore
            t(lang, "alarm.past_time"), parse_mode="HTML"
        )
        return MESSAGE

    user_id = update.effective_user.id  # type: ignore[union-attr]
    alarm = await create_alarm(
        user_id=user_id,
        trigger_time=trigger_dt,
        message_text=msg_text,
    )

    # Schedule the job in JobQueue
    context.job_queue.run_once(  # type: ignore[union-attr]
        _fire_alarm,
        when=trigger_dt,
        data={"alarm_id": alarm.id, "user_id": user_id, "message": msg_text},
        name=f"alarm_{alarm.id}",
        chat_id=user_id,
    )

    dt_str = fmt_dt(trigger_dt)
    await update.message.reply_text(  # type: ignore
        t(lang, "alarm.set_success", datetime=dt_str, message=msg_text),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )
    logger.info("Alarm %s scheduled for user %s at %s", alarm.id, user_id, trigger_dt)
    _clear_alarm_data(context)
    return ConversationHandler.END


# ── Alarm Fire Callback (JobQueue) ────────────────────────────────────────────

async def _fire_alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    from database import deactivate_alarm

    job = context.job
    data: dict = job.data  # type: ignore[union-attr]
    user_id: int = data["user_id"]
    alarm_id: int = data["alarm_id"]
    message: str = data["message"]

    lang = await get_lang_by_id(user_id)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=t(lang, "alarm.fired", message=message),
            parse_mode="HTML",
        )
        logger.info("Alarm %s fired for user %s", alarm_id, user_id)
    except Exception as exc:
        logger.error("Failed to send alarm %s to user %s: %s", alarm_id, user_id, exc)
    finally:
        await deactivate_alarm(alarm_id)


async def get_lang_by_id(user_id: int) -> str:
    from database import get_user
    from config import settings
    user = await get_user(user_id)
    if user and user.language_code:
        return user.language_code
    return settings.DEFAULT_LANGUAGE


# ── My Alarms ─────────────────────────────────────────────────────────────────

async def my_alarms_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)
    user_id = update.effective_user.id  # type: ignore[union-attr]

    if not await require_subscription(update, context, lang):
        return

    alarms = await get_active_alarms_for_user(user_id)
    if not alarms:
        await query.message.reply_text(  # type: ignore[union-attr]
            t(lang, "alarm.list_empty"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(lang),
        )
        return

    lines = [t(lang, "alarm.list_header")]
    for alarm in alarms:
        lines.append(
            t(
                lang,
                "alarm.list_item",
                id=alarm.id,
                datetime=fmt_dt(alarm.trigger_time),
                message=alarm.message_text[:40],
            )
        )
    text = "\n".join(lines)
    await query.message.reply_text(  # type: ignore[union-attr]
        text,
        parse_mode="HTML",
        reply_markup=my_alarms_keyboard(lang),
    )


async def delete_alarm_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.delete_prompt"), parse_mode="HTML"
    )
    return 0  # Handled separately with ConversationHandler fallback or plain handler


async def delete_alarm_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    lang = await get_lang(update)
    user_id = update.effective_user.id  # type: ignore[union-attr]
    raw = (update.message.text or "").strip()  # type: ignore[union-attr]

    try:
        alarm_id = int(raw)
    except ValueError:
        await update.message.reply_text(t(lang, "error.invalid_input"))  # type: ignore
        return

    success = await delete_alarm(alarm_id, user_id)
    if success:
        # Cancel the pending job if still pending
        jobs = context.job_queue.get_jobs_by_name(f"alarm_{alarm_id}")  # type: ignore
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text(  # type: ignore
            t(lang, "alarm.delete_success", id=alarm_id),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await update.message.reply_text(  # type: ignore
            t(lang, "alarm.delete_not_found"),
            parse_mode="HTML",
        )


# ── Cancel / Cleanup ──────────────────────────────────────────────────────────

async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)
    _clear_alarm_data(context)
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "alarm.cancelled"),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


def _clear_alarm_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in (_KEY_YEAR, _KEY_MONTH, _KEY_DAY, _KEY_HOUR, _KEY_MINUTE):
        context.user_data.pop(key, None)  # type: ignore[union-attr]


# ── Handler registration ───────────────────────────────────────────────────────

def build_alarm_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_alarm_entry, pattern=r"^menu:set_alarm$"),
        ],
        states={
            MONTH: [
                CallbackQueryHandler(month_callback, pattern=r"^alarm:(month:\d+|cancel)$"),
            ],
            DAY: [
                CallbackQueryHandler(
                    day_callback,
                    pattern=r"^alarm:(day:\d+|cancel|back:month)$",
                ),
            ],
            HOUR: [
                CallbackQueryHandler(
                    hour_callback,
                    pattern=r"^alarm:(hour:\d+|cancel|back:day)$",
                ),
            ],
            MINUTE: [
                CallbackQueryHandler(
                    minute_callback,
                    pattern=r"^alarm:(minute:\d+|cancel|back:hour)$",
                ),
            ],
            MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_input),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(_cancel, pattern=r"^alarm:cancel$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END),
        ],
        per_user=True,
        per_chat=False,
        name="alarm_creation",
        persistent=False,
    )


def register_alarm_handlers(application) -> None:  # type: ignore[type-arg]
    application.add_handler(build_alarm_conversation())
    application.add_handler(
        CallbackQueryHandler(my_alarms_callback, pattern=r"^menu:my_alarms$")
    )
    application.add_handler(
        CallbackQueryHandler(delete_alarm_prompt, pattern=r"^alarm:delete_prompt$")
    )
