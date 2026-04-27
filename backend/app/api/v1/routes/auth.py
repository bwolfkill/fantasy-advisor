from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
    EmailNotFoundError,
    PasswordDoesNotMatchError,
    UsernameAlreadyExistsError,
)
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import authenticate_user
from app.services.user_service import create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(db: Annotated[AsyncSession, Depends(get_db)], user_request: UserCreate) -> UserResponse:
    try:
        user: UserResponse = await create_user(db, user_request)
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists with that email"
        ) from None
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists with that username"
        ) from None

    return user


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def login(db: Annotated[AsyncSession, Depends(get_db)], login_request: LoginRequest) -> TokenResponse:
    try:
        token: TokenResponse = await authenticate_user(db, login_request)
    except EmailNotFoundError, PasswordDoesNotMatchError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login credentials") from None

    return token
