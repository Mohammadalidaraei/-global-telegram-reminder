"""
handlers/common.py — /start, /help, language selection, and main menu handlers.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from database import get_or_create_user, set_user_language
from i18n import t
from keyboards import language_keyboard, main_menu_keyboard
from utils.helpers import get_lang

logger = logging.getLogger(__name__)


# ── /start ─────────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return

    tg_lang = (tg_user.language_code or "en")[:2]
    supported = ("en", "fa", "es", "ar", "ru", "zh")
    lang = tg_lang if tg_lang in supported else "en"

    user, created = await get_or_create_user(
        user_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        language_code=lang,
    )
    if not created:
        lang = user.language_code  # use stored preference

    name = tg_user.first_name or tg_user.username or "there"
    await update.message.reply_text(  # type: ignore[union-attr]
        t(lang, "welcome", name=name),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )
    logger.info("User %s started the bot (lang=%s, new=%s)", tg_user.id, lang, created)


# ── Main Menu callback ─────────────────────────────────────────────────────────

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "main_menu"),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )


# ── Language Selection ─────────────────────────────────────────────────────────

async def language_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    lang = await get_lang(update)
    await query.message.reply_text(  # type: ignore[union-attr]
        t(lang, "choose_language"),
        parse_mode="HTML",
        reply_markup=language_keyboard(),
    )


async def set_language_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    data: str = query.data  # type: ignore[union-attr]
    _, new_lang = data.split(":", 1)

    user_id = update.effective_user.id  # type: ignore[union-attr]
    await set_user_language(user_id, new_lang)
    await query.answer(t(new_lang, "language_set"))  # type: ignore[union-attr]
    await query.message.reply_text(  # type: ignore[union-attr]
        t(new_lang, "main_menu"),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(new_lang),
    )
    logger.info("User %s changed language to %s", user_id, new_lang)


# ── Handler registration ───────────────────────────────────────────────────────

def register_common_handlers(application) -> None:  # type: ignore[type-arg]
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(
        CallbackQueryHandler(main_menu_callback, pattern=r"^menu:main$")
    )
    application.add_handler(
        CallbackQueryHandler(language_menu_callback, pattern=r"^menu:language$")
    )
    application.add_handler(
        CallbackQueryHandler(set_language_callback, pattern=r"^lang:")
    ) 
