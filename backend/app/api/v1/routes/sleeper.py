from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.clients.sleeper import get_sleeper_user_by_username
from app.core.exceptions import SleeperAPIError, SleeperUserNotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.sleeper import SleeperLinkAccountRequest, SleeperSyncSummary, SleeperUser
from app.services.sleeper_service import set_sleeper_user_id, sync_sleeper_user_leagues

router = APIRouter(prefix="/sleeper", tags=["sleeper"])


@router.post("/link", status_code=status.HTTP_200_OK, response_model=SleeperUser)
async def link_sleeper_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    body: SleeperLinkAccountRequest,
) -> SleeperUser:
    try:
        sleeper_user: SleeperUser = await get_sleeper_user_by_username(body.sleeper_username)
    except SleeperUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sleeper account not found") from None
    except SleeperAPIError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Sleeper API Error") from None

    existing: User = await db.scalar(select(User).where(User.sleeper_user_id == sleeper_user.user_id))
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sleeper account is linked to another user")

    if current_user.sleeper_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a Sleeper account linked")

    await set_sleeper_user_id(db, current_user, sleeper_user.user_id)

    return sleeper_user


@router.delete(path="/link", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_sleeper_account(
    db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]
):
    await set_sleeper_user_id(db, current_user, None)


@router.post(path="/sync", status_code=status.HTTP_200_OK, response_model=SleeperSyncSummary)
async def sync_user_leagues(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    season: Annotated[int | None, Query(ge=2000, le=datetime.now().year)] = datetime.now().year,
) -> SleeperSyncSummary:
    if not current_user.sleeper_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Sleeper account linked")
    return await sync_sleeper_user_leagues(db, current_user, season)
