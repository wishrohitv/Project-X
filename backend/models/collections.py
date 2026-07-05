"""
Alchemy model for collection, User create their own collection
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


class Collections(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    owner: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=datetime_utc, default=datetime_utc
    )

    def __repr__(self):
        return f"""Collections(
                id={self.id!r},
                name={self.name!r},
                description={self.description!r},
                owner={self.owner!r},
                created_at={self.created_at!r},
                updated_at={self.updated_at!r}
            )"""
