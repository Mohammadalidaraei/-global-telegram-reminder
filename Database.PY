"""
database.py — Async database engine, session factory, and CRUD helpers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings
from models import Alarm, Base, User

logger = logging.getLogger(__name__)

# ── Engine & Session Factory ──────────────────────────────────────────────────

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        connect_args = {}
        if "sqlite" in settings.DATABASE_URL:
            connect_args = {"check_same_thread": False}
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager providing a DB session with auto-commit/rollback."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (if they don't exist) on bot startup."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


# ── User CRUD ─────────────────────────────────────────────────────────────────


async def get_or_create_user(
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    language_code: str = "en",
) -> tuple[User, bool]:
    """
    Fetch an existing user or create one.
    Returns (user, created:bool).
    """
    async with get_db() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if user:
            return user, False
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        logger.info("New user registered: %s", user_id)
        return user, True


async def get_user(user_id: int) -> Optional[User]:
    async with get_db() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def set_user_language(user_id: int, lang: str) -> None:
    async with get_db() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(language_code=lang)
        )


async def set_subscription(user_id: int, expiry: datetime) -> None:
    async with get_db() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(subscription_expiry=expiry)
        )
    logger.info("Subscription set for user %s until %s", user_id, expiry)


async def revoke_subscription(user_id: int) -> None:
    async with get_db() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(subscription_expiry=None)
        )
    logger.info("Subscription revoked for user %s", user_id)


async def count_users() -> int:
    from sqlalchemy import func as sqla_func
    async with get_db() as session:
        result = await session.execute(
            select(sqla_func.count()).select_from(User)
        )
        return result.scalar_one()


# ── Alarm CRUD ────────────────────────────────────────────────────────────────


async def create_alarm(
    user_id: int,
    trigger_time: datetime,
    message_text: str,
) -> Alarm:
    async with get_db() as session:
        alarm = Alarm(
            user_id=user_id,
            trigger_time=trigger_time,
            message_text=message_text,
            is_active=True,
        )
        session.add(alarm)
        await session.flush()
        await session.refresh(alarm)
        logger.info(
            "Alarm %s created for user %s at %s", alarm.id, user_id, trigger_time
        )
        return alarm


async def get_active_alarms_for_user(user_id: int) -> Sequence[Alarm]:
    async with get_db() as session:
        result = await session.execute(
            select(Alarm)
            .where(Alarm.user_id == user_id, Alarm.is_active == True)  # noqa: E712
            .order_by(Alarm.trigger_time)
        )
        return result.scalars().all()


async def get_all_pending_alarms() -> Sequence[Alarm]:
    """Used on startup to re-inject jobs into JobQueue."""
    now = datetime.now(tz=timezone.utc)
    async with get_db() as session:
        result = await session.execute(
            select(Alarm).where(
                Alarm.is_active == True,  # noqa: E712
                Alarm.trigger_time > now,
            )
        )
        return result.scalars().all()


async def deactivate_alarm(alarm_id: int) -> None:
    async with get_db() as session:
        await session.execute(
            update(Alarm).where(Alarm.id == alarm_id).values(is_active=False)
        )


async def delete_alarm(alarm_id: int, user_id: int) -> bool:
    """Soft-delete by deactivating. Returns True if found and deactivated."""
    async with get_db() as session:
        result = await session.execute(
            select(Alarm).where(Alarm.id == alarm_id, Alarm.user_id == user_id)
        )
        alarm = result.scalar_one_or_none()
        if alarm is None:
            return False
        alarm.is_active = False
        return True


async def count_active_alarms() -> int:
    from sqlalchemy import func as sqla_func
    async with get_db() as session:
        result = await session.execute(
            select(sqla_func.count())
            .select_from(Alarm)
            .where(Alarm.is_active == True)  # noqa: E712
        )
        return result.scalar_one()
