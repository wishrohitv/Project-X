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


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), onupdate=datetime_utc, default=datetime_utc
    )

    def __repr__(self) -> str:
        return f"""
        <Category(
            id={self.id!r},
            category={self.category},
            created_at={self.created_at!r},
            updated_at={self.updated_at!r},
        )>"""
