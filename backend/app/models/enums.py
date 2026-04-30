from enum import StrEnum


class Platform(StrEnum):
    SLEEPER = "sleeper"
    MANUAL = "manual"


class LeagueType(StrEnum):
    DYNASTY = "dynasty"
    KEEPER = "keeper"
    REDRAFT = "redraft"


class ScoringFormat(StrEnum):
    PPR = "ppr"
    HALF_PPR = "half_ppr"
    STANDARD = "standard"


class Position(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"


class PlayerStatus(StrEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ValueSource(StrEnum):
    FANTASYCALC = "fantasycalc"
    CUSTOM = "custom"
