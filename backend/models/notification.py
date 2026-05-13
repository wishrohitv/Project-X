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
    user_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id"), nullable=True
    )
    type: Mapped[NotificationType] = mapped_column(
        "type",
        Enum(NotificationType),
        nullable=False,
        quote=True,
    )
    notice: Mapped[JSON] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", TIMESTAMP, default=datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", TIMESTAMP, default=datetime_utc, onupdate=datetime_utc
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        "read_at", TIMESTAMP, nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        "deleted_at", TIMESTAMP, nullable=True
    )

    def __repr__(self) -> str:
        return f"""
            Notifications(
                id={self.id},
                type={self.type},
                notice={self.notice},
                created_at={self.created_at},
                updated_at={self.updated_at},
                read_at={self.read_at},
                deleted_at={self.deleted_at},
            )

        """
