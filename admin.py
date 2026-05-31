"""
handlers/admin.py — Secure admin panel.
Access is strictly restricted to ADMIN_CHAT_ID.
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

from config import settings
from database import (
    count_active_alarms,
    count_users,
    get_user,
    revoke_subscription,
    set_subscription,
)
from i18n import t
from keyboards import admin_keyboard
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

# ── States ────────────────────────────────────────────────────────────────────
WAIT_USER_ID, WAIT_EXPIRY, WAIT_REMOVE_ID = range(3)

_KEY_TARGET_UID = "admin_target_uid"
_KEY_ACTION = "admin_action"


# ── /admin command ─────────────────────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id  # type: ignore[union-attr]
    if not is_admin(user_id):
        await update.message.reply_text(  # type: ignore[union-attr]
            t("en", "admin.unauthorized"), parse_mode="HTML"
        )
        return

    await update.message.reply_text(  # type: ignore[union-attr]
        t("en", "admin.panel"),
        parse_mode="HTML",
        reply_markup=admin_keyboard("en"),
    )


# ── Callback: open panel from inline button ───────────────────────────────────

async def admin_panel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    user_id = update.effective_user.id  # type: ignore[union-attr]
    await query.answer()  # type: ignore[union-attr]

    if not is_admin(user_id):
        await query.message.reply_text(  # type: ignore[union-attr]
            t("en", "admin.unauthorized"), parse_mode="HTML"
        )
        return

    await query.message.reply_text(  # type: ignore[union-attr]
        t("en", "admin.panel"),
        parse_mode="HTML",
        reply_markup=admin_keyboard("en"),
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

async def admin_stats_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if not is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return

    users = await count_users()
    alarms = await count_active_alarms()
    await query.message.reply_text(  # type: ignore[union-attr]
        t("en", "admin.stats", users=users, alarms=alarms),
        parse_mode="HTML",
        reply_markup=admin_keyboard("en"),
    )


# ── Add Subscription Flow ─────────────────────────────────────────────────────

async def add_sub_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if not is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return ConversationHandler.END

    context.user_data[_KEY_ACTION] = "add"  # type: ignore[index]
    await query.message.reply_text(  # type: ignore[union-attr]
        t("en", "admin.ask_user_id"), parse_mode="HTML"
    )
    return WAIT_USER_ID


async def remove_sub_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if not is_admin(update.effective_user.id):  # type: ignore[union-attr]
        return ConversationHandler.END

    context.user_data[_KEY_ACTION] = "remove"  # type: ignore[index]
    await query.message.reply_text(  # type: ignore[union-attr]
        t("en", "admin.ask_user_id"), parse_mode="HTML"
    )
    return WAIT_USER_ID


async def receive_target_user_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    raw = (update.message.text or "").strip()  # type: ignore[union-attr]
    try:
        target_uid = int(raw)
    except ValueError:
        await update.message.reply_text(t("en", "error.invalid_input"))  # type: ignore
        return WAIT_USER_ID

    user = await get_user(target_uid)
    action = context.user_data.get(_KEY_ACTION)  # type: ignore[union-attr]

    if action == "remove":
        if user is None:
            await update.message.reply_text(  # type: ignore
                t("en", "admin.user_not_found", user_id=target_uid), parse_mode="HTML"
            )
            return ConversationHandler.END
        await revoke_subscription(target_uid)
        await update.message.reply_text(  # type: ignore
            t("en", "admin.sub_removed", user_id=target_uid),
            parse_mode="HTML",
            reply_markup=admin_keyboard("en"),
        )
        return ConversationHandler.END

    # action == "add" — need expiry date
    if user is None:
        await update.message.reply_text(  # type: ignore
            t("en", "admin.user_not_found", user_id=target_uid), parse_mode="HTML"
        )
        return ConversationHandler.END

    context.user_data[_KEY_TARGET_UID] = target_uid  # type: ignore[index]
    await update.message.reply_text(  # type: ignore
        t("en", "admin.ask_expiry"), parse_mode="HTML"
    )
    return WAIT_EXPIRY


async def receive_expiry_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    raw = (update.message.text or "").strip()  # type: ignore[union-attr]
    try:
        expiry = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        await update.message.reply_text(  # type: ignore
            t("en", "admin.invalid_date"), parse_mode="HTML"
        )
        return WAIT_EXPIRY

    target_uid: int = context.user_data[_KEY_TARGET_UID]  # type: ignore[index]
    await set_subscription(target_uid, expiry)

    await update.message.reply_text(  # type: ignore
        t("en", "admin.sub_added", user_id=target_uid, expiry=raw),
        parse_mode="HTML",
        reply_markup=admin_keyboard("en"),
    )
    logger.info("Admin added subscription for %s until %s", target_uid, raw)
    return ConversationHandler.END


# ── Cancel admin conversation ─────────────────────────────────────────────────

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Admin operation cancelled.")  # type: ignore
    return ConversationHandler.END


# ── Build & register ──────────────────────────────────────────────────────────

def build_admin_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_sub_entry, pattern=r"^admin:add_sub$"),
            CallbackQueryHandler(remove_sub_entry, pattern=r"^admin:remove_sub$"),
        ],
        states={
            WAIT_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_user_id)
            ],
            WAIT_EXPIRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expiry_date)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_cancel),
        ],
        per_user=True,
        per_chat=False,
        name="admin_panel",
        persistent=False,
    )


def register_admin_handlers(application) -> None:  # type: ignore[type-arg]
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(
        CallbackQueryHandler(admin_panel_callback, pattern=r"^admin:panel$")
    )
    application.add_handler(
        CallbackQueryHandler(admin_stats_callback, pattern=r"^admin:stats$")
    )
    application.add_handler(build_admin_conversation())
