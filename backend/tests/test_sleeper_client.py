import httpx
import pytest
import respx

from app.clients import sleeper
from app.core.config import settings
from app.core.exceptions import SleeperAPIError, SleeperUserNotFoundError

base_url = settings.sleeper_api_base_url


async def test_get_sleeper_user_by_id(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/user/12345678").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_user.json"))
        )
        user = await sleeper.get_sleeper_user("12345678")
        assert user.username == "sleeperuser"


async def test_get_sleeper_user_by_username(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_user.json"))
        )
        user = await sleeper.get_sleeper_user_by_username("sleeperuser")
        assert user.user_id == "12345678"


async def test_get_sleeper_user_not_found():
    with respx.mock:
        respx.get(f"{base_url}/user/invaliduser").mock(return_value=httpx.Response(404))
        with pytest.raises(SleeperUserNotFoundError):
            await sleeper.get_sleeper_user_by_username("invaliduser")


async def test_get_sleeper_user_leagues(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser/leagues/nfl/2018").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_leagues.json"))
        )
        leagues = await sleeper.get_sleeper_user_leagues("sleeperuser", 2018)
        assert len(leagues) == 2
        assert leagues[0].name == "Sleeperbot Friends League"


async def test_get_sleeper_user_leagues_user_not_found():
    with respx.mock:
        respx.get(f"{base_url}/user/invaliduser/leagues/nfl/2018").mock(return_value=httpx.Response(200, json=[]))
        leagues = await sleeper.get_sleeper_user_leagues("invaliduser", 2018)
        assert len(leagues) == 0


async def test_get_sleeper_league(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/league/league_id").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_league.json"))
        )
        league = await sleeper.get_sleeper_league("league_id")
        assert league.name == "Sleeperbot Friends League"


async def test_get_sleeper_league_rosters(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/league/league_id/rosters").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_rosters.json"))
        )
        rosters = await sleeper.get_sleeper_league_rosters("league_id")
        assert rosters[0].roster_id == 1


async def test_get_sleeper_league_users(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/league/league_id/users").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_league_users.json"))
        )
        users = await sleeper.get_sleeper_league_users("league_id")
        assert users[0].user_id == "sleeper_user"
        assert users[0].team_name == "Dezpacito"


async def test_get_sleeper_players(load_test_data):
    with respx.mock:
        respx.get(f"{base_url}/players/nfl").mock(
            return_value=httpx.Response(200, json=load_test_data("sleeper_players.json"))
        )
        for _ in range(2):
            players = await sleeper.get_sleeper_players()

        assert respx.calls.call_count == 1
        assert players["3086"].first_name == "Tom"


async def test_sleeper_client_retry():
    with respx.mock:
        respx.get(f"{base_url}/user/12345678").mock(return_value=httpx.Response(500))

        with pytest.raises(SleeperAPIError):
            await sleeper.get_sleeper_user("12345678")

        assert respx.calls.call_count == 3
