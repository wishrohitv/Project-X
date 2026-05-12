from modules import (
    TIMESTAMP,
    ForeignKey,
    Mapped,
    String,
    datetime,
    mapped_column,
)
from utils import datetime_utc

from .base import Base


class Sessions(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=datetime_utc(), default=datetime_utc()
    )
