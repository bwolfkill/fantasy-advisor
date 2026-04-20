import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.team_player import team_player


class Team(Base):
    __tablename__ = "teams"

    league_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leagues.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    platform_roster_id: Mapped[str | None] = mapped_column(String)
    is_user_team: Mapped[bool] = mapped_column(Boolean, default=False)

    league: Mapped["League"] = relationship(back_populates="teams")  # type: ignore[name-defined]  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="teams")  # type: ignore[name-defined]  # noqa: F821
    players: Mapped[list["Player"]] = relationship(secondary=team_player, back_populates="teams")  # type: ignore[name-defined]  # noqa: F821
