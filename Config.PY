"""
config.py — Central configuration for Telegram Reminder Bot.
All secrets are loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    # ── Telegram ──────────────────────────────────────────────────────────────
    BOT_TOKEN: str = field(default_factory=lambda: _require("BOT_TOKEN"))
    ADMIN_CHAT_ID: int = field(
        default_factory=lambda: int(_require("ADMIN_CHAT_ID"))
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./reminder_bot.db"
        )
    )

    # ── Redis (optional — falls back to in-memory PTB persistence) ────────────
    REDIS_URL: str | None = field(
        default_factory=lambda: os.getenv("REDIS_URL")  # e.g. redis://localhost:6379/0
    )

    # ── i18n ──────────────────────────────────────────────────────────────────
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "fa", "es", "ar", "ru", "zh")

    # ── Subscription ──────────────────────────────────────────────────────────
    SUBSCRIPTION_PRICE_LABEL: str = "⭐ 5 Stars / month"

    # ── Job Queue ─────────────────────────────────────────────────────────────
    SCHEDULER_TIMEZONE: str = field(
        default_factory=lambda: os.getenv("TZ", "UTC")
    )


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Please create a .env file or set it in your environment."
        )
    return value


# Singleton — import this everywhere
settings = Config()
