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
    postID: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    userID: Mapped[int] = mapped_column(ForeignKey("users.id"))
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc()
    )

    def __repr__(self) -> str:
        return f"Follower(postsID={self.postID!r}, userID={self.userID!r}), createdAt={self.createdAt!r}"
