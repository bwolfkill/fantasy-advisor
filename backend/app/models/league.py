import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LeagueType, Platform, ScoringFormat


class League(Base):
    __tablename__ = "leagues"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    platform: Mapped[Platform] = mapped_column(String)
    platform_league_id: Mapped[str | None] = mapped_column(String)
    season: Mapped[int] = mapped_column(Integer)
    league_type: Mapped[LeagueType] = mapped_column(String)
    scoring_format: Mapped[ScoringFormat] = mapped_column(String)
    num_teams: Mapped[int] = mapped_column(Integer)
    roster_positions: Mapped[list] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="leagues")  # type: ignore[name-defined]  # noqa: F821
    teams: Mapped[list["Team"]] = relationship(back_populates="league")  # type: ignore[name-defined]  # noqa: F821

    __table_args__ = (UniqueConstraint("user_id", "platform", "platform_league_id", name="uq_platform_league_id"),)
