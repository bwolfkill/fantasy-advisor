from pydantic import BaseModel, ConfigDict, Field


class SleeperBase(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )


class SleeperUser(SleeperBase):
    user_id: str
    username: str
    display_name: str
    avatar: str | None = Field(default=None)
    team_name: str | None = Field(default=None)


class SleeperLeague(SleeperBase):
    league_id: str
    name: str
    season: str
    status: str
    sport: str
    settings: dict
    scoring_settings: dict
    roster_positions: list[str]
    total_rosters: int


class SleeperLeagueUser(SleeperBase):
    user_id: str
    display_name: str
    team_name: str | None = None


class SleeperRoster(SleeperBase):
    roster_id: int
    owner_id: str | None = Field(default=None)
    players: list[str] | None = Field(default=None)
    league_id: str


class SleeperPlayer(SleeperBase):
    player_id: str
    full_name: str | None = Field(default=None, alias="search_full_name")
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    position: str | None = Field(default=None)
    team: str | None = Field(default=None)
    age: int | None = Field(default=None)
    years_exp: int | None = Field(default=None)
    status: str | None = Field(default=None)
    active: bool | None = Field(default=None)
