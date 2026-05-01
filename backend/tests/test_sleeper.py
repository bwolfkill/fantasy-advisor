import httpx
import respx
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from tests.conftest import load_test_data

base_url = settings.sleeper_api_base_url


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


async def test_link_sleeper_account_when_already_linked(
    db_session: AsyncSession, authenticated_client: AsyncClient, valid_user_payload: dict
):
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
