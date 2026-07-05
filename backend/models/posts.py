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
    - when parent_post_id is None(null) and is_reply will be always false (because its original post) then it will be considered original post
    - if parent_post_id is post id and is_reply is false then it will be considered reposted/qouted post
    -  if parent_post_id is post id and is_reply is true then it will be considered replies
    """

    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(String(500), nullable=True)
    tags: Mapped[str] = mapped_column(String(100), nullable=True)
    media_url: Mapped[str] = mapped_column(nullable=True)
    media_public_id: Mapped[str] = mapped_column(String(55), nullable=True)
    file_type: Mapped[str] = mapped_column(String(8), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(5), nullable=True)
    visibility: Mapped[bool] = mapped_column(default=True)
    parent_post_id: Mapped[Optional[int]] = mapped_column(default=None, nullable=True)
    is_reply: Mapped[bool] = mapped_column(default=False, nullable=False)
    age_rating: Mapped[AgeRating] = mapped_column(
        "age_rating",
        Enum(AgeRating),
        default=AgeRating.pg13,  # 'pg13' age ratings on posts by default
        quote=True,
    )
    category: Mapped[Optional[int]] = mapped_column(
        ForeignKey("category.id"), nullable=True
    )
    replying_to: Mapped[Optional[JSONB]] = mapped_column(
        JSONB, nullable=True
    )  # usernames of users who is being replied to this post i.e. ['user1', 'user2']

    is_template: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime_utc,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=datetime_utc,
        default=datetime_utc,
    )

    def __repr__(self) -> str:
        return f"""Post(
                    'id': {self.id!r},
                    'user_id': {self.user_id!r},
                    'title': {self.text!r},
                    'tags': {self.tags!r},
                    'media_url': {self.media_url!r},
                    'media_public_id': {self.media_public_id!r},
                    'file_type': {self.file_type!r},
                    'file_extension': {self.file_extension!r},
                    'visibility': {self.visibility!r},
                    'age_rating': {self.age_rating!r},
                    'category': {self.category!r},
                    'replying_to': {self.replying_to!r},
                    'is_template': {self.is_template!r},
                    'created_at': {self.created_at!r},
                    'updated_at': {self.updated_at!r},
                )"""
