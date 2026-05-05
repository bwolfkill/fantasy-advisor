import httpx
import pytest
import respx
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.league import League
from app.models.team import Team
from app.models.team_player import team_player
from app.models.user import User
from tests.conftest import load_test_data

base_url = settings.sleeper_api_base_url

SLEEPER_USER_ID = "188815879448829952"
TEST_SEASON = 2024


# --- Helpers ---


def _mock_sync(league: dict, rosters: list, league_users: list):
    league_id = league["league_id"]
    respx.get(f"{base_url}/user/{SLEEPER_USER_ID}/leagues/nfl/{TEST_SEASON}").mock(
        return_value=httpx.Response(status.HTTP_200_OK, json=[league])
    )
    respx.get(f"{base_url}/league/{league_id}/rosters").mock(
        return_value=httpx.Response(status.HTTP_200_OK, json=rosters)
    )
    respx.get(f"{base_url}/league/{league_id}/users").mock(
        return_value=httpx.Response(status.HTTP_200_OK, json=league_users)
    )


@pytest.fixture
async def linked_client(db_session: AsyncSession, authenticated_client: AsyncClient) -> AsyncClient:
    response = await authenticated_client.get("/api/v1/users/me")
    user = await db_session.scalar(select(User).where(User.id == response.json()["id"]))
    user.sleeper_user_id = SLEEPER_USER_ID
    await db_session.flush()
    return authenticated_client


# --- Link / Unlink tests ---


async def test_link_sleeper_account_success(authenticated_client: AsyncClient):
    sleeper_user = load_test_data("sleeper_user.json")
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser").mock(
            return_value=httpx.Response(status.HTTP_200_OK, json=sleeper_user)
        )

        response = await authenticated_client.post(
            "/api/v1/sleeper/link", json={"sleeper_username": sleeper_user["username"]}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] == sleeper_user["user_id"]

        response = await authenticated_client.get("/api/v1/users/me")
        assert response.json()["sleeper_user_id"] == sleeper_user["user_id"]


async def test_link_sleeper_account_invalid_username(authenticated_client: AsyncClient):
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser").mock(return_value=httpx.Response(status.HTTP_404_NOT_FOUND))

        response = await authenticated_client.post("/api/v1/sleeper/link", json={"sleeper_username": "sleeperuser"})
        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_link_sleeper_account_linked_to_other_account(
    db_session: AsyncSession, authenticated_client: AsyncClient
):
    sleeper_user = load_test_data("sleeper_user.json")
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser").mock(
            return_value=httpx.Response(status.HTTP_200_OK, json=sleeper_user)
        )
        user_sleeper_account_linked_to = User(**load_test_data("db_user.json"))
        user_sleeper_account_linked_to.sleeper_user_id = sleeper_user["user_id"]
        db_session.add(user_sleeper_account_linked_to)
        await db_session.flush()

        response = await authenticated_client.post(
            "/api/v1/sleeper/link", json={"sleeper_username": sleeper_user["username"]}
        )
        assert response.status_code == status.HTTP_409_CONFLICT


