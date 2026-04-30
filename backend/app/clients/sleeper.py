import time

from fastapi import status
from httpx import AsyncClient, Response
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import SleeperAPIError, SleeperUserNotFoundError
from app.schemas.sleeper import SleeperLeague, SleeperLeagueUser, SleeperPlayer, SleeperRoster, SleeperUser

client = AsyncClient(timeout=10.0)
base_url = settings.sleeper_api_base_url
sleeper_retry = retry(
    wait=wait_exponential(multiplier=1, min=1, max=4),
    stop=stop_after_attempt(3),
    retry=retry_if_exception(lambda e: isinstance(e, SleeperAPIError) and e.status_code >= 500),
    reraise=True,
)

_players_cache: dict = {}
_players_cache_time: float = 0.0
_PLAYERS_CACHE_TTL: float = 60 * 60 * 24


@sleeper_retry
async def get_sleeper_user(user_id: str) -> SleeperUser:
    response: Response = await client.get(base_url + f"/user/{user_id}")

    if response.status_code != status.HTTP_200_OK:
        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise SleeperUserNotFoundError(user_id=user_id)

        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    user: SleeperUser = SleeperUser.model_validate(response.json())

    return user


@sleeper_retry
async def get_sleeper_user_by_username(username: str) -> SleeperUser:
    response: Response = await client.get(base_url + f"/user/{username}")

    if response.status_code != status.HTTP_200_OK:
        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise SleeperUserNotFoundError(username=username)

        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    user: SleeperUser = SleeperUser.model_validate(response.json())

    return user


@sleeper_retry
async def get_sleeper_user_leagues(user_id: str, season: int) -> list[SleeperLeague]:
    response: Response = await client.get(base_url + f"/user/{user_id}/leagues/nfl/{season}")

    if response.status_code != status.HTTP_200_OK:
        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    leagues: list[SleeperLeague] = [SleeperLeague.model_validate(league) for league in response.json()]

    return leagues


@sleeper_retry
async def get_sleeper_league(league_id: str) -> SleeperLeague:
    response: Response = await client.get(base_url + f"/league/{league_id}")

    if response.status_code != status.HTTP_200_OK:
        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    league: SleeperLeague = SleeperLeague.model_validate(response.json())

    return league


@sleeper_retry
async def get_sleeper_league_rosters(league_id: str) -> list[SleeperRoster]:
    response: Response = await client.get(base_url + f"/league/{league_id}/rosters")

    if response.status_code != status.HTTP_200_OK:
        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    rosters: list[SleeperRoster] = [SleeperRoster.model_validate(roster) for roster in response.json()]

    return rosters


@sleeper_retry
async def get_sleeper_league_users(league_id: str) -> list[SleeperLeagueUser]:
    response: Response = await client.get(base_url + f"/league/{league_id}/users")

    if response.status_code != status.HTTP_200_OK:
        raise SleeperAPIError(status_code=response.status_code, message=response.text)

    users: list[SleeperLeagueUser] = []
    for user in response.json():
        u = SleeperLeagueUser.model_validate(user)
        u.team_name = user.get("metadata", {}).get("team_name", None)
        users.append(u)

    return users


@sleeper_retry
async def get_sleeper_players() -> dict[str, SleeperPlayer]:
    """
    Returns all Sleeper player data.

    USE SPARINGLY! THE AVERAGE RETURN SIZE FOR THIS CALL IS ~5MB.

    Checks the in-memory cache `_players_cache` before making a client call.

    `_players_cache` has a default TTL of 24 hours.

    Returns:
    dict[str, SleeperPlayer]
    """
    global _players_cache
    global _players_cache_time
    now = time.time()
    if (now - _players_cache_time) < _PLAYERS_CACHE_TTL:
        data = _players_cache
    else:
        response: Response = await client.get(base_url + "/players/nfl")

        if response.status_code != status.HTTP_200_OK:
            raise SleeperAPIError(status_code=response.status_code, message=response.text)

        data = response.json()
        _players_cache = data
        _players_cache_time = now

    players: dict[str, SleeperPlayer] = {
        player_id: SleeperPlayer.model_validate(player_data) for player_id, player_data in data.items()
    }

    return players
