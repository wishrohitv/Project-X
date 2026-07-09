from modules import (
    TIMESTAMP,
    Enum,
    ForeignKey,
    LargeBinary,
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
from .enums import AccountStatus, Provider
from .profile import Profile


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=True)
    username: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(40))
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    provider: Mapped[Provider] = mapped_column(Enum(Provider), default=Provider.local)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime_utc
    )
    role: Mapped[int] = mapped_column(ForeignKey("role.id"), default=3)
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.active
    )
    is_verified: Mapped[bool] = mapped_column(default=False)
    profile: Mapped[Profile] = relationship(
        backref="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"""<Users(
                id={self.id!r},
                name={self.name!r},
                username={self.username!r}
                email={self.email!r},
                created_at={self.created_at!r},
                role={self.role!r},
                password{self.password!r},
                account_status={self.account_status!r},
                is_verified={self.is_verified!r}
            )>"""
