from app.models.enums import ValueSource
from app.services.player_values.base import PlayerValueProvider


def get_provider(source: ValueSource = ValueSource.FANTASYCALC) -> PlayerValueProvider:
    match source:
        case ValueSource.FANTASYCALC:
            pass
        case ValueSource.CUSTOM:
            pass
        case _:
            raise ValueError("Unknown value source")
