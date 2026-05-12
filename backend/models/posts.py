from modules import (
    JSONB,
    TIMESTAMP,
    Enum,
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
from .enums import AgeRating


class Posts(Base):
    """
    This post table stores post and its replies and reposted posts
    - when parentPostID is None(null) and isReply will be always false (because its original post) then it will be considered original post
    - if parentPostID is post id and isReply is false then it will be considered reposted/qouted post
    -  if parentPostID is post id and isReply is true then it will be considered replies
    """

    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    userID: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(String(500), nullable=True)
    tags: Mapped[str] = mapped_column(String(100), nullable=True)
    mediaUrl: Mapped[str] = mapped_column(nullable=True)
    mediaPublicID: Mapped[str] = mapped_column(String(55), nullable=True)
    fileType: Mapped[str] = mapped_column(String(8), nullable=True)
    fileExtension: Mapped[str] = mapped_column(String(5), nullable=True)
    visibility: Mapped[bool] = mapped_column(default=True)
    parentPostID: Mapped[int] = mapped_column(default=None, nullable=True)
    isReply: Mapped[bool] = mapped_column(default=False, nullable=False)
    ageRating: Mapped[AgeRating] = mapped_column(
        "ageRating",
        Enum(AgeRating),
        default=AgeRating.pg13,  # 'pg13' age ratings on posts by default
        quote=True,
    )
    category: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=True)
    replyingTo: Mapped[JSONB] = mapped_column(
        JSONB, nullable=True
    )  # usernames of users who is being replied to this post i.e. ['user1', 'user2']

    isTemplate: Mapped[bool] = mapped_column(default=False, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc(),
    )
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=datetime_utc(),
        default=datetime_utc(),
    )

    def __repr__(self) -> str:
        return f"""Posts(
                    'id': {self.id!r},
                    'userID': {self.userID!r},
                    'title': {self.text!r},
                    'tags': {self.tags!r},
                    'mediaUrl': {self.mediaUrl!r},
                    'mediaPublicID': {self.mediaPublicID!r},
                    'fileType': {self.fileType!r},
                    'fileExtension': {self.fileExtension!r},
                    'visibility': {self.visibility!r},
                    'ageRating': {self.ageRating!r},
                    'category': {self.category!r},
                    'replyingTo': {self.replyingTo!r},
                    'isTemplate': {self.isTemplate!r},
                    'createdAt': {self.createdAt!r},
                    'updatedAt': {self.updatedAt!r},
                )"""
