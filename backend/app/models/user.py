from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    sleeper_user_id: Mapped[str | None] = mapped_column(String, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    leagues: Mapped[list["League"]] = relationship(back_populates="user")  # type: ignore[name-defined]  # noqa: F821
    teams: Mapped[list["Team"]] = relationship(back_populates="user")  # type: ignore[name-defined]  # noqa: F821
