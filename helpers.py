"""
utils/helpers.py — Shared utility helpers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database import get_user
from i18n import t
from keyboards import subscribe_keyboard

logger = logging.getLogger(__name__)

# ── Language Resolution ────────────────────────────────────────────────────────

async def resolve_lang(user_id: int, update_lang: str | None = None) -> str:
    """
    Determine the user's preferred language.
    Priority: DB stored lang > Telegram client lang > default.
    """
    user = await get_user(user_id)
    if user and user.language_code:
        return user.language_code
    if update_lang and update_lang[:2] in settings.SUPPORTED_LANGUAGES:
        return update_lang[:2]
    return settings.DEFAULT_LANGUAGE


async def get_lang(update: Update) -> str:
    """Convenience wrapper to get lang from an Update."""
    user_id = update.effective_user.id  # type: ignore[union-attr]
    tg_lang = update.effective_user.language_code  # type: ignore[union-attr]
    return await resolve_lang(user_id, tg_lang)


# ── Subscription Guard ────────────────────────────────────────────────────────

async def require_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    lang: str,
) -> bool:
    """
    Returns True if the user has an active subscription.
    Sends a subscription prompt and returns False otherwise.
    """
    user_id = update.effective_user.id  # type: ignore[union-attr]
    user = await get_user(user_id)
    if user and user.has_active_subscription:
        return True

    text = t(lang, "no_subscription")
    markup = subscribe_keyboard(lang)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(  # type: ignore
            text, parse_mode="HTML", reply_markup=markup
        )
    else:
        await update.message.reply_text(  # type: ignore
            text, parse_mode="HTML", reply_markup=markup
        )
    return False


# ── Admin Guard ───────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id == settings.ADMIN_CHAT_ID


# ── Date/Time Formatting ──────────────────────────────────────────────────────

def fmt_dt(dt: datetime) -> str:
    """Format a datetime to a readable UTC string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def fmt_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")
