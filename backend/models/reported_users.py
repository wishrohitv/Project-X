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


class ReportedUsers(Base):
    __tablename__ = "reported_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    reported_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_resolved: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime_utc(), onupdate=datetime_utc()
    )

    def __repr__(self) -> str:
        return f"""ReportedUser(
                        id={self.id}
                        user_id={self.user_id!r},
                        reported_by={self.reported_by!r}),
                        is_resolved={self.is_resolved!r},
                        description={self.description!r},
                        created_at={self.created_at!r}
                        updated_at={self.updated_at!r}
                    """
