from modules import (
    TIMESTAMP,
    ForeignKey,
    Integer,
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


class Reposts(Base):
    """
    Represents a repost of a post by a user.
    """

    __tablename__ = "reposts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=datetime_utc
    )

    def __repr__(self):
        return f"Repost(id={self.id}, user_id={self.user_id}, post_id={self.post_id}, created_at={self.created_at})"
