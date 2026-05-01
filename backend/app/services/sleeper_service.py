from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.sleeper import get_sleeper_players
from app.models.enums import Position
from app.models.player import Player
from app.models.user import User
from app.schemas.sleeper import SleeperPlayer


async def sync_players_from_sleeper(db: AsyncSession):
    p: dict[str, SleeperPlayer] = await get_sleeper_players()

    players_list: list[dict] = [
        {
            "sleeper_id": p_id,
            "full_name": p_values.full_name or f"{p_values.first_name} {p_values.last_name}",
            "position": p_values.position,
            "nfl_team": p_values.team,
            "age": p_values.age,
            "years_exp": p_values.years_exp,
            "status": p_values.status,
        }
        for p_id, p_values in p.items()
        if (p_values.full_name or (p_values.first_name and p_values.last_name)) and p_values.position in Position
    ]

    stmt = insert(Player).values(players_list)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["sleeper_id"],
        set_={
            "full_name": stmt.excluded.full_name,
            "position": stmt.excluded.position,
            "nfl_team": stmt.excluded.nfl_team,
            "age": stmt.excluded.age,
            "years_exp": stmt.excluded.years_exp,
            "status": stmt.excluded.status,
        },
    )

    await db.execute(upsert_stmt)
    await db.commit()


async def set_sleeper_user_id(db: AsyncSession, user: User, sleeper_user_id: str | None = None):
    user.sleeper_user_id = sleeper_user_id
    await db.commit()
