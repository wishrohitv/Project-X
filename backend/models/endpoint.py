from modules import (
    ARRAY,
    JSONB,
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


class Endpoint(Base):
    __tablename__ = "endpoint"
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(String(80))
    methods: Mapped[JSONB] = mapped_column(JSONB)  # LIST ITEM

    def __repr__(self) -> str:
        return f"Endpoints(id={self.id!r}, endpoint={self.endpoint!r}, method={self.methods!r})"
