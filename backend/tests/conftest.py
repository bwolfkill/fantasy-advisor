from datetime import timedelta

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app

test_engine = create_async_engine(settings.database_url, poolclass=NullPool)


def create_expired_token(subject: str = "fake-user-id") -> str:
    return create_access_token(subject, expires_delta=timedelta(seconds=-1))


@pytest.fixture()
async def db_session():
    async with test_engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session
        await conn.rollback()


@pytest.fixture()
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def valid_user_payload() -> dict:
    return {"email": "john@doe.com", "username": "johndoe1", "password": "password"}


@pytest.fixture
async def registered_user(client: AsyncClient, valid_user_payload: dict) -> dict:
    response = await client.post("/api/v1/auth/register", json=valid_user_payload)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, registered_user: dict, valid_user_payload: valid_user_payload
) -> AsyncClient:
    response = await client.post("/api/v1/auth/login", json=valid_user_payload)
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
