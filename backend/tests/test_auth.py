import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.user import User
from tests.conftest import create_expired_token


async def test_register_success(client: AsyncClient, valid_user_payload: dict):
    response = await client.post("/api/v1/auth/register", json=valid_user_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert "hashed_password" not in response.json()


@pytest.mark.parametrize(
    "payload,expected_status",
    [
        pytest.param(
            {"email": "john4@doe.com", "username": "johndoe4", "password": "pass"},
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="short password",
        ),
        pytest.param(
            {"email": "john.doe.com", "username": "johndoe5", "password": "password"},
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="invalid email format",
        ),
    ],
)
async def test_register_validation_errors(client: AsyncClient, payload: dict, expected_status: int):
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "payload,expected_status",
    [
        pytest.param(
            {"email": "john@doe.com", "username": "johndoe2", "password": "password"},
            status.HTTP_409_CONFLICT,
            id="duplicate email",
        ),
        pytest.param(
            {"email": "john3@doe.com", "username": "johndoe1", "password": "password"},
            status.HTTP_409_CONFLICT,
            id="duplicate username",
        ),
    ],
)
async def test_register_duplicate_conflicts(
    client: AsyncClient, registered_user: dict, payload: dict, expected_status: int
):
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == expected_status


async def test_login_success(client: AsyncClient, registered_user: dict, valid_user_payload: dict):
    response = await client.post("/api/v1/auth/login", json=valid_user_payload)
    assert response.status_code == status.HTTP_200_OK
    assert decode_access_token(response.json()["access_token"])["sub"] == registered_user["id"]
    assert response.json()["token_type"] == "bearer"


@pytest.mark.parametrize(
    "payload,expected_status",
    [
        pytest.param(
            {"email": "john1@doe.com", "username": "johndoe1", "password": "password"},
            status.HTTP_401_UNAUTHORIZED,
            id="wrong email",
        ),
        pytest.param(
            {"email": "john@doe.com", "username": "johndoe1", "password": "wrong_password"},
            status.HTTP_401_UNAUTHORIZED,
            id="wrong password",
        ),
    ],
)
async def test_login_invalid_credentials(
    client: AsyncClient, registered_user: dict, payload: dict, expected_status: int
):
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "auth_header",
    [
        pytest.param(None, id="no auth header"),
        pytest.param(f"Bearer {create_expired_token()}", id="expired token"),
        pytest.param("Bearer notavalidtoken", id="malformed token"),
    ],
)
async def test_protected_unauthorized(client: AsyncClient, auth_header: str | None):
    if auth_header:
        client.headers["Authorization"] = auth_header
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_protected_valid_token(authenticated_client: AsyncClient, registered_user: dict):
    response = await authenticated_client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == registered_user["id"]
    assert response.json()["email"] == registered_user["email"]


async def test_protected_inactive_user(
    client: AsyncClient, registered_user: dict, valid_user_payload: dict, db_session: AsyncSession
):
    login_response = await client.post("/api/v1/auth/login", json=valid_user_payload)
    token = login_response.json()["access_token"]

    user = await db_session.scalar(select(User).where(User.email == registered_user["email"]))
    user.is_active = False
    await db_session.flush()

    client.headers["Authorization"] = f"Bearer {token}"
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
