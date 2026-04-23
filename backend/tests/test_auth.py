import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.security import decode_access_token


@pytest.fixture
def valid_user_payload() -> dict:
    return {"email": "john@doe.com", "username": "johndoe1", "password": "password"}


@pytest.fixture
async def registered_user(client: AsyncClient, valid_user_payload: dict) -> dict:
    response = await client.post("/api/v1/auth/register", json=valid_user_payload)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


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
