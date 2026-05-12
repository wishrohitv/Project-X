from modules import (
    TIMESTAMP,
    ForeignKey,
    Integer,
    List,
    Mapped,
    Optional,
    String,
    mapped_column,
    relationship,
)

from .base import Base


class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str] = mapped_column(String(400), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    media_url: Mapped[str] = mapped_column(nullable=True)
    media_public_id: Mapped[str] = mapped_column(String(55), nullable=True)
    file_type: Mapped[str] = mapped_column(String(8), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(5), nullable=True)
    country: Mapped[str] = mapped_column(String(40))

    def __repr__(self) -> str:
        return f"""
            Profile(
                id={self.id!r},
                media_url={self.media_url!r},
                media_public_id={self.media_public_id!r},
                file_type={self.file_type!r},
                file_extension={self.file_extension!r},
                country={self.country!r}
            )"""
