"""
keyboards.py — Inline keyboard factory functions.
All keyboards are built dynamically based on user language.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from i18n import language_name, t


# ── Helpers ────────────────────────────────────────────────────────────────────

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def _cancel_row(lang: str) -> list[InlineKeyboardButton]:
    return [_btn(t(lang, "btn_cancel"), "alarm:cancel")]


def _back_row(lang: str, callback: str) -> list[InlineKeyboardButton]:
    return [_btn(t(lang, "btn_back"), callback)]


# ── Main Menu ──────────────────────────────────────────────────────────────────

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t(lang, "btn_set_alarm"), "menu:set_alarm"),
         _btn(t(lang, "btn_my_alarms"), "menu:my_alarms")],
        [_btn(t(lang, "btn_language"), "menu:language")],
        [_btn(t(lang, "btn_subscribe"), "menu:subscribe")],
    ])


# ── Language Selector ──────────────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    langs = ["en", "fa", "es", "ar", "ru", "zh"]
    rows = []
    for i in range(0, len(langs), 3):
        row = [
            _btn(language_name(l), f"lang:{l}") for l in langs[i:i + 3]
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


# ── Subscribe ──────────────────────────────────────────────────────────────────

def subscribe_keyboard(lang: str) -> InlineKeyboardMarkup:
    """CTA keyboard shown to non-subscribed users."""
    return InlineKeyboardMarkup([
        [_btn(t(lang, "btn_subscribe"), "menu:subscribe")],
    ])


# ── Alarm — Step 1: Month ─────────────────────────────────────────────────────

def month_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for row_start in range(1, 13, 3):
        row = [
            _btn(t(lang, f"months.{m}"), f"alarm:month:{m}")
            for m in range(row_start, min(row_start + 3, 13))
        ]
        rows.append(row)
    rows.append(_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


# ── Alarm — Step 2: Day ───────────────────────────────────────────────────────

def day_keyboard(lang: str, year: int, month: int) -> InlineKeyboardMarkup:
    _, num_days = calendar.monthrange(year, month)
    rows = []
    row: list[InlineKeyboardButton] = []
    for day in range(1, num_days + 1):
        row.append(_btn(str(day), f"alarm:day:{day}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        _btn(t(lang, "btn_back"), "alarm:back:month"),
        _btn(t(lang, "btn_cancel"), "alarm:cancel"),
    ])
    return InlineKeyboardMarkup(rows)


# ── Alarm — Step 3: Hour ──────────────────────────────────────────────────────

def hour_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for h in range(24):
        row.append(_btn(f"{h:02d}", f"alarm:hour:{h}"))
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        _btn(t(lang, "btn_back"), "alarm:back:day"),
        _btn(t(lang, "btn_cancel"), "alarm:cancel"),
    ])
    return InlineKeyboardMarkup(rows)


# ── Alarm — Step 4: Minute ────────────────────────────────────────────────────

def minute_keyboard(lang: str) -> InlineKeyboardMarkup:
    minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    rows = []
    row: list[InlineKeyboardButton] = []
    for m in minutes:
        row.append(_btn(f"{m:02d}", f"alarm:minute:{m}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        _btn(t(lang, "btn_back"), "alarm:back:hour"),
        _btn(t(lang, "btn_cancel"), "alarm:cancel"),
    ])
    return InlineKeyboardMarkup(rows)


# ── My Alarms ─────────────────────────────────────────────────────────────────

def my_alarms_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t(lang, "alarm.btn_delete"), "alarm:delete_prompt")],
        [_btn(t(lang, "btn_back"), "menu:main")],
    ])


# ── Admin Panel ────────────────────────────────────────────────────────────────

def admin_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t(lang, "admin.btn_add_sub"), "admin:add_sub")],
        [_btn(t(lang, "admin.btn_remove_sub"), "admin:remove_sub")],
        [_btn(t(lang, "admin.btn_stats"), "admin:stats")],
    ])
