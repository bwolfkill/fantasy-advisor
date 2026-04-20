from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PlayerStatus, Position
from app.models.team_player import team_player


class Player(Base):
    __tablename__ = "players"

    sleeper_id: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    fantasycalc_id: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    position: Mapped[Position] = mapped_column(String)
    nfl_team: Mapped[str | None] = mapped_column(String)
    age: Mapped[float | None] = mapped_column(Float)
    years_exp: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[PlayerStatus] = mapped_column(String, default=PlayerStatus.ACTIVE)

    values: Mapped[list["PlayerValue"]] = relationship(back_populates="player")  # type: ignore[name-defined]  # noqa: F821
    teams: Mapped[list["Team"]] = relationship(secondary=team_player, back_populates="players")  # type: ignore[name-defined]  # noqa: F821
