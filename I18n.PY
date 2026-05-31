"""
i18n.py — Localization engine.
Loads JSON translation files from the locales/ directory.
Usage:  t(lang, "key")  or  t(lang, "nested.key")
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).parent / "locales"
_FALLBACK_LANG = "en"


@lru_cache(maxsize=None)
def _load(lang: str) -> dict[str, Any]:
    path = LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        logger.warning("Locale file not found: %s — falling back to 'en'", path)
        path = LOCALES_DIR / "en.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def t(lang: str, key: str, **kwargs: Any) -> str:
    """
    Translate *key* for *lang*.
    Supports dot-notation for nested keys, e.g. "alarm.set_success".
    Falls back to English if the key is missing.
    """
    def _get(data: dict, parts: list[str]) -> str | None:
        node: Any = data
        for part in parts:
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        return node if isinstance(node, str) else None

    parts = key.split(".")
    text = _get(_load(lang), parts)
    if text is None and lang != _FALLBACK_LANG:
        text = _get(_load(_FALLBACK_LANG), parts)
    if text is None:
        logger.error("Missing translation key '%s' for lang '%s'", key, lang)
        return key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as exc:
            logger.warning("Missing placeholder %s in key '%s'", exc, key)
    return text


def language_name(lang: str) -> str:
    """Human-readable language name in the native script."""
    _names = {
        "en": "🇬🇧 English",
        "fa": "🇮🇷 فارسی",
        "es": "🇪🇸 Español",
        "ar": "🇸🇦 العربية",
        "ru": "🇷🇺 Русский",
        "zh": "🇨🇳 中文",
    }
    return _names.get(lang, lang)
