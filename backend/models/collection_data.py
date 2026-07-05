"""
User created collection post
"""

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


class CollectionData(Base):
    __tablename__ = "collection_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=datetime_utc, default=datetime_utc
    )

    def __repr__(self):
        return f"""CollectionData(
                id={self.id!r},
                collectionId={self.collection_id!r},
                post_id={self.post_id!r},
                created_at={self.created_at!r},
                updated_at={self.updated_at!r}
            )"""
