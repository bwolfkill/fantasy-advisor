from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> UserResponse:
    return current_user