async def test_link_sleeper_account_when_already_linked(db_session: AsyncSession, authenticated_client: AsyncClient):
    sleeper_user = load_test_data("sleeper_user.json")
    with respx.mock:
        respx.get(f"{base_url}/user/sleeperuser").mock(
            return_value=httpx.Response(status.HTTP_200_OK, json=sleeper_user)
        )

        response = await authenticated_client.get("/api/v1/users/me")
        user: User = await db_session.scalar(select(User).where(User.id == response.json()["id"]))
        user.sleeper_user_id = "alreadyhaveasleeperid"
        await db_session.flush()

        response = await authenticated_client.post(
            "/api/v1/sleeper/link", json={"sleeper_username": sleeper_user["username"]}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_unlink_sleeper_account(db_session: AsyncSession, authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/users/me")
    user: User = await db_session.scalar(select(User).where(User.id == response.json()["id"]))
    user.sleeper_user_id = "sleeper_user_id"
    await db_session.flush()

    response = await authenticated_client.delete("/api/v1/sleeper/link")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await authenticated_client.delete("/api/v1/sleeper/link")
    assert response.status_code == status.HTTP_204_NO_CONTENT


# --- Sync tests ---


async def test_sync_no_sleeper_link(authenticated_client: AsyncClient):
    response = await authenticated_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_sync_returns_correct_counts(linked_client: AsyncClient):
    league = load_test_data("sleeper_league_dynasty_ppr.json")
    rosters = load_test_data("sleeper_rosters_multi.json")
    league_users = load_test_data("sleeper_league_users_multi.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        response = await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["leagues_synced"] == 1
    assert data["teams_synced"] == 2
    assert data["players_synced"] == 3


async def test_sync_creates_db_records(db_session: AsyncSession, linked_client: AsyncClient):
    league = load_test_data("sleeper_league_dynasty_ppr.json")
    rosters = load_test_data("sleeper_rosters.json")
    league_users = load_test_data("sleeper_league_users_sync.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    db_league = await db_session.scalar(select(League).where(League.platform_league_id == league["league_id"]))
    assert db_league is not None

    teams = (await db_session.scalars(select(Team).where(Team.league_id == db_league.id))).all()
    assert len(teams) == 1

    tp_rows = (await db_session.execute(select(team_player).where(team_player.c.team_id == teams[0].id))).fetchall()
    assert len(tp_rows) == len(rosters[0]["players"])


async def test_sync_idempotent(db_session: AsyncSession, linked_client: AsyncClient):
    league = load_test_data("sleeper_league_dynasty_ppr.json")
    rosters = load_test_data("sleeper_rosters.json")
    league_users = load_test_data("sleeper_league_users_sync.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    leagues = (await db_session.scalars(select(League).where(League.platform_league_id == league["league_id"]))).all()
    assert len(leagues) == 1

    teams = (await db_session.scalars(select(Team).where(Team.league_id == leagues[0].id))).all()
    assert len(teams) == 1

    tp_rows = (await db_session.execute(select(team_player).where(team_player.c.team_id == teams[0].id))).fetchall()
    assert len(tp_rows) == len(rosters[0]["players"])


async def test_sync_dynasty_ppr_mapping(db_session: AsyncSession, linked_client: AsyncClient):
    league = load_test_data("sleeper_league_dynasty_ppr.json")
    rosters = load_test_data("sleeper_rosters.json")
    league_users = load_test_data("sleeper_league_users_sync.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    db_league = await db_session.scalar(select(League).where(League.platform_league_id == league["league_id"]))
    assert db_league.league_type == "dynasty"
    assert db_league.scoring_format == "ppr"


async def test_sync_redraft_standard_mapping(db_session: AsyncSession, linked_client: AsyncClient):
    league = load_test_data("sleeper_league_redraft_standard.json")
    rosters = load_test_data("sleeper_rosters.json")
    league_users = load_test_data("sleeper_league_users_sync.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    db_league = await db_session.scalar(select(League).where(League.platform_league_id == league["league_id"]))
    assert db_league.league_type == "redraft"
    assert db_league.scoring_format == "standard"


async def test_sync_user_team_identified(db_session: AsyncSession, linked_client: AsyncClient):
    league = load_test_data("sleeper_league_dynasty_ppr.json")
    rosters = load_test_data("sleeper_rosters_multi.json")
    league_users = load_test_data("sleeper_league_users_multi.json")

    with respx.mock:
        _mock_sync(league, rosters, league_users)
        await linked_client.post(f"/api/v1/sleeper/sync?season={TEST_SEASON}")

    db_league = await db_session.scalar(select(League).where(League.platform_league_id == league["league_id"]))
    teams = (await db_session.scalars(select(Team).where(Team.league_id == db_league.id))).all()

    user_teams = [t for t in teams if t.is_user_team]
    other_teams = [t for t in teams if not t.is_user_team]

    assert len(user_teams) == 1
    assert user_teams[0].platform_roster_id == "1"
    assert len(other_teams) == 1
    assert other_teams[0].platform_roster_id == "2"
