import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import LeagueType, ScoringFormat, ValueSource


class PlayerValue(Base):
    __tablename__ = "player_values"

    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"), index=True)
    source: Mapped[ValueSource] = mapped_column(String)
    league_type: Mapped[LeagueType] = mapped_column(String)
    scoring_format: Mapped[ScoringFormat] = mapped_column(String)
    value: Mapped[int] = mapped_column(Integer)
    rank: Mapped[int | None] = mapped_column(Integer)
    positional_rank: Mapped[int | None] = mapped_column(Integer)
    trend_30day: Mapped[int | None] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)

    player: Mapped["Player"] = relationship(back_populates="values")  # type: ignore[name-defined]  # noqa: F821

    __table_args__ = (
        Index(
            "idx_player_value_lookup",
            "player_id",
            "source",
            "league_type",
            "scoring_format",
            "date",
            unique=True,
        ),
    )
