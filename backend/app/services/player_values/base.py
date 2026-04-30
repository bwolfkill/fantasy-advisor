from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.models.enums import LeagueType, Position, ScoringFormat, ValueSource


class PlayerValueData(BaseModel):
    """Normalized player value data from any source."""

    source: ValueSource
    external_id: str | None = Field(default=None)
    player_name: str
    position: Position
    nfl_team: str | None = Field(default=None)
    value: int
    overall_rank: int | None = Field(default=None)
    positional_rank: int | None = Field(default=None)
    trend_30day: int | None = Field(default=None)
    league_type: LeagueType
    scoring_format: ScoringFormat


class PlayerValueProvider(ABC):
    """Abstract base class for player value data sources."""

    @abstractmethod
    async def fetch_values(
        self,
        league_type: LeagueType,
        scoring_format: ScoringFormat,
    ) -> list[PlayerValueData]:
        """
        Fetch current player values for the givin format.
        Implementors should handle their own HTTP calls, parsing, and error handling.
        """
        pass

    @property
    @abstractmethod
    def source(self) -> ValueSource:
        """The ValueSource enum value for this provider."""
        pass
