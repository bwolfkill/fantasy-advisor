from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.sleeper import (
    get_sleeper_league_rosters,
    get_sleeper_league_users,
    get_sleeper_players,
    get_sleeper_user_leagues,
)
from app.models.enums import LeagueType, Platform, PlayerStatus, Position, ScoringFormat
from app.models.league import League
from app.models.player import Player
from app.models.team import Team
from app.models.team_player import team_player
from app.models.user import User
from app.schemas.sleeper import SleeperLeague, SleeperLeagueUser, SleeperPlayer, SleeperRoster, SleeperSyncSummary


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


async def sync_sleeper_user_leagues(db: AsyncSession, user: User, year: int) -> SleeperSyncSummary:
    leagues_synced = 0
    teams_synced = 0
    players_synced = 0

    leagues: list[SleeperLeague] = await get_sleeper_user_leagues(user.sleeper_user_id, year)

    for league in leagues:
        league_type_raw = league.settings.get("type", 0)
        if league_type_raw == 2:
            league_type = LeagueType.DYNASTY
        elif league_type_raw == 0:
            league_type = LeagueType.REDRAFT
        else:
            league_type = LeagueType.KEEPER

        rec = league.scoring_settings.get("rec", 0)
        if rec == 1.0:
            scoring_format = ScoringFormat.PPR
        elif rec == 0.5:
            scoring_format = ScoringFormat.HALF_PPR
        else:
            scoring_format = ScoringFormat.STANDARD

        league_stmt = insert(League).values(
            user_id=user.id,
            platform=Platform.SLEEPER,
            platform_league_id=league.league_id,
            name=league.name,
            season=int(league.season),
            league_type=league_type,
            scoring_format=scoring_format,
            num_teams=league.total_rosters,
            roster_positions=league.roster_positions,
        )
        league_upsert = league_stmt.on_conflict_do_update(
            constraint="uq_platform_league_id",
            set_={
                "name": league_stmt.excluded.name,
                "season": league_stmt.excluded.season,
                "league_type": league_stmt.excluded.league_type,
                "scoring_format": league_stmt.excluded.scoring_format,
                "num_teams": league_stmt.excluded.num_teams,
                "roster_positions": league_stmt.excluded.roster_positions,
            },
        ).returning(League.id)

        result = await db.execute(league_upsert)
        league_db_id = result.scalar_one()
        leagues_synced += 1

        rosters: list[SleeperRoster] = await get_sleeper_league_rosters(league.league_id)
        league_users: list[SleeperLeagueUser] = await get_sleeper_league_users(league.league_id)

        team_name_by_user: dict[str, str] = {lu.user_id: (lu.team_name or lu.display_name) for lu in league_users}

        for roster in rosters:
            team_name = team_name_by_user.get(roster.owner_id, "")

            existing_team = (
                await db.execute(
                    select(Team).where(
                        Team.league_id == league_db_id,
                        Team.platform_roster_id == str(roster.roster_id),
                    )
                )
            ).scalar_one_or_none()

            if existing_team:
                existing_team.name = team_name
                existing_team.is_user_team = roster.owner_id == user.sleeper_user_id
                team = existing_team
            else:
                team = Team(
                    league_id=league_db_id,
                    user_id=user.id,
                    name=team_name,
                    platform_roster_id=str(roster.roster_id),
                    is_user_team=roster.owner_id == user.sleeper_user_id,
                )
                db.add(team)
                await db.flush()

            teams_synced += 1

            if roster.players:
                await db.execute(delete(team_player).where(team_player.c.team_id == team.id))

                for sleeper_player_id in roster.players:
                    player = (
                        await db.execute(select(Player).where(Player.sleeper_id == sleeper_player_id))
                    ).scalar_one_or_none()

                    if not player:
                        player = Player(
                            sleeper_id=sleeper_player_id,
                            full_name=f"Unknown ({sleeper_player_id})",
                            position=Position.QB,
                            status=PlayerStatus.ACTIVE,
                        )
                        db.add(player)
                        await db.flush()

                    await db.execute(insert(team_player).values(team_id=team.id, player_id=player.id))
                    players_synced += 1

    await db.commit()
    return SleeperSyncSummary(leagues_synced=leagues_synced, teams_synced=teams_synced, players_synced=players_synced)
