from modules import (
    TIMESTAMP,
    ForeignKey,
    List,
    Mapped,
    Optional,
    String,
    datetime,
    mapped_column,
    relationship,
)
from utils import datetime_utc

from .base import Base


class Follower(Base):
    __tablename__ = "follower"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(
        "timestamp", TIMESTAMP(timezone=True), default=datetime_utc
    )

    def __repr__(self) -> str:
        return f"""
        Follower(
            user_id={self.user_id!r},
            follower_id={self.follower_id!r},
            created_at={self.created_at!r}
        )"""
