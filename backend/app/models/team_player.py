from sqlalchemy import Column, ForeignKey, Table

from app.models.base import Base

team_player = Table(
    "team_player",
    Base.metadata,
    Column("team_id", ForeignKey("teams.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
)
