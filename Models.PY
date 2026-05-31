"""
models.py — SQLAlchemy ORM models (async-compatible).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


class User(Base):
    """Represents a Telegram user registered with the bot."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="Telegram user_id"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str] = mapped_column(
        String(8), nullable=False, default="en", server_default="en"
    )
    subscription_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now,
    )

    alarms: Mapped[list["Alarm"]] = relationship(
        "Alarm", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def has_active_subscription(self) -> bool:
        if self.subscription_expiry is None:
            return False
        return self.subscription_expiry > datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} lang={self.language_code} "
            f"sub_expiry={self.subscription_expiry}>"
        )


class Alarm(Base):
    """A single reminder entry belonging to a user."""

    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now,
    )

    user: Mapped["User"] = relationship("User", back_populates="alarms")

    def __repr__(self) -> str:
        return (
            f"<Alarm id={self.id} user_id={self.user_id} "
            f"trigger={self.trigger_time} active={self.is_active}>"
        )
