from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailAlreadyExistsError, UsernameAlreadyExistsError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


async def create_user(db: AsyncSession, user_request: UserCreate) -> User:
    if await db.scalar(select(User).where(User.email == user_request.email)):
        raise EmailAlreadyExistsError
    if await db.scalar(select(User).where(User.username == user_request.username)):
        raise UsernameAlreadyExistsError

    new_user = User(
        email=user_request.email, username=user_request.username, hashed_password=hash_password(user_request.password)
    )
    db.add(new_user)
    await db.commit()

    return new_user
