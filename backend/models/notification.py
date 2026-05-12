from modules import (
    JSON,
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
from .enums import NotificationType


class Notifications(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    userID: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    type: Mapped[NotificationType] = mapped_column(
        "type",
        Enum(NotificationType),
        nullable=False,
        quote=True,
    )
    notice: Mapped[JSON] = mapped_column(JSON, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime_utc)
    updatedAt: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime_utc, onupdate=datetime_utc
    )
    readAt: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    deletedAt: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    def __repr__(self) -> str:
        return f"""
            Notifications(
                id={self.id},
                type={self.type},
                notice={self.notice},
                createdAt={self.createdAt},
                updatedAt={self.updatedAt},
                readAt={self.readAt},
                deletedAt={self.deletedAt},
            )

        """
