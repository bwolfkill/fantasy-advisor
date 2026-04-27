from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def test_create_user(db_session: AsyncSession):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )
    db_session.add(user)
    await db_session.flush()

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    fetched = result.scalar_one()

    assert fetched.id == user.id
    assert fetched.email == "test@example.com"
    assert fetched.username == "testuser"
    assert fetched.is_active is True


async def test_get_me_authenticated(authenticated_client: AsyncClient, registered_user: dict):
    response = await authenticated_client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == registered_user["id"]


async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
