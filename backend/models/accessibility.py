from modules import (
    ARRAY,
    BOOLEAN,
    INTEGER,
    JSON,
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


class Accessibility(Base):
    __tablename__ = "accessibility"
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[str] = mapped_column(ForeignKey("endpoint.id"))
    roles: Mapped[JSONB] = mapped_column(JSONB, default=[])  # LIST ITEM
    partial_access: Mapped[BOOLEAN] = mapped_column(BOOLEAN, default=False)

    def __repr__(self) -> str:
        return f"""
            <Accessibility(id={self.id!r},
            endpoint_id={self.endpoint_id!r},
            roles={self.roles!r},
            partial_access={self.partial_access!r})>"""
