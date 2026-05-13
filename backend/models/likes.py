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


class Likes(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc()
    )

    def __repr__(self) -> str:
        return f"Follower(post_id={self.post_id!r}, user_id={self.user_id!r}), createdAt={self.created_at!r}"
