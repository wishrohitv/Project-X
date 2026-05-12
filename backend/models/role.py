from modules import (
    TIMESTAMP,
    ForeignKey,
    List,
    Mapped,
    Optional,
    String,
    mapped_column,
    relationship,
)

from .base import Base


# model for role
class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(15))

    def __repr__(self) -> str:
        return f"Role(id={self.id!r}, role={self.role!r})"
