from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailNotFoundError, PasswordDoesNotMatchError
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse


async def authenticate_user(db: AsyncSession, login_request: LoginRequest) -> TokenResponse:
    user: User = await db.scalar(select(User).where(User.email == login_request.email))

    if not user:
        raise EmailNotFoundError

    if not verify_password(login_request.password, user.hashed_password):
        raise PasswordDoesNotMatchError

    token = TokenResponse(access_token=create_access_token(subject=str(user.id)))

    return token
